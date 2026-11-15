package marketdata

import (
	"math"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

func rates(ticker string, points map[string]float64) History {
	h := History{Symbol: ticker}
	for _, d := range []string{"2023-01-02", "2023-01-03", "2023-01-05", "2023-01-06"} {
		if v, ok := points[d]; ok {
			h.Bars = append(h.Bars, Bar{Date: civil.MustParse(d), Open: v, High: v, Low: v, Close: v})
		}
	}
	return h
}

func TestRateDirectionAndForwardFillOnly(t *testing.T) {
	data := Histories{
		"KRW=X":    rates("KRW=X", map[string]float64{"2023-01-03": 1300, "2023-01-05": 2600}),
		"EURUSD=X": rates("EURUSD=X", map[string]float64{"2023-01-02": 1.25}),
		"JPY=X":    rates("JPY=X", map[string]float64{"2023-01-02": 125}),
	}
	cases := []struct {
		currency string
		day      string
		want     float64
	}{
		{"USD", "2023-01-01", 1},
		{"KRW", "2023-01-03", 1.0 / 1300},
		{"KRW", "2023-01-04", 1.0 / 1300}, // 휴장일은 직전 값
		{"KRW", "2023-01-05", 1.0 / 2600},
		{"EUR", "2023-01-06", 1.25}, // EURUSD는 곱한다
		{"JPY", "2023-01-02", 1.0 / 125},
	}
	for _, tc := range cases {
		got, err := RateOn(tc.currency, civil.MustParse(tc.day), data)
		if err != nil || math.Abs(got-tc.want) > 1e-15 {
			t.Errorf("%s %s: %v %v want %v", tc.currency, tc.day, got, err, tc.want)
		}
	}
	// 첫 환율보다 앞선 날은 미래 값으로 메우지 않는다.
	if _, err := RateOn("KRW", civil.MustParse("2023-01-02"), data); err == nil {
		t.Error("back-filled a future rate")
	}
	if _, err := RateOn("XYZ", civil.MustParse("2023-01-05"), data); err == nil {
		t.Error("unsupported currency accepted")
	}
	if _, err := RateOn("GBP", civil.MustParse("2023-01-05"), data); err == nil {
		t.Error("missing rate series accepted")
	}
}

// 독립 원장: 수정 원화 주가 65,000원, 진입 환율 1,300원/USD, 원금 $1,000이면 20 단위.
// 종료 환율이 2,600원/USD면 평가액은 $500이다.
func TestKRWLedgerExample(t *testing.T) {
	data := Histories{"KRW=X": rates("KRW=X", map[string]float64{"2023-01-03": 1300, "2023-01-05": 2600})}
	in, _ := RateOn("KRW", civil.MustParse("2023-01-03"), data)
	out, _ := RateOn("KRW", civil.MustParse("2023-01-05"), data)
	units := 1000 / (65000 * in)
	if math.Abs(units-20) > 1e-12 || math.Abs(units*65000*out-500) > 1e-9 {
		t.Fatalf("units %v value %v", units, units*65000*out)
	}
}

func TestSupportedCurrenciesMatchPython(t *testing.T) {
	want := []string{"USD", "KRW", "JPY", "EUR", "GBP", "CNY", "HKD", "TWD", "SGD", "AUD", "CAD", "CHF", "INR"}
	for _, c := range want {
		if _, ok := FXTicker(c); !ok {
			t.Errorf("%s unsupported", c)
		}
	}
	if len(supportedFX)+1 != len(want) {
		t.Errorf("currency table has %d entries", len(supportedFX)+1)
	}
}
