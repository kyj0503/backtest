//go:build integration

// 실제 MySQL이 필요한 테스트다. TEST_MYSQL_ROOT_DSN(go-sql-driver 형식, DB 이름 없이
// 예: root:pw@tcp(mysql:3306)/)을 주고 `go test -tags integration ./...`로 실행한다.
// 테스트마다 임시 데이터베이스를 만들고 지운다.
package migrate

import (
	"context"
	"database/sql"
	"fmt"
	"io/fs"
	"os"
	"strings"
	"testing"
	"time"

	_ "github.com/go-sql-driver/mysql"

	"github.com/kyj0503/backtest/backtest_be_go/migrations"
)

func tempDatabase(t *testing.T) *sql.DB {
	t.Helper()
	root := os.Getenv("TEST_MYSQL_ROOT_DSN")
	if root == "" {
		t.Skip("TEST_MYSQL_ROOT_DSN not set")
	}
	admin, err := sql.Open("mysql", root)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { admin.Close() })
	name := fmt.Sprintf("migrate_test_%d", time.Now().UnixNano())
	if _, err := admin.Exec("CREATE DATABASE " + name + " CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _, _ = admin.Exec("DROP DATABASE " + name) })
	// backtestctl과 같이 parseTime=true (goose Status가 tstamp를 time.Time으로 읽는다).
	db, err := sql.Open("mysql", strings.TrimSuffix(root, "/")+"/"+name+"?charset=utf8mb4&parseTime=true")
	if err != nil {
		t.Fatal(err)
	}
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { db.Close() })
	return db
}

func closePrecision(t *testing.T, db *sql.DB) string {
	t.Helper()
	var p, s int
	if err := db.QueryRow(`SELECT NUMERIC_PRECISION, NUMERIC_SCALE FROM information_schema.COLUMNS
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_prices' AND COLUMN_NAME = 'close'`).Scan(&p, &s); err != nil {
		t.Fatal(err)
	}
	return fmt.Sprintf("%d,%d", p, s)
}

func TestUpOnEmptyDatabase(t *testing.T) {
	ctx := context.Background()
	db := tempDatabase(t)
	m, err := New(db, migrations.FS)
	if err != nil {
		t.Fatal(err)
	}
	results, err := m.Up(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != int(m.Latest()) {
		t.Fatalf("applied %d migrations, want %d", len(results), m.Latest())
	}
	if got := closePrecision(t, db); got != "38,18" {
		t.Fatalf("daily_prices.close precision %s", got)
	}
	// 한글 COMMENT가 이중 인코딩되지 않아야 한다 (schema.sql의 SET NAMES와 같은 문제).
	var comment string
	if err := db.QueryRow(`SELECT TABLE_COMMENT FROM information_schema.TABLES
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_news'`).Scan(&comment); err != nil {
		t.Fatal(err)
	}
	if comment != "종목별 뉴스 캐시" {
		t.Fatalf("table comment %q", comment)
	}
	again, err := m.Up(ctx)
	if err != nil || len(again) != 0 {
		t.Fatalf("second up: %v %v", again, err)
	}
	statuses, err := m.Status(ctx)
	if err != nil {
		t.Fatal(err)
	}
	for _, s := range statuses {
		if s.AppliedAt.IsZero() {
			t.Fatalf("version %d not applied", s.Source.Version)
		}
	}
	if err := m.Baseline(ctx, 1); err == nil {
		t.Fatal("baseline must refuse a goose-managed database")
	}
}

// Python 시절(Alembic 1f574a9ba22e) DB: 00001과 같은 테이블이 goose 기록 없이 있다.
func TestPythonEraDatabaseNeedsMatchingBaseline(t *testing.T) {
	ctx := context.Background()
	db := tempDatabase(t)
	baseline, err := fs.ReadFile(migrations.FS, "00001_baseline.sql")
	if err != nil {
		t.Fatal(err)
	}
	for _, stmt := range strings.Split(string(baseline), ";\n") {
		if strings.Contains(stmt, "CREATE TABLE") {
			if _, err := db.Exec(stmt); err != nil {
				t.Fatal(err)
			}
		}
	}
	if _, err := db.Exec(`INSERT INTO stocks (ticker) VALUES ('AAPL')`); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO daily_prices (stock_id, date, open, high, low, close, adj_close)
		VALUES (1, '2024-01-02', 1.5, 2, 1, 1.75, 1.75)`); err != nil {
		t.Fatal(err)
	}

	m, err := New(db, migrations.FS)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := m.Up(ctx); err == nil || !strings.Contains(err.Error(), "baseline 1") {
		t.Fatalf("up must refuse an unbaselined database and suggest baseline 1, got %v", err)
	}
	if v, err := m.Detect(ctx); err != nil || v != 1 {
		t.Fatalf("detect %d %v", v, err)
	}
	if err := m.Baseline(ctx, 2); err == nil {
		t.Fatal("baseline must refuse a version that does not match the schema")
	}
	if err := m.Baseline(ctx, 1); err != nil {
		t.Fatal(err)
	}
	results, err := m.Up(ctx)
	if err != nil || len(results) != 1 || results[0].Source.Version != 2 {
		t.Fatalf("up after baseline: %v %v", results, err)
	}
	if got := closePrecision(t, db); got != "38,18" {
		t.Fatalf("precision %s", got)
	}
	var close string
	if err := db.QueryRow(`SELECT close FROM daily_prices WHERE stock_id = 1`).Scan(&close); err != nil {
		t.Fatal(err)
	}
	if close != "1.750000000000000000" {
		t.Fatalf("existing row changed: %s", close)
	}
}
