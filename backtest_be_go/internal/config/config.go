// Package config는 환경 변수에서 서버 설정을 읽는다.
//
// 이름과 기본값은 Python 백엔드(app/core/config.py)와 같게 유지한다. 운영 .env를 바꾸지 않고
// 백엔드만 교체할 수 있어야 하기 때문이다. 환경 변수 이름은 대문자다(compose env_file 기준).
package config

import (
	"errors"
	"fmt"
	"math"
	"net/netip"
	"os"
	"strconv"
	"strings"
	"time"
)

// Version은 /health 응답과 OpenAPI info.version에 실린다.
const Version = "1.7.10"

// APIPrefix는 모든 공개 API의 경로 접두사다.
const APIPrefix = "/api/v1"

type Config struct {
	Host     string
	Port     int
	Debug    bool
	LogLevel string

	Turnstile Turnstile
	Database  Database

	MaxPortfolioItems        int
	MaxSymbolLength          int
	MaxBacktestDurationDays  int
	MaxBacktestDurationYears int
	MinBacktestPeriodDays    int
	DefaultCommission        float64

	MaxConcurrentBacktests          int
	MaxConcurrentBacktestsPerClient int
	BacktestTimeout                 time.Duration
	BacktestQueueTimeout            time.Duration
	BacktestCancelGrace             time.Duration
	TrustedProxies                  []netip.Prefix

	MaxConcurrentMarketData int
	MarketDataQueueTimeout  time.Duration
	MarketDataTimeout       time.Duration

	ReadinessDBTimeout     time.Duration
	SupplementalDataBudget time.Duration

	YahooTimeout           time.Duration
	ExchangeRateTicker     string
	VolatilityThresholdPct float64

	NaverClientID     string
	NaverClientSecret string

	// FixtureFile이 있으면 시장 데이터를 외부 대신 이 JSON(testdata/rust/histories.json 형식)에서 읽는다.
	// E2E 전용이며 Debug가 켜져 있을 때만 허용한다.
	FixtureFile string
}

type Turnstile struct {
	Enabled          bool
	SecretKey        string
	AllowedHostnames []string
	ExpectedAction   string
	Timeout          time.Duration
}

// Getenv는 테스트에서 환경을 바꿔 끼울 수 있게 하는 조회 함수다.
type Getenv func(string) string

// FromEnvironment는 프로세스 환경 변수로 Load를 호출한다.
func FromEnvironment() (Config, error) { return Load(os.Getenv) }

// DatabaseFromEnvironment는 DB 설정만 읽는다. backtestctl처럼 HTTP 설정(Turnstile 등)이 필요 없는
// 도구가 쓴다.
func DatabaseFromEnvironment() (Database, error) { return loadDatabase(os.Getenv) }

// Load는 환경 변수를 읽어 검증한다. 잘못된 값은 기본값으로 대체하지 않고 오류로 돌려준다.
func Load(getenv Getenv) (Config, error) {
	r := reader{getenv: getenv}
	c := Config{
		Host:     r.str("HOST", "0.0.0.0"),
		Port:     r.integer("PORT", 8000),
		Debug:    r.boolean("DEBUG", false),
		LogLevel: strings.ToUpper(r.str("LOG_LEVEL", "INFO")),

		Turnstile: Turnstile{
			// 운영 설정이 빠졌을 때 요청이 통과하면 안 되므로 기본값은 켜짐이다.
			Enabled:          r.boolean("TURNSTILE_ENABLED", true),
			SecretKey:        r.str("TURNSTILE_SECRET_KEY", ""),
			AllowedHostnames: splitList(r.str("TURNSTILE_ALLOWED_HOSTNAMES", "")),
			ExpectedAction:   r.str("TURNSTILE_EXPECTED_ACTION", "backtest"),
			Timeout:          r.seconds("TURNSTILE_TIMEOUT_SECONDS", 5),
		},

		MaxPortfolioItems:        r.integer("MAX_PORTFOLIO_ITEMS", 20),
		MaxSymbolLength:          r.integer("MAX_SYMBOL_LENGTH", 10),
		MaxBacktestDurationDays:  r.integer("MAX_BACKTEST_DURATION_DAYS", 3650),
		MaxBacktestDurationYears: r.integer("MAX_BACKTEST_DURATION_YEARS", 10),
		MinBacktestPeriodDays:    r.integer("MIN_BACKTEST_PERIOD_DAYS", 30),
		DefaultCommission:        r.float("DEFAULT_COMMISSION", 0.002),

		MaxConcurrentBacktests:          r.integer("MAX_CONCURRENT_BACKTESTS", 8),
		MaxConcurrentBacktestsPerClient: r.integer("MAX_CONCURRENT_BACKTESTS_PER_CLIENT", 2),
		BacktestTimeout:                 r.seconds("BACKTEST_TIMEOUT_SECONDS", 60),
		BacktestQueueTimeout:            r.seconds("BACKTEST_QUEUE_TIMEOUT_SECONDS", 30),
		BacktestCancelGrace:             r.seconds("BACKTEST_CANCEL_GRACE_SECONDS", 15),
		TrustedProxies: r.prefixes("TRUSTED_PROXY_CIDRS",
			"127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fc00::/7"),

		MaxConcurrentMarketData: r.integer("MAX_CONCURRENT_MARKET_DATA", 4),
		MarketDataQueueTimeout:  r.seconds("MARKET_DATA_QUEUE_TIMEOUT_SECONDS", 2),
		MarketDataTimeout:       r.seconds("MARKET_DATA_TIMEOUT_SECONDS", 20),

		ReadinessDBTimeout:     r.seconds("READINESS_DB_TIMEOUT_SECONDS", 2),
		SupplementalDataBudget: r.seconds("SUPPLEMENTAL_DATA_TIMEOUT_SECONDS", 15),

		YahooTimeout:           r.seconds("YAHOO_FINANCE_TIMEOUT", 30),
		ExchangeRateTicker:     r.str("EXCHANGE_RATE_TICKER", "KRW=X"),
		VolatilityThresholdPct: r.float("VOLATILITY_THRESHOLD_PCT", 5),

		NaverClientID:     r.str("NAVER_CLIENT_ID", ""),
		NaverClientSecret: r.str("NAVER_CLIENT_SECRET", ""),

		FixtureFile: r.str("BACKTEST_FIXTURE_FILE", ""),
	}

	db, err := loadDatabase(getenv)
	if err != nil {
		r.errs = append(r.errs, err)
	}
	c.Database = db

	r.errs = append(r.errs, c.validate()...)
	if len(r.errs) > 0 {
		return Config{}, errors.Join(r.errs...)
	}
	return c, nil
}

