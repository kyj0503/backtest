package api

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"os"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/admission"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/monitoring"
	"github.com/kyj0503/backtest/backtest_be_go/internal/news"
)

var quietLog = slog.New(slog.NewTextHandler(io.Discard, nil))

func testConfig(t testing.TB) config.Config {
	t.Helper()
	cfg, err := config.Load(func(k string) string {
		return map[string]string{"TURNSTILE_ENABLED": "false"}[k]
	})
	if err != nil {
		t.Fatal(err)
	}
	return cfg
}

func fixtureHistories(t testing.TB) marketdata.Histories {
	t.Helper()
	raw, err := os.ReadFile("../../testdata/rust/histories.json")
	if err != nil {
		t.Fatal(err)
	}
	var h marketdata.Histories
	if err := json.Unmarshal(raw, &h); err != nil {
		t.Fatal(err)
	}
	return h
}

type blockingFetcher struct {
	inner   marketdata.Fetcher
	release chan struct{}
}

func (b *blockingFetcher) Fetch(ctx context.Context, s string, start, end civil.Date) (marketdata.History, error) {
	select {
	case <-b.release:
	case <-ctx.Done():
		return marketdata.History{}, ctx.Err()
	}
	return b.inner.Fetch(ctx, s, start, end)
}

func newTestService(t testing.TB, fetcher marketdata.Fetcher, cfg config.Config) (*Service, http.Handler) {
	t.Helper()
	if fetcher == nil {
		fetcher = marketdata.NewFixtureFetcher(fixtureHistories(t))
	}
	reg := monitoring.NewRegistry()
	s := &Service{
		Cfg: cfg, Log: quietLog, Source: marketdata.NewSource(fetcher, nil, quietLog),
		News: news.NewService("", "", nil, quietLog), Turnstile: NewTurnstile(cfg.Turnstile),
		Calc:  admission.New(cfg.MaxConcurrentBacktests, cfg.MaxConcurrentBacktestsPerClient, "백테스트"),
		Reads: admission.New(cfg.MaxConcurrentMarketData, 4, "참고 데이터 조회"),
		Today: func() civil.Date { return civil.MustParse("2026-11-15") },
	}
	s.App = reg.NewApp(nil, monitoring.Gauges{})
	h := NewRouter(Deps{Config: cfg, Log: quietLog, Metrics: reg, Ready: fakeProbe{true, "ok"}, Service: s})
	return s, h
}

