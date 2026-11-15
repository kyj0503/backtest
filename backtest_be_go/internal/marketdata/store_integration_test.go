//go:build integration

package marketdata

import (
	"context"
	"database/sql"
	"fmt"
	"math"
	"os"
	"strings"
	"sync"
	"testing"
	"time"

	_ "github.com/go-sql-driver/mysql"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/migrate"
	"github.com/kyj0503/backtest/backtest_be_go/migrations"
)

// testDB는 goose head 스키마를 가진 임시 DB다. 서버와 같은 세션 설정(UTC)을 쓴다.
func testDB(t *testing.T) *sql.DB {
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
	name := fmt.Sprintf("store_test_%d", time.Now().UnixNano())
	if _, err := admin.Exec("CREATE DATABASE " + name + " CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _, _ = admin.Exec("DROP DATABASE " + name) })
	dsn := strings.TrimSuffix(root, "/") + "/" + name + "?charset=utf8mb4&time_zone=%27%2B00%3A00%27"
	mdb, err := sql.Open("mysql", dsn+"&parseTime=true")
	if err != nil {
		t.Fatal(err)
	}
	m, err := migrate.New(mdb, migrations.FS)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := m.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	mdb.Close()
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	return db
}

func bars(from string, closes ...float64) []Bar {
	d := civil.MustParse(from)
	out := make([]Bar, len(closes))
	for i, c := range closes {
		out[i] = Bar{Date: d.AddDays(i), Open: c, High: c, Low: c, Close: c, Volume: 1e6}
	}
	return out
}

func TestStoreRoundTripKeepsSubCentPrecision(t *testing.T) {
	ctx := context.Background()
	s := NewMySQLStore(testDB(t))
	first := civil.MustParse("2023-01-02")
	ftd := civil.MustParse("1980-12-12")
	h := History{Symbol: "ZZTINY", Currency: "USD", CompanyName: "주식회사 테스트", Exchange: "NMS",
		FirstTradeDate: &ftd, Bars: bars("2023-01-02", 0.00001, 0.00003, 123456.123456789)}
	if err := s.Save(ctx, h, first, first.AddDays(2)); err != nil {
		t.Fatal(err)
	}
	got, err := s.Cached(ctx, "ZZTINY", first, first.AddDays(2))
	if err != nil || got == nil {
		t.Fatalf("%v %v", got, err)
	}
	for i, want := range []float64{0.00001, 0.00003, 123456.123456789} {
		if math.Abs(got.Bars[i].Close-want) > 1e-15*math.Max(1, want) {
			t.Errorf("bar %d: %v want %v", i, got.Bars[i].Close, want)
		}
	}
	if got.Currency != "USD" || got.CompanyName != "주식회사 테스트" || got.FirstTradeDate == nil || *got.FirstTradeDate != ftd {
		t.Fatalf("metadata %+v", got)
	}
	// 요청 구간이 스냅샷 밖이면 쓰지 않는다.
	if c, _ := s.Cached(ctx, "ZZTINY", first.AddDays(-1), first.AddDays(2)); c != nil {
		t.Fatal("snapshot used outside its range")
	}
}

// 분할 뒤 일부 구간만 새로 받아도 이전 기준의 행과 섞지 않는다(F05).
func TestPartialRefreshReplacesTheWholeSnapshot(t *testing.T) {
	ctx := context.Background()
	db := testDB(t)
	s := NewMySQLStore(db)
	first := civil.MustParse("2023-01-02")
	last := first.AddDays(1)
	if err := s.Save(ctx, History{Symbol: "ZZSPLIT", Currency: "USD", Bars: bars("2023-01-02", 100, 50)}, first, last); err != nil {
		t.Fatal(err)
	}
	if err := s.Save(ctx, History{Symbol: "ZZSPLIT", Currency: "USD", Bars: bars("2023-01-03", 50)}, last, last); err != nil {
		t.Fatal(err)
	}
	if c, _ := s.Cached(ctx, "ZZSPLIT", first, last); c != nil {
		t.Fatal("partial refresh merged with an older adjustment basis")
	}
	var n int
	_ = db.QueryRow(`SELECT COUNT(*) FROM daily_prices`).Scan(&n)
	if n != 1 {
		t.Fatalf("old rows kept: %d", n)
	}
}

func TestSuspiciousOrStaleSnapshotsAreNotUsed(t *testing.T) {
	ctx := context.Background()
	db := testDB(t)
	s := NewMySQLStore(db)
	first := civil.MustParse("2023-01-02")
	last := first.AddDays(2)
	if err := s.Save(ctx, History{Symbol: "ZZQ", Currency: "USD", Bars: bars("2023-01-02", 1, 2, 3)}, first, last); err != nil {
		t.Fatal(err)
	}
	if c, _ := s.Cached(ctx, "ZZQ", first, last); c == nil {
		t.Fatal("fresh snapshot not used")
	}
	if _, err := db.Exec(`UPDATE daily_prices SET data_quality = 'suspicious' WHERE date = '2023-01-03'`); err != nil {
		t.Fatal(err)
	}
	if c, _ := s.Cached(ctx, "ZZQ", first, last); c != nil {
		t.Fatal("suspicious row accepted")
	}
	if _, err := db.Exec(`UPDATE daily_prices SET data_quality = 'good'`); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`DELETE FROM daily_prices WHERE date = '2023-01-03'`); err != nil {
		t.Fatal(err)
	}
	if c, _ := s.Cached(ctx, "ZZQ", first, last); c != nil {
		t.Fatal("snapshot with a removed row accepted")
	}
	if err := s.Save(ctx, History{Symbol: "ZZQ", Currency: "USD", Bars: bars("2023-01-02", 1, 2, 3)}, first, last); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`UPDATE stocks SET data_last_update = UTC_TIMESTAMP() - INTERVAL 2 HOUR`); err != nil {
		t.Fatal(err)
	}
	if c, _ := s.Cached(ctx, "ZZQ", first, last); c != nil {
		t.Fatal("stale snapshot accepted")
	}
}

