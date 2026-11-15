// Command server는 백테스트 HTTP 서버다.
//
//	server              서버 실행 (SIGTERM/SIGINT에 graceful shutdown)
//	server -healthcheck 같은 컨테이너의 /health를 조회해 종료 코드로 알린다
//	                    (distroless 런타임에는 curl이 없어 Docker HEALTHCHECK가 이걸 쓴다)
package main

import (
	"context"
	"database/sql"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
	_ "time/tzdata" // 거래소 시간대를 이미지의 tzdata 유무와 상관없이 쓰기 위해 내장한다

	"github.com/go-sql-driver/mysql"

	"github.com/kyj0503/backtest/backtest_be_go/internal/admission"
	"github.com/kyj0503/backtest/backtest_be_go/internal/api"
	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
	"github.com/kyj0503/backtest/backtest_be_go/internal/health"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/monitoring"
	"github.com/kyj0503/backtest/backtest_be_go/internal/news"
)

func main() {
	healthcheck := flag.Bool("healthcheck", false, "query /health on the local server and exit")
	flag.Parse()

	if *healthcheck {
		os.Exit(runHealthcheck())
	}
	if err := run(); err != nil {
		slog.Error("server stopped", "error", err)
		os.Exit(1)
	}
}

func run() error {
	cfg, err := config.FromEnvironment()
	if err != nil {
		return fmt.Errorf("invalid configuration: %w", err)
	}
	log := newLogger(cfg.LogLevel)
	slog.SetDefault(log)
	// 드라이버 자체 로그(연결 끊김 등)도 같은 형식으로 남긴다.
	_ = mysql.SetLogger(slog.NewLogLogger(log.Handler(), slog.LevelWarn))
	log.Info("database configuration loaded", "database", cfg.Database.Redacted())

	// 설정 오류(CA 파일 없음 등)는 첫 요청이 아니라 기동 시점에 드러나게 한다.
	if _, err := cfg.Database.DriverConfig(cfg.ReadinessDBTimeout); err != nil {
		return err
	}
	probe := health.NewDBProbe(func() (*sql.DB, error) {
		dc, err := cfg.Database.DriverConfig(cfg.ReadinessDBTimeout)
		if err != nil {
			return nil, err
		}
		connector, err := mysql.NewConnector(dc)
		if err != nil {
			return nil, err
		}
		return sql.OpenDB(connector), nil
	}, cfg.ReadinessDBTimeout, log)

	service, closeService, err := newService(cfg, log)
	if err != nil {
		return err
	}
	defer closeService()
	metrics := monitoring.NewRegistry()
	allow := make([]string, 0, len(news.TickerNames)+len(popularETFs))
	for k := range news.TickerNames {
		allow = append(allow, k)
	}
	allow = append(allow, popularETFs...)
	service.App = metrics.NewApp(allow, monitoring.Gauges{
		BacktestRunning: func() float64 { return float64(service.Calc.Running()) },
		BacktestWaiting: func() float64 { return float64(service.Calc.Waiting()) },
		MarketRunning:   func() float64 { return float64(service.Reads.Running()) },
		MarketWaiting:   func() float64 { return float64(service.Reads.Waiting()) },
	})

	handler := api.NewRouter(api.Deps{
		Config:  cfg,
		Log:     log,
		Metrics: metrics,
		Ready:   probe,
		Service: service,
	})

	srv := &http.Server{
		Addr:              cfg.ListenAddr(),
		Handler:           handler,
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       120 * time.Second,
		ErrorLog:          slog.NewLogLogger(log.Handler(), slog.LevelWarn),
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	errCh := make(chan error, 1)
	go func() {
		log.Info("server listening", "addr", srv.Addr, "version", config.Version,
			"docs", config.APIPrefix+"/docs")
		errCh <- srv.ListenAndServe()
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
	}
	log.Info("shutdown requested")
	// 진행 중인 백테스트(최대 대기 + 실행 시간)가 끝날 시간을 준다.
	grace := cfg.BacktestQueueTimeout + cfg.BacktestTimeout + 5*time.Second
	shutdownCtx, cancel := context.WithTimeout(context.Background(), grace)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("graceful shutdown: %w", err)
	}
	if err := <-errCh; !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	log.Info("server stopped cleanly")
	return nil
}