func post(h http.Handler, body string, header http.Header) *httptest.ResponseRecorder {
	req := httptest.NewRequest(http.MethodPost, "/api/v1/backtest", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	for k, v := range header {
		req.Header[k] = v
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func get(h http.Handler, path string) *httptest.ResponseRecorder {
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, path, nil))
	return rec
}

func jsonEqual(t *testing.T, got []byte, want any) bool {
	t.Helper()
	var g any
	if err := json.Unmarshal(got, &g); err != nil {
		t.Fatalf("invalid JSON %s", got)
	}
	w, _ := json.Marshal(want)
	var wv any
	_ = json.Unmarshal(w, &wv)
	return reflect.DeepEqual(g, wv)
}

// Python(FastAPI/pydantic)이 실제로 돌려준 422 본문 23개와 같아야 한다.
func TestHTTPBoundaryMatchesPython(t *testing.T) {
	raw, err := os.ReadFile("../../testdata/rust/http-boundary.json")
	if err != nil {
		t.Fatal(err)
	}
	var cases []struct {
		Name    string `json:"name"`
		Request struct {
			Method string          `json:"method"`
			Path   string          `json:"path"`
			Body   json.RawMessage `json:"body"`
			Raw    *string         `json:"raw"` // 잘못된 JSON처럼 본문을 문자 그대로 보내는 경우
		} `json:"request"`
		Expected any `json:"expected"`
	}
	if err := json.Unmarshal(raw, &cases); err != nil {
		t.Fatal(err)
	}
	if len(cases) != 23 {
		t.Fatalf("expected 23 cases, got %d", len(cases))
	}
	_, h := newTestService(t, nil, testConfig(t))
	for _, c := range cases {
		var rec *httptest.ResponseRecorder
		if c.Request.Method == http.MethodGet {
			rec = get(h, c.Request.Path)
		} else {
			body := string(c.Request.Body)
			if c.Request.Raw != nil {
				body = *c.Request.Raw
			}
			rec = post(h, body, nil)
		}
		if rec.Code != http.StatusUnprocessableEntity {
			t.Errorf("%s: status %d body %s", c.Name, rec.Code, rec.Body)
			continue
		}
		if !jsonEqual(t, rec.Body.Bytes(), c.Expected) {
			want, _ := json.Marshal(c.Expected)
			t.Errorf("%s:\n got  %s\n want %s", c.Name, rec.Body, want)
		}
	}
}

// 참고 조회의 변환 결과가 Python(unified_data_service)과 같아야 한다(testdata/rust/supplemental.json).
func TestReferenceReadsMatchPython(t *testing.T) {
	raw, err := os.ReadFile("../../testdata/rust/supplemental.json")
	if err != nil {
		t.Fatal(err)
	}
	var want map[string]any
	if err := json.Unmarshal(raw, &want); err != nil {
		t.Fatal(err)
	}
	_, h := newTestService(t, nil, testConfig(t))
	period := "start_date=2023-01-02&end_date=2023-10-31"
	prices := get(h, "/api/v1/prices?symbols=AAPL&symbols=msft&"+period)
	if prices.Code != 200 {
		t.Fatalf("prices %d %s", prices.Code, prices.Body)
	}
	var p struct {
		Data map[string]json.RawMessage `json:"data"`
	}
	_ = json.Unmarshal(prices.Body.Bytes(), &p)
	for _, key := range []string{"stock_data", "volatility_events"} {
		if !jsonEqual(t, p.Data[key], want[key]) {
			t.Errorf("%s differs from Python", key)
		}
	}
	if !jsonEqual(t, p.Data["supplemental_status"], map[string]string{"ticker_info": "ok", "stock_data": "ok", "volatility_events": "ok"}) {
		t.Errorf("status %s", p.Data["supplemental_status"])
	}

	fx := get(h, "/api/v1/exchange-rates?"+period)
	_ = json.Unmarshal(fx.Body.Bytes(), &p)
	for _, key := range []string{"exchange_rates", "exchange_stats"} {
		if !jsonEqual(t, p.Data[key], want[key]) {
			t.Errorf("%s differs from Python", key)
		}
	}
	bm := get(h, "/api/v1/benchmarks?"+period)
	_ = json.Unmarshal(bm.Body.Bytes(), &p)
	for _, key := range []string{"sp500_benchmark", "nasdaq_benchmark"} {
		if !jsonEqual(t, p.Data[key], want[key]) {
			t.Errorf("%s differs from Python", key)
		}
	}
	if string(p.Data["sp500_total_return_pct"]) == "null" {
		t.Error("sp500 total return missing")
	}
	nw := get(h, "/api/v1/news?symbols=AAPL")
	if nw.Code != 200 || !strings.Contains(nw.Body.String(), `"news":"empty"`) {
		t.Errorf("news without keys: %d %s", nw.Code, nw.Body)
	}
}

func TestBacktestSuccessWithSupplementalSections(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	body := `{"portfolio":[{"symbol":"aapl","amount":5000},{"symbol":"005930.KS","amount":5000}],
		"start_date":"2023-01-03","end_date":"2023-10-31","include_news":false}`
	rec := post(h, body, nil)
	if rec.Code != 200 {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
	var resp struct {
		Status string                     `json:"status"`
		Data   map[string]json.RawMessage `json:"data"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	for _, k := range []string{"portfolio_statistics", "ticker_info", "stock_data", "exchange_rates", "sp500_benchmark", "latest_news", "supplemental_status", "calculation_assumptions"} {
		if _, ok := resp.Data[k]; !ok {
			t.Errorf("missing %s", k)
		}
	}
	// 고정 시세의 AAPL·삼성전자에는 ±5% 이상 변동일이 없어 volatility_events는 empty다.
	if !jsonEqual(t, resp.Data["supplemental_status"], map[string]string{"ticker_info": "ok", "stock_data": "ok",
		"volatility_events": "empty", "exchange_rates": "ok", "benchmarks": "ok", "news": "skipped"}) {
		t.Errorf("status %s", resp.Data["supplemental_status"])
	}
	var stats map[string]any
	_ = json.Unmarshal(resp.Data["portfolio_statistics"], &stats)
	if stats["alpha_vs_sp500_pct"] == nil || stats["sp500_total_return_pct"] == nil {
		t.Errorf("benchmark comparison missing: %v", stats)
	}
	alpha := stats["alpha_vs_sp500_pct"].(float64)
	if d := stats["Time_Weighted_Return"].(float64) - stats["sp500_total_return_pct"].(float64); d != alpha {
		t.Errorf("alpha must be TWR - benchmark: %v vs %v", alpha, d)
	}
	var infos map[string]map[string]any
	_ = json.Unmarshal(resp.Data["ticker_info"], &infos)
	if infos["005930.KS"]["currency"] != "KRW" || infos["AAPL"] == nil {
		t.Errorf("ticker info %v", infos)
	}
	// Python 순서: 계산 결과 키 다음에 부가 데이터 키
	if i, j := strings.Index(rec.Body.String(), `"warnings"`), strings.Index(rec.Body.String(), `"ticker_info"`); i < 0 || j < i {
		t.Error("supplemental keys must follow the calculation keys")
	}
}

func TestMissingSymbolIsWarningAndAllMissingIs422(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	rec := post(h, `{"portfolio":[{"symbol":"AAPL","amount":1},{"symbol":"ZZZZ","amount":1}],"start_date":"2023-01-03","end_date":"2023-10-31","include_news":false,"include_benchmarks":false,"include_exchange_rates":false,"include_stock_data":false,"include_volatility_events":false}`, nil)
	if rec.Code != 200 || !strings.Contains(rec.Body.String(), "종목 ZZZZ의 가격 데이터를 불러오지 못해") {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
	rec = post(h, `{"portfolio":[{"symbol":"ZZZZ","amount":1}],"start_date":"2023-01-03","end_date":"2023-10-31"}`, nil)
	if rec.Code != 422 {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
}

func TestAdmissionLimits(t *testing.T) {
	cfg := testConfig(t)
	cfg.MaxConcurrentBacktests, cfg.MaxConcurrentBacktestsPerClient = 1, 1
	cfg.BacktestQueueTimeout, cfg.BacktestTimeout = 50*time.Millisecond, 100*time.Millisecond
	bf := &blockingFetcher{inner: marketdata.NewFixtureFetcher(fixtureHistories(t)), release: make(chan struct{})}
	s, h := newTestService(t, bf, cfg)
	s.Source.FetchBudget = 150 * time.Millisecond
	body := `{"portfolio":[{"symbol":"AAPL","amount":1}],"start_date":"2023-01-03","end_date":"2023-10-31"}`

	var wg sync.WaitGroup
	wg.Add(1)
	var first *httptest.ResponseRecorder
	go func() { defer wg.Done(); first = post(h, body, nil) }()
	for s.Calc.Running() == 0 {
		time.Sleep(time.Millisecond)
	}
	// 같은 클라이언트(httptest 기본 192.0.2.1)의 두 번째 요청은 즉시 429
	if rec := post(h, body, nil); rec.Code != 429 || rec.Header().Get("Retry-After") != "10" {
		t.Fatalf("per-client: %d %s", rec.Code, rec.Body)
	}
	// 다른 클라이언트는 슬롯을 기다리다 503
	other := http.Header{}
	req := httptest.NewRequest(http.MethodPost, "/api/v1/backtest", strings.NewReader(body))
	req.RemoteAddr = "198.51.100.7:1234"
	req.Header = other
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != 503 || rec.Header().Get("Retry-After") != "30" {
		t.Fatalf("queue timeout: %d %s", rec.Code, rec.Body)
	}
	wg.Wait()
	// 첫 요청은 시세가 오지 않아 실행 시간 초과(504)
	if first.Code != 504 {
		t.Fatalf("execution timeout: %d %s", first.Code, first.Body)
	}
	if s.Calc.Running() != 0 || s.Calc.Waiting() != 0 {
		t.Fatalf("slots leaked: running %d waiting %d", s.Calc.Running(), s.Calc.Waiting())
	}
	close(bf.release)
}

func TestClientKey(t *testing.T) {
	trusted := []netip.Prefix{netip.MustParsePrefix("10.0.0.0/8"), netip.MustParsePrefix("127.0.0.0/8")}
	cases := []struct {
		remote, xff, want string
	}{
		{"203.0.113.5:1", "1.2.3.4", "203.0.113.5"},           // 신뢰하지 않는 상대의 XFF는 무시
		{"10.0.0.2:1", "1.2.3.4, 10.0.0.9", "1.2.3.4"},        // 오른쪽부터 신뢰 대역을 건너뛴다
		{"10.0.0.2:1", "9.9.9.9, 1.2.3.4", "1.2.3.4"},         // 위조된 앞쪽 값은 쓰지 않는다
		{"10.0.0.2:1", "bogus, 1.2.3.4", "10.0.0.2"},          // 하나라도 IP가 아니면 헤더 전체 무시
		{"[2001:db8:1:2:3:4:5:6]:1", "", "2001:db8:1:2::/64"}, // IPv6는 /64
	}
	for _, c := range cases {
		r := httptest.NewRequest(http.MethodGet, "/", nil)
		r.RemoteAddr = c.remote
		if c.xff != "" {
			r.Header.Set("X-Forwarded-For", c.xff)
		}
		if got := clientKey(r, trusted); got != c.want {
			t.Errorf("%s %q: got %s want %s", c.remote, c.xff, got, c.want)
		}
	}
}

func TestTurnstile(t *testing.T) {
	var lastForm string
	verifier := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		b, _ := io.ReadAll(r.Body)
		lastForm = string(b)
		token := r.FormValue("response")
		if token == "" {
			_ = r.ParseForm()
		}
		switch {
		case strings.Contains(lastForm, "response=good"):
			_, _ = w.Write([]byte(`{"success":true,"hostname":"backtest.yeonjae.kr","action":"backtest"}`))
		case strings.Contains(lastForm, "response=otherhost"):
			_, _ = w.Write([]byte(`{"success":true,"hostname":"evil.example","action":"backtest"}`))
		case strings.Contains(lastForm, "response=down"):
			w.WriteHeader(500)
		default:
			_, _ = w.Write([]byte(`{"success":false}`))
		}
	}))
	defer verifier.Close()
	cfg := testConfig(t)
	cfg.Turnstile = config.Turnstile{Enabled: true, SecretKey: "s", AllowedHostnames: []string{"backtest.yeonjae.kr"},
		ExpectedAction: "backtest", Timeout: time.Second}
	s, h := newTestService(t, nil, cfg)
	s.Turnstile.verifyURL = verifier.URL
	body := `{"portfolio":[{"symbol":"AAPL","amount":1}],"start_date":"2023-01-03","end_date":"2023-10-31","include_news":false,"include_benchmarks":false,"include_exchange_rates":false,"include_stock_data":false,"include_volatility_events":false}`
	cases := []struct {
		tokens []string
		want   int
	}{
		{nil, 403}, {[]string{"good", "good"}, 403}, {[]string{strings.Repeat("x", 2049)}, 403},
		{[]string{"bad"}, 403}, {[]string{"otherhost"}, 403}, {[]string{"down"}, 503}, {[]string{"good"}, 200},
	}
	for _, c := range cases {
		hdr := http.Header{}
		for _, tok := range c.tokens {
			hdr.Add("X-Turnstile-Token", tok)
		}
		if rec := post(h, body, hdr); rec.Code != c.want {
			t.Errorf("tokens %v: %d %s", c.tokens, rec.Code, rec.Body)
		}
	}
	if !strings.Contains(lastForm, "secret=s") {
		t.Error("secret not sent")
	}
}

func TestUnclassifiedErrorHasOnlyAnID(t *testing.T) {
	s, _ := newTestService(t, nil, testConfig(t))
	rec := httptest.NewRecorder()
	s.writeErr(rec, io.ErrUnexpectedEOF)
	if rec.Code != 500 || !strings.Contains(rec.Body.String(), "오류 ID: ") || strings.Contains(rec.Body.String(), "EOF") {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
}

func TestBodyTooLarge(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	rec := post(h, `{"x":"`+strings.Repeat("a", maxBody)+`"}`, nil)
	if rec.Code != 413 {
		t.Fatalf("%d", rec.Code)
	}
	_ = bytes.MinRead
}

// 깨진 UTF-8 본문은 Python(Starlette)과 같이 400이다. U+FFFD로 바꿔 계산하지 않는다.
func TestInvalidUTF8BodyIs400(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	body := "{\"portfolio\":[{\"symbol\":\"\xbf\xb9\xb1\xdd\",\"amount\":1,\"asset_type\":\"cash\"}],\"start_date\":\"2023-01-03\",\"end_date\":\"2023-10-31\"}"
	rec := post(h, body, nil)
	if rec.Code != 400 || !strings.Contains(rec.Body.String(), "There was an error parsing the body") {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
}

// 조회 인자 오류는 Python(pydantic query 모델)이 실제로 돌려준 422 목록과 같아야 한다(2026-11-15 캡처).
func TestReadQueryErrorsMatchPython(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	ve := map[string]any{"error": map[string]any{}}
	cases := []struct {
		path string
		want []map[string]any
	}{
		{"/api/v1/prices?symbols=A%3CB&start_date=2023-01-02&end_date=2023-10-31", []map[string]any{{"type": "value_error", "loc": []any{"query", "symbols"},
			"msg": "Value error, 주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.", "input": map[string]any{"symbol": "A<B"}, "ctx": ve}}},
		{"/api/v1/prices?symbols=AAPL&start_date=2023-03-02&end_date=2023-02-01", []map[string]any{{"type": "value_error", "loc": []any{"query"},
			"msg": "Value error, 종료일은 시작일 이후여야 합니다.", "input": map[string]any{"symbols": []any{"AAPL"}, "start_date": "2023-03-02", "end_date": "2023-02-01"}, "ctx": ve}}},
		{"/api/v1/prices?symbols=AAPL&start_date=2023-01-02&end_date=2099-02-01", []map[string]any{{"type": "value_error", "loc": []any{"query"},
			"msg": "Value error, 미래 날짜는 조회할 수 없습니다.", "input": map[string]any{"symbols": []any{"AAPL"}, "start_date": "2023-01-02", "end_date": "2099-02-01"}, "ctx": ve}}},
		{"/api/v1/prices?symbols=AAPL&start_date=2003-01-02&end_date=2023-02-01", []map[string]any{{"type": "value_error", "loc": []any{"query"},
			"msg": "Value error, 조회 기간이 최대 허용 기간을 초과했습니다.", "input": map[string]any{"symbols": []any{"AAPL"}, "start_date": "2003-01-02", "end_date": "2023-02-01"}, "ctx": ve}}},
		{"/api/v1/prices?symbols=AAPL&start_date=2023-13-02&end_date=2023-02-01", []map[string]any{{"type": "date_from_datetime_parsing", "loc": []any{"query", "start_date"},
			"msg": "Input should be a valid date or datetime, month value is outside expected range of 1-12", "input": "2023-13-02",
			"ctx": map[string]any{"error": "month value is outside expected range of 1-12"}}}},
		{"/api/v1/news?symbols=", []map[string]any{{"type": "string_too_short", "loc": []any{"query", "symbols", "symbol"},
			"msg": "String should have at least 1 character", "input": "", "ctx": map[string]any{"min_length": 1}}}},
		{"/api/v1/news?symbols=%EC%98%88%EA%B8%88", []map[string]any{{"type": "value_error", "loc": []any{"query", "symbols"},
			"msg": "Value error, 주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.", "input": map[string]any{"symbol": "예금"}, "ctx": ve}}},
		{"/api/v1/news?symbols=A&symbols=B&symbols=C&symbols=D&symbols=E&symbols=F&symbols=G&symbols=H&symbols=I&symbols=J&symbols=K&symbols=L&symbols=M&symbols=N&symbols=O&symbols=P&symbols=Q&symbols=R&symbols=S&symbols=T&symbols=U",
			[]map[string]any{{"type": "too_long", "loc": []any{"query", "symbols"}, "msg": "List should have at most 20 items after validation, not 21",
				"input": []any{"A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"},
				"ctx":   map[string]any{"field_type": "List", "max_length": 20, "actual_length": 21}}}},
	}
	for _, c := range cases {
		rec := get(h, c.path)
		if rec.Code != 422 || !jsonEqual(t, rec.Body.Bytes(), map[string]any{"detail": c.want}) {
			t.Errorf("%s: %d %s", c.path, rec.Code, rec.Body)
		}
	}
}

// 시세를 찾지 못한 종목은 Python처럼 200에 빈 목록과 기본 종목 정보로 돌려준다.
func TestPricesUnknownSymbolIsEmptyNotError(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	rec := get(h, "/api/v1/prices?symbols=ZZZZ&start_date=2023-01-02&end_date=2023-10-31")
	want := map[string]any{"status": "success", "data": map[string]any{
		"ticker_info":         map[string]any{"ZZZZ": map[string]any{"symbol": "ZZZZ", "currency": nil, "company_name": "ZZZZ", "exchange": "Unknown", "first_trade_date": nil}},
		"stock_data":          map[string]any{"ZZZZ": []any{}},
		"volatility_events":   map[string]any{"ZZZZ": []any{}},
		"supplemental_status": map[string]any{"ticker_info": "ok", "stock_data": "empty", "volatility_events": "empty"},
	}}
	if rec.Code != 200 || !jsonEqual(t, rec.Body.Bytes(), want) {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
}

// 빈 본문은 FastAPI처럼 JSON 오류가 아니라 body 누락이다.
func TestEmptyBodyIsMissing(t *testing.T) {
	_, h := newTestService(t, nil, testConfig(t))
	rec := post(h, "", nil)
	want := map[string]any{"detail": []map[string]any{{"type": "missing", "loc": []any{"body"}, "msg": "Field required", "input": nil}}}
	if rec.Code != 422 || !jsonEqual(t, rec.Body.Bytes(), want) {
		t.Fatalf("%d %s", rec.Code, rec.Body)
	}
}