func (c Config) validate() []error {
	var errs []error
	check := func(ok bool, format string, args ...any) {
		if !ok {
			errs = append(errs, fmt.Errorf(format, args...))
		}
	}
	check(c.Port > 0 && c.Port < 65536, "PORT must be 1-65535, got %d", c.Port)
	switch c.LogLevel {
	case "DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL":
	default:
		errs = append(errs, fmt.Errorf("LOG_LEVEL %q is not one of DEBUG, INFO, WARNING, ERROR, CRITICAL", c.LogLevel))
	}
	check(c.Turnstile.Timeout > 0 && c.Turnstile.Timeout <= 10*time.Second,
		"TURNSTILE_TIMEOUT_SECONDS must be in (0, 10]")
	if c.Turnstile.Enabled {
		check(c.Turnstile.SecretKey != "", "TURNSTILE_SECRET_KEY is required when TURNSTILE_ENABLED=true")
		check(len(c.Turnstile.AllowedHostnames) > 0,
			"TURNSTILE_ALLOWED_HOSTNAMES is required when TURNSTILE_ENABLED=true")
	}
	check(c.MaxConcurrentBacktests > 0, "MAX_CONCURRENT_BACKTESTS must be positive")
	check(c.MaxConcurrentMarketData > 0, "MAX_CONCURRENT_MARKET_DATA must be positive")
	check(c.BacktestTimeout > 0 && c.BacktestQueueTimeout > 0, "backtest timeouts must be positive")
	check(c.MarketDataTimeout > 0 && c.MarketDataQueueTimeout > 0, "market data timeouts must be positive")
	check(c.ReadinessDBTimeout > 0, "READINESS_DB_TIMEOUT_SECONDS must be positive")
	check(c.SupplementalDataBudget > 0, "SUPPLEMENTAL_DATA_TIMEOUT_SECONDS must be positive")
	check(c.MinBacktestPeriodDays > 0 && c.MinBacktestPeriodDays <= c.MaxBacktestDurationDays,
		"MIN_BACKTEST_PERIOD_DAYS must be in [1, MAX_BACKTEST_DURATION_DAYS]")
	check(c.FixtureFile == "" || c.Debug, "BACKTEST_FIXTURE_FILE is only allowed with DEBUG=true")
	return errs
}

// ListenAddr는 net/http가 쓰는 host:port 문자열이다.
func (c Config) ListenAddr() string {
	host := c.Host
	if strings.Contains(host, ":") && !strings.HasPrefix(host, "[") {
		host = "[" + host + "]"
	}
	return fmt.Sprintf("%s:%d", host, c.Port)
}

type reader struct {
	getenv Getenv
	errs   []error
}

func (r *reader) raw(name string) (string, bool) {
	v := strings.TrimSpace(r.getenv(name))
	return v, v != ""
}

func (r *reader) str(name, def string) string {
	if v, ok := r.raw(name); ok {
		return v
	}
	return def
}

func (r *reader) integer(name string, def int) int {
	v, ok := r.raw(name)
	if !ok {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		r.errs = append(r.errs, fmt.Errorf("%s: %q is not an integer", name, v))
		return def
	}
	return n
}

func (r *reader) float(name string, def float64) float64 {
	v, ok := r.raw(name)
	if !ok {
		return def
	}
	f, err := strconv.ParseFloat(v, 64)
	if err != nil || math.IsNaN(f) || math.IsInf(f, 0) {
		r.errs = append(r.errs, fmt.Errorf("%s: %q is not a finite number", name, v))
		return def
	}
	return f
}

func (r *reader) seconds(name string, def float64) time.Duration {
	f := r.float(name, def)
	return time.Duration(f * float64(time.Second))
}

// boolean은 pydantic과 같은 표기(true/false, 1/0, yes/no, on/off)를 받는다.
func (r *reader) boolean(name string, def bool) bool {
	v, ok := r.raw(name)
	if !ok {
		return def
	}
	switch strings.ToLower(v) {
	case "1", "true", "t", "yes", "y", "on":
		return true
	case "0", "false", "f", "no", "n", "off":
		return false
	}
	r.errs = append(r.errs, fmt.Errorf("%s: %q is not a boolean", name, v))
	return def
}

func (r *reader) prefixes(name, def string) []netip.Prefix {
	var out []netip.Prefix
	for _, item := range splitList(r.str(name, def)) {
		p, err := netip.ParsePrefix(item)
		if err != nil {
			r.errs = append(r.errs, fmt.Errorf("%s: %q is not a CIDR", name, item))
			continue
		}
		out = append(out, p.Masked())
	}
	return out
}

func splitList(v string) []string {
	var out []string
	for _, item := range strings.Split(v, ",") {
		if item = strings.TrimSpace(item); item != "" {
			out = append(out, item)
		}
	}
	return out
}
