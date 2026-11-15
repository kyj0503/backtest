package config

import (
	"strings"
	"testing"
	"time"
)

func env(values map[string]string) Getenv {
	return func(name string) string { return values[name] }
}

func devEnv() map[string]string {
	return map[string]string{
		"TURNSTILE_ENABLED": "false",
		"DATABASE_URL":      "mysql+pymysql://appuser:appuser123@mysql:3306/stock_data_cache?charset=utf8mb4",
	}
}

func TestDefaultsMatchPythonSettings(t *testing.T) {
	c, err := Load(env(devEnv()))
	if err != nil {
		t.Fatal(err)
	}
	checks := []struct {
		name      string
		got, want any
	}{
		{"port", c.Port, 8000},
		{"max items", c.MaxPortfolioItems, 20},
		{"min period", c.MinBacktestPeriodDays, 30},
		{"max days", c.MaxBacktestDurationDays, 3650},
		{"commission", c.DefaultCommission, 0.002},
		{"concurrent", c.MaxConcurrentBacktests, 8},
		{"per client", c.MaxConcurrentBacktestsPerClient, 2},
		{"timeout", c.BacktestTimeout, 60 * time.Second},
		{"queue", c.BacktestQueueTimeout, 30 * time.Second},
		{"market concurrent", c.MaxConcurrentMarketData, 4},
		{"market queue", c.MarketDataQueueTimeout, 2 * time.Second},
		{"market timeout", c.MarketDataTimeout, 20 * time.Second},
		{"readiness", c.ReadinessDBTimeout, 2 * time.Second},
		{"supplemental", c.SupplementalDataBudget, 15 * time.Second},
		{"turnstile action", c.Turnstile.ExpectedAction, "backtest"},
		{"fx ticker", c.ExchangeRateTicker, "KRW=X"},
		{"trusted proxies", len(c.TrustedProxies), 6},
	}
	for _, tc := range checks {
		if tc.got != tc.want {
			t.Errorf("%s = %v, want %v", tc.name, tc.got, tc.want)
		}
	}
}

func TestTurnstileEnabledByDefaultRequiresSecrets(t *testing.T) {
	e := devEnv()
	delete(e, "TURNSTILE_ENABLED")
	_, err := Load(env(e))
	if err == nil || !strings.Contains(err.Error(), "TURNSTILE_SECRET_KEY") {
		t.Fatalf("expected missing secret error, got %v", err)
	}
	e["TURNSTILE_SECRET_KEY"] = "s"
	e["TURNSTILE_ALLOWED_HOSTNAMES"] = "backtest.yeonjae.kr, localhost"
	c, err := Load(env(e))
	if err != nil {
		t.Fatal(err)
	}
	if !c.Turnstile.Enabled || len(c.Turnstile.AllowedHostnames) != 2 || c.Turnstile.AllowedHostnames[1] != "localhost" {
		t.Fatalf("unexpected turnstile config %+v", c.Turnstile)
	}
}

func TestInvalidValuesAreErrorsNotDefaults(t *testing.T) {
	cases := map[string]string{
		"PORT":                     "eighty",
		"DEBUG":                    "maybe",
		"BACKTEST_TIMEOUT_SECONDS": "NaN",
		"TRUSTED_PROXY_CIDRS":      "10.0.0.0/33",
		"LOG_LEVEL":                "VERBOSE",
		"BACKTEST_FIXTURE_FILE":    "/fixtures/histories.json", // DEBUG 없이 금지
	}
	for name, value := range cases {
		e := devEnv()
		e[name] = value
		if _, err := Load(env(e)); err == nil || !strings.Contains(err.Error(), name) {
			t.Errorf("%s=%q: expected error naming the variable, got %v", name, value, err)
		}
	}
}

func TestListenAddrBracketsIPv6(t *testing.T) {
	if got := (Config{Host: "::", Port: 8000}).ListenAddr(); got != "[::]:8000" {
		t.Fatalf("got %q", got)
	}
	if got := (Config{Host: "0.0.0.0", Port: 8000}).ListenAddr(); got != "0.0.0.0:8000" {
		t.Fatalf("got %q", got)
	}
}
