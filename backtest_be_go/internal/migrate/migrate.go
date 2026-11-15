// Package migrate는 goose 마이그레이션 실행과 기존 DB 기준선(baseline) 표시를 담당한다.
//
// 자동 downgrade는 제공하지 않는다. 운영 DB는 CI가 아니라 사람이 백업 후 직접 올린다.
package migrate

import (
	"context"
	"database/sql"
	"fmt"
	"io/fs"

	"github.com/pressly/goose/v3"
	"github.com/pressly/goose/v3/database"
)

// VersionTable은 goose 버전 테이블 이름이다. Alembic의 alembic_version은 건드리지 않고 남겨 둔다.
const VersionTable = "goose_db_version"

type Migrator struct {
	db       *sql.DB
	store    database.Store
	provider *goose.Provider
}

func New(db *sql.DB, fsys fs.FS) (*Migrator, error) {
	store, err := database.NewStore(database.DialectMySQL, VersionTable)
	if err != nil {
		return nil, err
	}
	p, err := goose.NewProvider(goose.DialectCustom, db, fsys, goose.WithStore(store))
	if err != nil {
		return nil, err
	}
	return &Migrator{db: db, store: store, provider: p}, nil
}

// Latest는 내장된 마이그레이션 중 가장 높은 버전이다.
func (m *Migrator) Latest() int64 {
	sources := m.provider.ListSources()
	if len(sources) == 0 {
		return 0
	}
	return sources[len(sources)-1].Version
}

func (m *Migrator) Up(ctx context.Context) ([]*goose.MigrationResult, error) {
	if err := m.refuseUnbaselined(ctx); err != nil {
		return nil, err
	}
	return m.provider.Up(ctx)
}

func (m *Migrator) Status(ctx context.Context) ([]*goose.MigrationStatus, error) {
	return m.provider.Status(ctx)
}

// refuseUnbaselined는 goose 기록 없이 테이블만 있는 DB(Python 시절 DB)에 00001을 다시 실행하려는
// 실수를 막는다. 그런 DB는 baseline으로 현재 버전을 먼저 표시해야 한다.
func (m *Migrator) refuseUnbaselined(ctx context.Context) error {
	tracked, err := m.versionTableExists(ctx)
	if err != nil || tracked {
		return err
	}
	exists, err := m.tableExists(ctx, "stocks")
	if err != nil {
		return err
	}
	if exists {
		detected, derr := m.Detect(ctx)
		hint := ""
		if derr == nil {
			hint = fmt.Sprintf(" (detected schema version %d: run `backtestctl migrate baseline %d` after a backup)", detected, detected)
		}
		return fmt.Errorf("database has tables but no %s%s", VersionTable, hint)
	}
	return nil
}

// Detect는 goose 기록이 없는 기존 DB의 스키마 버전을 실제 컬럼 정의로 판별한다.
//
//	1: Alembic 1f574a9ba22e(develop) — daily_prices.close가 DECIMAL(19,4)
//	2: Alembic 6f903c2a711b(rust-migration) 또는 현재 schema.sql — DECIMAL(38,18)
func (m *Migrator) Detect(ctx context.Context) (int64, error) {
	for _, table := range []string{"stocks", "daily_prices", "stock_news"} {
		ok, err := m.tableExists(ctx, table)
		if err != nil {
			return 0, err
		}
		if !ok {
			return 0, fmt.Errorf("table %s is missing; not a recognizable schema", table)
		}
	}
	var precision, scale int
	err := m.db.QueryRowContext(ctx, `
		SELECT NUMERIC_PRECISION, NUMERIC_SCALE FROM information_schema.COLUMNS
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_prices' AND COLUMN_NAME = 'close'`,
	).Scan(&precision, &scale)
	if err != nil {
		return 0, fmt.Errorf("read daily_prices.close definition: %w", err)
	}
	switch {
	case precision == 19 && scale == 4:
		return 1, nil
	case precision == 38 && scale == 18:
		return 2, nil
	}
	return 0, fmt.Errorf("daily_prices.close is DECIMAL(%d,%d); not a known schema version", precision, scale)
}

// Baseline은 이미 스키마가 있는 DB에 version까지 적용됨으로 기록한다. SQL은 실행하지 않는다.
// 실제 스키마(Detect)가 version과 다르면 기록하지 않는다. 잘못된 기준선은 이후 마이그레이션을
// 건너뛰거나 이미 적용된 변경을 다시 실행하게 만든다.
func (m *Migrator) Baseline(ctx context.Context, version int64) error {
	if version < 1 || version > m.Latest() {
		return fmt.Errorf("baseline version must be 1..%d", m.Latest())
	}
	tracked, err := m.versionTableExists(ctx)
	if err != nil {
		return err
	}
	if tracked {
		return fmt.Errorf("%s already exists; baseline is only for databases that goose has never managed", VersionTable)
	}
	detected, err := m.Detect(ctx)
	if err != nil {
		return err
	}
	if detected != version {
		return fmt.Errorf("schema looks like version %d, not %d; refusing to baseline", detected, version)
	}

	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()
	// CREATE TABLE은 MySQL에서 암묵적으로 커밋된다. 테이블 생성 뒤 INSERT가 실패하면 빈 버전 테이블만
	// 남을 수 있으므로, 그 경우 사람이 테이블을 지우고 다시 실행해야 한다는 점을 오류로 알린다.
	if err := m.store.CreateVersionTable(ctx, tx); err != nil {
		return err
	}
	for v := int64(0); v <= version; v++ {
		if err := m.store.Insert(ctx, tx, database.InsertRequest{Version: v}); err != nil {
			return fmt.Errorf("record version %d (drop %s before retrying): %w", v, VersionTable, err)
		}
	}
	return tx.Commit()
}

func (m *Migrator) versionTableExists(ctx context.Context) (bool, error) {
	return m.tableExists(ctx, VersionTable)
}

func (m *Migrator) tableExists(ctx context.Context, name string) (bool, error) {
	var n int
	err := m.db.QueryRowContext(ctx, `
		SELECT COUNT(*) FROM information_schema.TABLES
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?`, name).Scan(&n)
	if err != nil {
		return false, err
	}
	return n > 0, nil
}
