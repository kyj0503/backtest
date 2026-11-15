package marketdata

import (
	"encoding/json"
	"math"
	"os"
	"testing"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// 실제 Yahoo 응답 7종(미국·한국·일본·독일·환율 2종·암호화폐)에 대해 날짜·통화·OHLC·거래량이
// 독립 계산(Python zoneinfo + 산술) 기대값과 같아야 한다. 허용 오차는 1e-12 상대값.
func TestCapturedYahooResponses(t *testing.T) {
	raw, err := os.ReadFile("../../testdata/rust/yahoo-chart-regression.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Cases []struct {
			Symbol   string          `json:"symbol"`
			Currency string          `json:"currency"`
			Raw      json.RawMessage `json:"raw"`
			Expected []Bar           `json:"expected"`
		} `json:"cases"`
	}
	if err := json.Unmarshal(raw, &fixture); err != nil {
		t.Fatal(err)
	}
	if len(fixture.Cases) != 7 {
		t.Fatalf("expected 7 cases, got %d", len(fixture.Cases))
	}
	for _, c := range fixture.Cases {
		h, err := ParseChart(c.Symbol, c.Raw)
		if err != nil {
			t.Errorf("%s: %v", c.Symbol, err)
			continue
		}
		if h.Currency != c.Currency {
			t.Errorf("%s: currency %s", c.Symbol, h.Currency)
		}
		if len(h.Bars) != len(c.Expected) {
			t.Errorf("%s: %d bars, want %d", c.Symbol, len(h.Bars), len(c.Expected))
			continue
		}
		for i, want := range c.Expected {
			got := h.Bars[i]
			if got.Date != want.Date {
				t.Errorf("%s[%d]: date %s want %s", c.Symbol, i, got.Date, want.Date)
			}
			pairs := [][2]float64{{got.Open, want.Open}, {got.High, want.High}, {got.Low, want.Low},
				{got.Close, want.Close}, {got.Volume, want.Volume}}
			for k, p := range pairs {
				if math.Abs(p[0]-p[1]) > 1e-12*math.Max(1, math.Abs(p[1])) {
					t.Errorf("%s %s field %d: %v != %v", c.Symbol, got.Date, k, p[0], p[1])
				}
			}
		}
	}
}

// chart는 합성 응답을 만든다: 모든 봉 O=100 H=120 L=80 C=100, 수정종가 100.
type chart map[string]any

func newChart(zone string, instants []time.Time) chart {
	n := len(instants)
	ts := make([]int64, n)
	for i, t := range instants {
		ts[i] = t.Unix()
	}
	fill := func(v float64) []any {
		out := make([]any, n)
		for i := range out {
			out[i] = v
		}
		return out
	}
	return chart{"chart": map[string]any{"error": nil, "result": []any{map[string]any{
		"meta": map[string]any{"currency": "USD", "symbol": "TEST", "exchangeTimezoneName": zone,
			"gmtoffset": 3600, "exchangeName": "TST", "longName": "Test Corp"},
		"timestamp": ts,
		"indicators": map[string]any{
			"quote":    []any{map[string]any{"open": fill(100), "high": fill(120), "low": fill(80), "close": fill(100), "volume": fill(1000)}},
			"adjclose": []any{map[string]any{"adjclose": fill(100)}},
		},
	}}}}
}

func (c chart) result() map[string]any {
	return c["chart"].(map[string]any)["result"].([]any)[0].(map[string]any)
}
func (c chart) quote(field string) []any {
	return c.result()["indicators"].(map[string]any)["quote"].([]any)[0].(map[string]any)[field].([]any)
}
func (c chart) adj() []any {
	return c.result()["indicators"].(map[string]any)["adjclose"].([]any)[0].(map[string]any)["adjclose"].([]any)
}
func (c chart) bytes(t *testing.T) []byte {
	b, err := json.Marshal(c)
	if err != nil {
		t.Fatal(err)
	}
	return b
}

func days(start string, n int) []time.Time {
	d := civil.MustParse(start).Time()
	out := make([]time.Time, n)
	for i := range out {
		out[i] = d.AddDate(0, 0, i)
	}
	return out
}

func status(err error) int { return apperr.Status(err) }

// T01: 주식의 수정종가가 하나라도 없으면 가격 기준이 섞이므로 503이다.
func TestMissingStockAdjustmentIsUnavailable(t *testing.T) {
	base := newChart("UTC", days("2023-01-02", 40))
	for i := range base.adj() {
		base.adj()[i] = 50.0
	}
	h, err := ParseChart("TEST", base.bytes(t))
	if err != nil {
		t.Fatal(err)
	}
	for _, b := range h.Bars {
		if b.Close != 50 || b.Open != 50 || b.High != 60 || b.Low != 40 {
			t.Fatalf("adjustment ratio must apply once to OHLC: %+v", b)
		}
	}
	for _, missing := range []int{0, 20, 39} {
		c := newChart("UTC", days("2023-01-02", 40))
		c.adj()[missing] = nil
		if _, err := ParseChart("TEST", c.bytes(t)); status(err) != 503 {
			t.Errorf("missing adjclose at %d: %v", missing, err)
		}
	}
	c := newChart("UTC", days("2023-01-02", 40))
	delete(c.result()["indicators"].(map[string]any), "adjclose")
	if _, err := ParseChart("TEST", c.bytes(t)); status(err) != 503 {
		t.Errorf("absent adjclose: %v", err)
	}
	// 환율은 기업 행사가 없으므로 수정종가가 없으면 원종가를 쓴다.
	if h, err := ParseChart("KRW=X", c.bytes(t)); err != nil || h.Bars[0].Close != 100 {
		t.Errorf("FX without adjclose: %v %+v", err, h.Bars)
	}
}

