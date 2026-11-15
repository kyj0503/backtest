// Command backtestctl은 운영·배치 작업 도구다. 서버와 같은 환경 변수(DATABASE_URL 등)를 읽는다.
//
//	backtestctl migrate status            적용 상태 출력
//	backtestctl migrate up                대기 중인 마이그레이션 적용 (백업 후 실행)
//	backtestctl migrate detect            goose 기록이 없는 기존 DB의 스키마 버전 판별
//	backtestctl migrate baseline <ver>    기존 DB에 <ver>까지 적용됨 표시 (SQL 실행 없음, 백업 후 실행)
//	backtestctl check-orphans [--delete]  부모 stocks 행이 없는 일봉 점검(발견 시 종료 코드 1) / 삭제
//
// Python 배치 중 daily_price_update / manage_stock_splits / update_ticker_listing_dates는 옮기지 않는다.
// 시세 캐시는 종목 단위 스냅샷(1시간 유효)을 통째로 교체하므로 분할·배당 조정이 다음 조회에 자동 반영되고,
// 상장일은 시세 응답 메타에서 매번 온다. 미리 받아 둔 5년치 시세는 1시간 뒤 쓰이지 않는다.
package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	_ "time/tzdata"

	"github.com/go-sql-driver/mysql"

	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/migrate"
	"github.com/kyj0503/backtest/backtest_be_go/migrations"
)

const usage = `usage:
  backtestctl migrate status
  backtestctl migrate up
  backtestctl migrate detect
  backtestctl migrate baseline <version>
  backtestctl check-orphans [--delete]`

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	err := run(ctx, os.Args[1:])
	stop()
	if err != nil {
		fmt.Fprintln(os.Stderr, "backtestctl:", err)
		if errors.Is(err, errUsage) {
			fmt.Fprintln(os.Stderr, usage)
			os.Exit(2)
		}
		os.Exit(1)
	}
}

var errUsage = errors.New("invalid arguments")

// errOrphansFound는 점검 모드에서 고아 행을 찾았다는 뜻이다(종료 코드 1, cron 알림 조건).
var errOrphansFound = errors.New("orphan daily_prices rows found")

func run(ctx context.Context, args []string) error {
	if len(args) >= 1 && args[0] == "check-orphans" {
		del := false
		switch {
		case len(args) == 2 && args[1] == "--delete":
			del = true
		case len(args) != 1:
			return errUsage
		}
		return checkOrphans(ctx, del)
	}
	if len(args) < 2 || args[0] != "migrate" {
		return errUsage
	}
	db, err := openDB()
	if err != nil {
		return err
	}
	defer db.Close()
	m, err := migrate.New(db, migrations.FS)
	if err != nil {
		return err
	}

	switch args[1] {
	case "status":
		statuses, err := m.Status(ctx)
		if err != nil {
			return err
		}
		for _, s := range statuses {
			applied := "pending"
			if !s.AppliedAt.IsZero() {
				applied = "applied " + s.AppliedAt.UTC().Format("2006-01-02T15:04:05Z")
			}
			fmt.Printf("%05d  %-40s %s\n", s.Source.Version, baseName(s.Source.Path), applied)
		}
		return nil
	case "up":
		results, err := m.Up(ctx)
		for _, r := range results {
			fmt.Printf("applied %05d %s (%s)\n", r.Source.Version, baseName(r.Source.Path), r.Duration)
		}
		if err != nil {
			return err
		}
		if len(results) == 0 {
			fmt.Println("no pending migrations")
		}
		return nil
	case "detect":
		v, err := m.Detect(ctx)
		if err != nil {
			return err
		}
		fmt.Println(v)
		return nil
	case "baseline":
		if len(args) != 3 {
			return errUsage
		}
		v, err := strconv.ParseInt(args[2], 10, 64)
		if err != nil {
			return errUsage
		}
		if err := m.Baseline(ctx, v); err != nil {
			return err
		}
		fmt.Printf("recorded versions 1..%d as applied in %s\n", v, migrate.VersionTable)
		return nil
	}
	return errUsage
}

func checkOrphans(ctx context.Context, del bool) error {
	db, err := openDB()
	if err != nil {
		return err
	}
	defer db.Close()
	rows, ids, err := marketdata.OrphanPrices(ctx, db)
	if err != nil {
		return err
	}
	fmt.Printf("orphan daily_prices rows: %d (stock_id values: %d)\n", rows, ids)
	if rows == 0 {
		return nil
	}
	if !del {
		return errOrphansFound
	}
	n, err := marketdata.DeleteOrphanPrices(ctx, db)
	if err != nil {
		return err
	}
	fmt.Printf("deleted %d rows\n", n)
	return nil
}

func openDB() (*sql.DB, error) {
	dbCfg, err := config.DatabaseFromEnvironment()
	if err != nil {
		return nil, err
	}
	dc, err := dbCfg.DriverConfig(0)
	if err != nil {
		return nil, err
	}
	// goose 버전 테이블의 tstamp(TIMESTAMP)를 time.Time으로 읽으려면 필요하다. 서버와 달리
	// backtestctl은 시세 DATE 컬럼을 다루지 않으므로 시간대 해석 문제가 없다.
	dc.ParseTime = true
	connector, err := mysql.NewConnector(dc)
	if err != nil {
		return nil, err
	}
	db := sql.OpenDB(connector)
	db.SetMaxOpenConns(1)
	return db, nil
}

func baseName(path string) string {
	for i := len(path) - 1; i >= 0; i-- {
		if path[i] == '/' {
			return path[i+1:]
		}
	}
	return path
}
