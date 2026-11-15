package engine

import (
	"math"
	"strconv"
	"testing"
)

func tradeLog(t *testing.T, d *Data, key string) []map[string]any {
	t.Helper()
	v := view(t, d)
	raw := obj(v, "strategy_details", key, "trade_log").([]any)
	out := make([]map[string]any, len(raw))
	for i, r := range raw {
		out[i] = r.(map[string]any)
	}
	return out
}

// F01: 마지막 봉의 신호는 과거(그 봉의 시가)로 체결하지 않는다. 기간을 늘려도 기존 날짜의 평가는 같다.
func TestFinalSignalCannotTradeInThePast(t *testing.T) {
	p := make([]float64, 40)
	for i := range p {
		p[i] = 100 - float64(i)*0.2
	}
	p[39] = 200
	o := append([]float64(nil), p...)
	o[39] = 100
	req := request(t, `{"strategy":"ema_strategy","strategy_params":{"fast_window":5,"slow_window":10}}`, 40)
	d := run(t, req, series("TEST", p, o))
	near(t, "final", d.PortfolioStatistics.FinalValue, 10000)
	if len(tradeLog(t, d, "TEST")) != 0 {
		t.Fatal("trade from the final signal")
	}
	p2 := append(append([]float64(nil), p...), 200)
	o2 := append(append([]float64(nil), o...), 200)
	longer := req
	longer.EndDate = req.EndDate.AddDays(1)
	ext := run(t, longer, series("TEST", p2, o2))
	a, _ := d.EquityCurve.Get("2023-02-10")
	b, _ := ext.EquityCurve.Get("2023-02-10")
	if a != b {
		t.Fatalf("extending the period changed a past valuation: %v vs %v", a, b)
	}
}

// F02: 진입·청산 모두 수수료를 내고, 미청산 포지션은 마지막 종가로 평가한다.
func TestBothSidesPayCommission(t *testing.T) {
	p := make([]float64, 40)
	for i := range p {
		switch {
		case i < 4:
			p[i] = 100
		case i >= 14 && i < 24:
			p[i] = 110
		default:
			p[i] = 90
		}
	}
	d := run(t, request(t, `{"strategy":"ema_strategy","strategy_params":{"fast_window":5,"slow_window":10},"commission":0.01}`, 40),
		series("TEST", p, flat(40, 100)))
	tr := tradeLog(t, d, "TEST")[0]
	q := num(tr["Size"])
	near(t, "commission", num(tr["Commission"]), q*2)
	near(t, "pnl", num(tr["PnL"]), -q*2)
	near(t, "final", d.PortfolioStatistics.FinalValue, 10000-q*2)
}

// F08: RSI는 첫 n개 변화의 평균으로 시작하고, 완전 평탄 구간은 50(신호 없음)이다.
func TestWilderSeedAndFlatRSI(t *testing.T) {
	p := flat(40, 100)
	p[1] = 101
	d := run(t, request(t, `{"strategy":"rsi_strategy","strategy_params":{"rsi_period":2,"rsi_oversold":40,"rsi_overbought":70}}`, 40),
		series("TEST", p, nil))
	v := view(t, d)
	if len(obj(v, "strategy_details", "TEST", "trade_log").([]any)) != 0 || len(obj(v, "strategy_details", "TEST", "open_positions").([]any)) != 0 {
		t.Fatal("flat RSI must not trade")
	}
}

// S01: 소수 단위 수량이라 가격 단위를 바꿔도 같은 경제 경로의 자산 가치가 같다. 체결은 다음 봉 시가.
func TestFractionalUnitsAndNextOpenLedger(t *testing.T) {
	for _, fee := range []float64{0, 0.01} {
		q := 9500 / (980 * (1 + fee))
		expected := 10000 - q*970*(1+fee) + q*1500*(1-fee)
		for _, scale := range []float64{0.01, 0.5, 1, 2, 100} {
			p := flat(40, 1500*scale)
			copy(p, []float64{1000 * scale, 990 * scale, 980 * scale, 970 * scale})
			d := run(t, request(t, `{"strategy":"rsi_strategy","strategy_params":{"rsi_period":2},"commission":`+strconv.FormatFloat(fee, 'f', -1, 64)+`}`, 40),
				series("TEST", p, nil))
			near(t, "final", d.PortfolioStatistics.FinalValue, expected)
			tr := tradeLog(t, d, "TEST")[0]
			near(t, "size", num(tr["Size"]), q/scale)
			near(t, "commission", num(tr["Commission"]), q*(970+1500)*fee)
			if tr["EntryTime"] != "2023-01-05T00:00:00" || tr["QuantityUnit"] != "fractional_adjusted_unit" {
				t.Fatalf("%v", tr)
			}
		}
	}
}