// T02: 일부만 비었거나 0·음수·모순인 봉은 503, 전부 비어 있는 봉(휴장)만 건너뛴다.
func TestInvalidBarsFailButAbsentBarsAreSkipped(t *testing.T) {
	cases := []struct {
		field string
		value any
	}{
		{"open", 1.0}, {"open", 1000.0}, {"close", 0.0}, {"low", -1.0}, {"high", 79.0}, {"open", nil},
	}
	for _, tc := range cases {
		c := newChart("UTC", days("2023-01-02", 40))
		c.quote(tc.field)[20] = tc.value
		if _, err := ParseChart("TEST", c.bytes(t)); status(err) != 503 {
			t.Errorf("%s=%v: %v", tc.field, tc.value, err)
		}
	}
	c := newChart("UTC", days("2023-01-02", 40))
	for _, f := range []string{"open", "high", "low", "close"} {
		c.quote(f)[20] = nil
	}
	c.adj()[20] = nil
	h, err := ParseChart("TEST", c.bytes(t))
	if err != nil || len(h.Bars) != 39 {
		t.Fatalf("absent bar must be skipped: %v %d", err, len(h.Bars))
	}
}

// 날짜는 그 시점의 거래소 시간대 규칙으로 정한다. gmtoffset(3600)은 일부러 틀린 값이다.
func TestExchangeDatesFollowHistoricalTimeZoneRules(t *testing.T) {
	cases := []struct {
		zone    string
		instant string
		want    string
	}{
		// 뉴욕 장 시작 09:30 EST = 14:30Z (겨울), 09:30 EDT = 13:30Z (여름)
		{"America/New_York", "2023-01-03T14:30:00Z", "2023-01-03"},
		{"America/New_York", "2023-07-03T13:30:00Z", "2023-07-03"},
		// 서울 자정 직후 봉은 UTC로는 전날이다
		{"Asia/Seoul", "2023-03-01T15:00:00Z", "2023-03-02"},
		{"Asia/Tokyo", "2023-03-01T15:30:00Z", "2023-03-02"},
		// 런던 자정 봉: 겨울 00:00Z, 여름(BST) 23:00Z 전날
		{"Europe/London", "2023-01-09T00:00:00Z", "2023-01-09"},
		{"Europe/London", "2023-06-11T23:00:00Z", "2023-06-12"},
	}
	for _, tc := range cases {
		instant, _ := time.Parse(time.RFC3339, tc.instant)
		h, err := ParseChart("TEST", newChart(tc.zone, []time.Time{instant}).bytes(t))
		if err != nil {
			t.Fatal(err)
		}
		if got := h.Bars[0].Date.String(); got != tc.want {
			t.Errorf("%s %s: got %s want %s", tc.zone, tc.instant, got, tc.want)
		}
	}
	// 시간대 이름이 없을 때만 gmtoffset을 쓴다.
	instant, _ := time.Parse(time.RFC3339, "2023-01-09T23:30:00Z")
	h, err := ParseChart("TEST", newChart("", []time.Time{instant}).bytes(t))
	if err != nil || h.Bars[0].Date.String() != "2023-01-10" {
		t.Fatalf("gmtoffset fallback: %v %v", err, h.Bars)
	}
	if _, err := ParseChart("TEST", newChart("Mars/Olympus", []time.Time{instant}).bytes(t)); status(err) != 503 {
		t.Fatalf("unknown zone: %v", err)
	}
}

func TestMalformedResponses(t *testing.T) {
	c := newChart("UTC", days("2023-01-02", 5))
	q := c.result()["indicators"].(map[string]any)["quote"].([]any)[0].(map[string]any)
	q["close"] = q["close"].([]any)[:4]
	if _, err := ParseChart("TEST", c.bytes(t)); status(err) != 503 {
		t.Errorf("length mismatch: %v", err)
	}
	notFoundBody := []byte(`{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found, symbol may be delisted"}}}`)
	if _, err := ParseChart("ZZZZ", notFoundBody); status(err) != 404 {
		t.Errorf("not found: %v", err)
	}
	if _, err := ParseChart("TEST", []byte(`{"chart":{"result":[{"meta":{},"indicators":{}}],"error":null}}`)); status(err) != 404 {
		t.Errorf("no timestamps: %v", err)
	}
	if _, err := ParseChart("TEST", []byte(`<html>`)); status(err) != 503 {
		t.Errorf("html: %v", err)
	}
}

func TestDuplicateDatesKeepFirstAndSort(t *testing.T) {
	ts := days("2023-01-02", 3)
	ts = append(ts, ts[1].Add(time.Hour)) // 같은 날 두 번째 봉
	c := newChart("UTC", []time.Time{ts[2], ts[0], ts[1], ts[3]})
	c.quote("close")[2] = 110.0
	c.quote("high")[2] = 120.0
	c.adj()[2] = 110.0
	h, err := ParseChart("TEST", c.bytes(t))
	if err != nil {
		t.Fatal(err)
	}
	if len(h.Bars) != 3 || h.Bars[0].Date.String() != "2023-01-02" || h.Bars[1].Close != 110 {
		t.Fatalf("%+v", h.Bars)
	}
	if h.CompanyName != "Test Corp" || h.Exchange != "TST" {
		t.Fatalf("meta %+v", h)
	}
}