// popularETFs는 ticker_popularity_total 라벨 허용 목록에 더하는 주요 ETF다(Python과 같다).
var popularETFs = []string{"SPY", "QQQ", "VOO", "VTI", "IVV", "DIA", "IWM", "SCHD", "JEPI", "TQQQ", "SQQQ",
	"SOXL", "SOXX", "SMH", "ARKK", "GLD", "SLV", "TLT", "IEF", "SHY", "BND", "AGG",
	"VNQ", "VEA", "VWO", "EFA", "EEM", "XLK", "XLF", "XLE", "XLV", "BRK-B"}

// newService는 시세 원천(Yahoo 또는 고정 픽스처), MySQL 캐시, 뉴스, 실행 슬롯을 만든다.
func newService(cfg config.Config, log *slog.Logger) (*api.Service, func(), error) {
	var db *sql.DB
	if cfg.Database.Configured {
		dc, err := cfg.Database.DriverConfig(0)
		if err != nil {
			return nil, nil, err
		}
		connector, err := mysql.NewConnector(dc)
		if err != nil {
			return nil, nil, err
		}
		db = sql.OpenDB(connector)
		db.SetMaxOpenConns(cfg.Database.MaxOpenConns)
		db.SetMaxIdleConns(cfg.Database.MaxIdleConns)
		db.SetConnMaxLifetime(cfg.Database.ConnMaxLifetime)
	}
	var fetcher marketdata.Fetcher = marketdata.NewYahoo(cfg.YahooTimeout, log)
	if cfg.FixtureFile != "" {
		f, err := marketdata.LoadFixtures(cfg.FixtureFile)
		if err != nil {
			return nil, nil, err
		}
		log.Warn("using fixture market data instead of Yahoo (DEBUG only)", "file", cfg.FixtureFile)
		fetcher = f
	}
	var store marketdata.Store
	if db != nil {
		store = marketdata.NewMySQLStore(db)
	}
	s := &api.Service{
		Cfg:       cfg,
		Log:       log,
		Source:    marketdata.NewSource(fetcher, store, log),
		News:      news.NewService(cfg.NaverClientID, cfg.NaverClientSecret, db, log),
		Turnstile: api.NewTurnstile(cfg.Turnstile),
		Calc:      admission.New(cfg.MaxConcurrentBacktests, cfg.MaxConcurrentBacktestsPerClient, "백테스트"),
		Reads:     admission.New(cfg.MaxConcurrentMarketData, 4, "참고 데이터 조회"),
		Today:     api.SeoulToday,
	}
	if cfg.FixtureFile != "" {
		// 고정 시세에는 뉴스가 없다. 외부 API를 부르지 않는다.
		s.News.ClientID, s.News.ClientSecret = "", ""
	}
	closeFn := func() {
		if db != nil {
			_ = db.Close()
		}
	}
	return s, closeFn, nil
}

func newLogger(level string) *slog.Logger {
	var l slog.Level
	switch level {
	case "DEBUG":
		l = slog.LevelDebug
	case "WARNING", "WARN":
		l = slog.LevelWarn
	case "ERROR", "CRITICAL":
		l = slog.LevelError
	default:
		l = slog.LevelInfo
	}
	return slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: l}))
}

func runHealthcheck() int {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Get("http://127.0.0.1:" + port + "/health")
	if err != nil {
		fmt.Fprintln(os.Stderr, "healthcheck:", err)
		return 1
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		fmt.Fprintln(os.Stderr, "healthcheck: status", resp.StatusCode)
		return 1
	}
	return 0
}