func TestAllStrategiesPreserveWealthUnderUnitChange(t *testing.T) {
	p := make([]float64, 120)
	half := make([]float64, 120)
	for i := range p {
		p[i] = 100 + 20*math.Sin(float64(i)/7) + float64(i)/10
		half[i] = p[i] / 2
	}
	for _, s := range []string{"sma_strategy", "ema_strategy", "macd_strategy", "rsi_strategy", "bollinger_strategy"} {
		req := request(t, `{"strategy":"`+s+`","commission":0.01}`, 120)
		a := run(t, req, series("TEST", p, nil))
		b := run(t, req, series("TEST", half, nil))
		for _, k := range a.EquityCurve.Keys() {
			x, _ := a.EquityCurve.Get(k)
			y, _ := b.EquityCurve.Get(k)
			near(t, s+" "+k, x, y)
		}
		if a.PortfolioStatistics.TotalTrades == 0 {
			t.Errorf("%s: scenario produced no trades", s)
		}
	}
}

// S04: 체결 가격은 USD, *Native는 체결일 환율의 종목 통화 가격이다.
func TestNativeExecutionPrices(t *testing.T) {
	p := flat(40, 110000)
	copy(p, []float64{100000, 99000, 98000})
	stock := series("TEST", p, nil)
	stock.Currency = "KRW"
	stock.Bars[3].Open, stock.Bars[3].Low = 97000, 97000
	rates := make([]float64, 40)
	for i := range rates {
		rates[i] = 1000 + float64(i)
	}
	d := run(t, request(t, `{"strategy":"rsi_strategy","strategy_params":{"rsi_period":2}}`, 40), stock, series("KRW=X", rates, nil))
	tr := tradeLog(t, d, "TEST")[0]
	near(t, "entry native", num(tr["EntryPriceNative"]), 97000)
	near(t, "entry usd", num(tr["EntryPrice"]), 97000.0/1003)
	near(t, "exit native", num(tr["ExitPriceNative"]), 110000)
	if tr["NativeCurrency"] != "KRW" || tr["PriceCurrency"] != "USD" {
		t.Fatal(tr)
	}
}

// T03: 볼린저는 첫 완성 창의 봉부터 신호를 보고 다음 봉 시가에 체결한다.
func TestBollingerFirstCompleteWindow(t *testing.T) {
	for _, period := range []int{5, 20} {
		for _, fee := range []float64{0, 0.01} {
			for _, delay := range []int{0, 1} {
				signal := period - 1 + delay
				h := series("TEST", flat(40, 100), nil)
				h.Bars[signal].Open, h.Bars[signal].Close, h.Bars[signal].Low = 80, 80, 80
				h.Bars[signal+1].Open, h.Bars[signal+1].Low = 80, 80
				req := request(t, `{"strategy":"bollinger_strategy","strategy_params":{"period":`+strconv.Itoa(period)+`,"std_dev":1},"commission":`+strconv.FormatFloat(fee, 'f', -1, 64)+`}`, 40)
				d := run(t, req, h)
				q := 9500 / (80 * (1 + fee))
				near(t, "final", d.PortfolioStatistics.FinalValue, 10000-q*80*(1+fee)+q*100*(1-fee))
				tr := tradeLog(t, d, "TEST")[0]
				if tr["EntryTime"] != day0.AddDays(signal+1).String()+"T00:00:00" || tr["ExitTime"] != day0.AddDays(signal+2).String()+"T00:00:00" ||
					num(tr["EntryPrice"]) != 80 || num(tr["ExitPrice"]) != 100 {
					t.Fatalf("period %d delay %d: %v", period, delay, tr)
				}
			}
		}
	}
	d := run(t, request(t, `{"strategy":"bollinger_strategy","strategy_params":{"period":100,"std_dev":1}}`, 40), series("TEST", flat(40, 100), nil))
	if d.PortfolioStatistics.FinalValue != 10000 || len(tradeLog(t, d, "TEST")) != 0 {
		t.Fatal("incomplete window traded")
	}
}

func TestStrategyRejectsDCAAndRebalance(t *testing.T) {
	for _, extra := range []string{
		`{"strategy":"sma_strategy","rebalance_frequency":"monthly_1"}`,
		`{"strategy":"sma_strategy","portfolio":[{"symbol":"TEST","amount":100,"investment_type":"dca"}]}`,
		`{"strategy":"sma_strategy","strategy_params":{"short_window":30,"long_window":20}}`,
		`{"strategy":"sma_strategy","strategy_params":{"short_window":1}}`,
	} {
		if code := runErr(t, request(t, extra, 40), series("TEST", flat(40, 100), nil)); code != 422 {
			t.Errorf("%s: %d", extra, code)
		}
	}
}

func TestStrategyCashAndZeroWeight(t *testing.T) {
	req := request(t, `{"strategy":"sma_strategy","portfolio":[{"symbol":"TEST","weight":100},{"symbol":"현금","weight":0,"asset_type":"cash"}]}`, 40)
	d := run(t, req, series("TEST", flat(40, 100), nil))
	if len(d.Warnings) != 1 {
		t.Fatalf("%q", d.Warnings)
	}
	near(t, "final", d.PortfolioStatistics.FinalValue, 100)
	if d.PortfolioStatistics.TradeWinRate.IsZero() {
		t.Fatal("Trade_Win_Rate must be present (null) on the strategy path")
	}
}