// Python·Rust가 남긴 행(스냅샷 표식 없음)은 캐시로 쓰지 않는다.
func TestLegacyRowsAreRefetched(t *testing.T) {
	ctx := context.Background()
	db := testDB(t)
	if _, err := db.Exec(`INSERT INTO stocks (ticker, info_json, data_last_update) VALUES ('AAPL', '{"currency":"USD"}', UTC_TIMESTAMP())`); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO daily_prices (stock_id, date, open, high, low, close) VALUES (1, '2023-01-02', 1, 1, 1, 1)`); err != nil {
		t.Fatal(err)
	}
	d := civil.MustParse("2023-01-02")
	if c, err := NewMySQLStore(db).Cached(ctx, "AAPL", d, d); c != nil || err != nil {
		t.Fatalf("legacy rows used: %v %v", c, err)
	}
}

func TestFailedSaveKeepsPreviousSnapshot(t *testing.T) {
	ctx := context.Background()
	db := testDB(t)
	s := NewMySQLStore(db)
	first := civil.MustParse("2023-01-02")
	last := first.AddDays(1)
	if err := s.Save(ctx, History{Symbol: "ZZFX=X", Currency: "KRW", Bars: bars("2023-01-02", 1300, 1301)}, first, last); err != nil {
		t.Fatal(err)
	}
	broken := History{Symbol: "ZZFX=X", Currency: "KRW", Bars: bars("2023-01-02", 1300, 1301)}
	broken.Bars[1].High = 1 // CHECK (high >= low) 위반 → INSERT 실패 → 롤백
	if err := s.Save(ctx, broken, first, last); err == nil {
		t.Fatal("constraint violation not reported")
	}
	if c, _ := s.Cached(ctx, "ZZFX=X", first, last); c == nil || len(c.Bars) != 2 {
		t.Fatalf("previous snapshot lost: %+v", c)
	}
	if err := s.Save(ctx, History{Symbol: "ZZNEW", Currency: "USD", Bars: broken.Bars}, first, last); err == nil {
		t.Fatal("constraint violation not reported")
	}
	var n int
	_ = db.QueryRow(`SELECT COUNT(*) FROM stocks WHERE ticker = 'ZZNEW'`).Scan(&n)
	if n != 0 {
		t.Fatal("failed child insert left the parent row")
	}
	if err := s.Save(ctx, History{Symbol: "ZZBIG", Currency: "USD", Bars: bars("2023-01-02", 1e-13)}, first, first); err == nil {
		t.Fatal("unstorable price accepted")
	}
}

func TestOrphanPrices(t *testing.T) {
	ctx := context.Background()
	db := testDB(t)
	s := NewMySQLStore(db)
	d := civil.MustParse("2023-01-02")
	if err := s.Save(ctx, History{Symbol: "ZZKEEP", Currency: "USD", Bars: bars("2023-01-02", 1, 2)}, d, d.AddDays(1)); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO daily_prices (stock_id, date, open, high, low, close) VALUES (999, '2023-01-02', 1, 1, 1, 1), (999, '2023-01-03', 1, 1, 1, 1)`); err != nil {
		t.Fatal(err)
	}
	rows, ids, err := OrphanPrices(ctx, db)
	if err != nil || rows != 2 || ids != 1 {
		t.Fatalf("%d %d %v", rows, ids, err)
	}
	n, err := DeleteOrphanPrices(ctx, db)
	if err != nil || n != 2 {
		t.Fatalf("%d %v", n, err)
	}
	if c, _ := s.Cached(ctx, "ZZKEEP", d, d.AddDays(1)); c == nil || len(c.Bars) != 2 {
		t.Fatal("non-orphan rows were deleted")
	}
}

// 같은 종목의 교체와 읽기를 동시에 많이 해도 읽기는 완전한 스냅샷만 본다.
func TestConcurrentReplaceAndRead(t *testing.T) {
	ctx := context.Background()
	s := NewMySQLStore(testDB(t))
	first := civil.MustParse("2023-01-02")
	last := first.AddDays(29)
	closes := func(v float64) []float64 {
		out := make([]float64, 30)
		for i := range out {
			out[i] = v
		}
		return out
	}
	if err := s.Save(ctx, History{Symbol: "ZZC", Currency: "USD", Bars: bars("2023-01-02", closes(1)...)}, first, last); err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	errs := make(chan error, 100)
	for w := range 4 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range 15 {
				v := float64(w*100 + i + 2)
				if err := s.Save(ctx, History{Symbol: "ZZC", Currency: "USD", Bars: bars("2023-01-02", closes(v)...)}, first, last); err != nil {
					errs <- err
				}
			}
		}()
	}
	for range 4 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for range 40 {
				c, err := s.Cached(ctx, "ZZC", first, last)
				if err != nil {
					errs <- err
					continue
				}
				if c == nil {
					continue
				}
				if len(c.Bars) != 30 {
					errs <- fmt.Errorf("partial snapshot: %d bars", len(c.Bars))
				}
				for _, b := range c.Bars {
					if b.Close != c.Bars[0].Close {
						errs <- fmt.Errorf("mixed snapshot")
						break
					}
				}
			}
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Error(err)
	}
}
