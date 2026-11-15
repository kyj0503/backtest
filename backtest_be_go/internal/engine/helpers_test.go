package engine

import (
	"context"
	"encoding/json"
	"math"
	"os"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

var testLimits = Limits{MinPeriodDays: 30, MaxPeriodDays: 3650, MaxItems: 20, MaxSymbolLen: 10, Today: civil.MustParse("2026-11-15")}

var day0 = civil.MustParse("2023-01-02")

// series는 2023-01-02부터 매일(주말 포함) 봉을 만든다. opens가 nil이면 시가 = 종가.
func series(symbol string, closes []float64, opens []float64) marketdata.History {
	h := marketdata.History{Symbol: symbol, Currency: "USD", CompanyName: symbol, Exchange: "test"}
	for i, c := range closes {
		o := c
		if opens != nil {
			o = opens[i]
		}
		h.Bars = append(h.Bars, marketdata.Bar{Date: day0.AddDays(i), Open: o, Close: c,
			High: math.Max(c, o), Low: math.Min(c, o), Volume: 1e6})
	}
	return h
}

func flat(n int, v float64) []float64 {
	out := make([]float64, n)
	for i := range out {
		out[i] = v
	}
	return out
}

// request는 TEST 1종목 $10,000, 수수료 0, 리밸런싱 없음, n일 기간에 extra(JSON)를 덮어쓴 요청이다.
func request(t *testing.T, extra string, n int) Request {
	t.Helper()
	base := map[string]any{
		"portfolio":           []any{map[string]any{"symbol": "TEST", "amount": 10000}},
		"start_date":          day0.String(),
		"end_date":            day0.AddDays(n - 1).String(),
		"commission":          0,
		"rebalance_frequency": "none",
	}
	if extra != "" {
		var e map[string]any
		if err := json.Unmarshal([]byte(extra), &e); err != nil {
			t.Fatal(err)
		}
		for k, v := range e {
			base[k] = v
		}
	}
	raw, _ := json.Marshal(base)
	return decodeRequest(t, raw)
}

func decodeRequest(t *testing.T, raw []byte) Request {
	t.Helper()
	r := Defaults()
	if err := json.Unmarshal(raw, &r); err != nil {
		t.Fatalf("decode %s: %v", raw, err)
	}
	return r
}

func run(t *testing.T, req Request, hs ...marketdata.History) *Data {
	t.Helper()
	d, err := Run(context.Background(), req, histories(hs...), testLimits)
	if err != nil {
		t.Fatalf("run: %v", err)
	}
	return d
}

func histories(hs ...marketdata.History) marketdata.Histories {
	out := marketdata.Histories{}
	for _, h := range hs {
		out[h.Symbol] = h
	}
	return out
}

func runErr(t *testing.T, req Request, hs ...marketdata.History) int {
	t.Helper()
	_, err := Run(context.Background(), req, histories(hs...), testLimits)
	if err == nil {
		t.Fatal("expected an error")
	}
	return apperr.Status(err)
}

func near(t *testing.T, what string, got, want float64) {
	t.Helper()
	if math.Abs(got-want) >= 1e-7 {
		t.Errorf("%s: got %.12g want %.12g", what, got, want)
	}
}

// view는 응답을 JSON으로 왕복해 클라이언트가 보는 형태로 돌려준다.
func view(t *testing.T, d *Data) map[string]any {
	t.Helper()
	raw, err := json.Marshal(d)
	if err != nil {
		t.Fatal(err)
	}
	var out map[string]any
	if err := json.Unmarshal(raw, &out); err != nil {
		t.Fatal(err)
	}
	return out
}

func num(v any) float64 { return v.(float64) }

func obj(v any, path ...string) any {
	for _, p := range path {
		v = v.(map[string]any)[p]
	}
	return v
}

func readJSON(t *testing.T, path string, v any) {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(raw, v); err != nil {
		t.Fatal(err)
	}
}
