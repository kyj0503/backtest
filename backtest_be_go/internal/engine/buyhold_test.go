package engine

import (
	"context"
	"errors"
	"math"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// 독립 원장 기대값(손으로 계산한 값)만 쓴다. Python 출력은 쓰지 않는다.

// F02: 매수 예산 B, 수수료 c이면 매수 금액은 B/(1+c)다.
func TestBuyFeeIsOnTopOfNotional(t *testing.T) {
	d := run(t, request(t, `{"commission":0.01}`, 40), series("TEST", flat(40, 100), nil))
	near(t, "final", d.PortfolioStatistics.FinalValue, 10000/1.01)
	tr := detail(d, "TEST").TradeLog[0]
	near(t, "commission", tr.Commission, tr.Size*100*0.01)
	near(t, "notional+fee", tr.Size*100+tr.Commission, 10000)
}

// F04: 현금 적립은 예정일에만 늘어난다(첫날부터 미래 납입액을 보유하지 않는다).
func TestCashDepositsOnScheduleOnly(t *testing.T) {
	d := run(t, request(t, `{"portfolio":[{"symbol":"RESERVE","amount":500,"asset_type":"cash","investment_type":"dca","dca_frequency":"weekly_1"}]}`, 40))
	v, _ := d.EquityCurve.Get("2023-01-02")
	near(t, "day 1", v, 500)
	near(t, "final", d.PortfolioStatistics.FinalValue, 3000) // 1/2, 1/9, 1/16, 1/23, 1/30, 2/6
}

// total_amount: 센트 단위 기본 회차 + 마지막 회차 잔액으로 총예산을 보존한다.
func TestTotalAmountRemainderOnLastInstallment(t *testing.T) {
	d := run(t, request(t, `{"portfolio":[{"symbol":"TEST","amount":333.33,"total_amount":1000,"investment_type":"dca","dca_frequency":"monthly_1"}]}`, 70),
		series("TEST", flat(70, 100), nil))
	near(t, "initial", d.PortfolioStatistics.InitialValue, 1000)
	near(t, "final", d.PortfolioStatistics.FinalValue, 1000)
	log := detail(d, "TEST").TradeLog
	near(t, "last installment", log[len(log)-1].Size*100, 333.34)
}

// F06: 리밸런싱 수수료는 실제 회전 금액 기준이고 원장 거래와 같다.
func TestRebalanceUsesActualTurnoverAndOneLedger(t *testing.T) {
	prices := make([]float64, 40)
	for i := range prices {
		prices[i] = 100
		if i >= 7 {
			prices[i] = 200
		}
	}
	d := run(t, request(t, `{"portfolio":[{"symbol":"TEST","amount":1000},{"symbol":"RESERVE","amount":1000,"asset_type":"cash"}],"commission":0.01,"rebalance_frequency":"weekly_1"}`, 40),
		series("TEST", prices, nil))
	rb := d.RebalanceHistory[0]
	var event RebalanceTrade
	for _, tr := range rb.Trades {
		if tr.Symbol == "TEST" {
			event = tr
		}
	}
	var sell Trade
	for _, tr := range detail(d, "TEST").TradeLog {
		if tr.Type == "SELL" {
			sell = tr
		}
	}
	near(t, "shares", *event.Shares, sell.Size)
	near(t, "fee", rb.CommissionCost, sell.Size*200*0.01)
	stock := 1000 / 1.01 * 2
	v, _ := d.EquityCurve.Get("2023-01-09")
	near(t, "after rebalance", v, 2*(stock+1000-0.01*stock)/1.99)
}

// F07: 현금 항목 이름이 CASH 티커와 같아도 덮어쓰지 않는다.
func TestCashIdentifierCannotOverwriteAStock(t *testing.T) {
	p := flat(40, 100)
	p[39] = 200
	d := run(t, request(t, `{"portfolio":[{"symbol":"RESERVE","amount":1000,"asset_type":"cash"},{"symbol":"CASH","amount":2000}]}`, 40),
		series("CASH", p, nil))
	cash, _ := d.IndividualReturns.Get("CASH")
	reserve, _ := d.IndividualReturns.Get("RESERVE__cash_1")
	near(t, "stock", cash.(HoldingReturn).FinalValue, 4000)
	near(t, "cash", reserve.(HoldingReturn).FinalValue, 1000)
	if len(d.IndividualResults) != 2 {
		t.Fatal(len(d.IndividualResults))
	}
}

// F10: 가격이 그대로인 적립식에서 부동소수점 잡음으로 상승·하락일을 세지 않는다.
func TestFlatDCAHasNoFakeUpOrDownDays(t *testing.T) {
	d := run(t, request(t, `{"portfolio":[{"symbol":"TEST","amount":999.99,"investment_type":"dca","dca_frequency":"weekly_1"}]}`, 100),
		series("TEST", flat(100, 7), nil))
	s := d.PortfolioStatistics
	if s.PositiveDays != 0 || s.NegativeDays != 0 {
		t.Fatalf("positive %d negative %d", s.PositiveDays, s.NegativeDays)
	}
	if s.ProfitFactor.v != nil {
		t.Fatal("profit factor must be null on the buy&hold path")
	}
}

// F11: 납입 기준 총수익률과 TWR을 구분한다.
func TestTotalReturnVersusTimeWeighted(t *testing.T) {
	p := make([]float64, 40)
	for i := range p {
		p[i] = 100
		if i >= 35 {
			p[i] = 200
		}
	}
	d := run(t, request(t, `{"portfolio":[{"symbol":"TEST","amount":1000,"investment_type":"dca","dca_frequency":"monthly_1"}]}`, 40),
		series("TEST", p, nil))
	near(t, "total return", d.PortfolioStatistics.TotalReturn, 50)
	near(t, "TWR", d.PortfolioStatistics.TimeWeightedReturn, 100)
}

// S02: 최초 매수 수수료는 첫 일간 수익률에 한 번 들어가고, 일간 수익률의 곱이 TWR과 같다.
func TestFirstFeeInReturnsExactlyOnce(t *testing.T) {
	d := run(t, request(t, `{"commission":0.01}`, 40), series("TEST", flat(40, 100), nil))
	loss := 1/1.01 - 1
	first, _ := d.DailyReturns.Get("2023-01-02")
	near(t, "first return", first, loss*100)
	growth := 1.0
	for _, k := range d.DailyReturns.Keys() {
		v, _ := d.DailyReturns.Get(k)
		growth *= 1 + v/100
	}
	near(t, "growth", growth, 1/1.01)
	s := d.PortfolioStatistics
	near(t, "TWR", s.TimeWeightedReturn, loss*100)
	near(t, "MDD", s.MaxDrawdown, loss*100)
	near(t, "volatility", s.AnnualVolatility, math.Abs(loss)*math.Sqrt(365.0/40)*100)
	if s.NegativeDays != 1 {
		t.Fatal(s.NegativeDays)
	}
}

// S02: 주말 납입 후 월요일 매수 수수료가 납입금을 이중으로 세지 않는다.
func TestWeekendInflowThenFee(t *testing.T) {
	req := request(t, `{"commission":0.01,"start_date":"2023-01-01"}`, 40)
	d := run(t, req, series("TEST", flat(40, 100), nil))
	sun, _ := d.DailyReturns.Get("2023-01-01")
	mon, _ := d.DailyReturns.Get("2023-01-02")
	near(t, "sunday", sun, 0)
	near(t, "monday", mon, (1/1.01-1)*100)
	near(t, "final", d.PortfolioStatistics.FinalValue, 10000/1.01)
}

// S05: 매수 대기 현금과 늦게 상장한 종목도 계정 비중에 포함된다.
func TestWaitingCashKeepsAccountWeights(t *testing.T) {
	late := series("LATE", flat(40, 100), nil)
	late.Bars = late.Bars[10:]
	req := request(t, `{"start_date":"2023-01-01","portfolio":[{"symbol":"TEST","amount":5000},{"symbol":"LATE","amount":5000}]}`, 40)
	d := run(t, req, series("TEST", flat(40, 100), nil), late)
	for _, row := range d.WeightHistory {
		sum := 0.0
		for _, k := range row.Keys() {
			if k == "date" {
				continue
			}
			w, _ := row.Get(k)
			sum += w.(float64)
			near(t, k, w.(float64), 0.5)
		}
		near(t, "sum", sum, 1)
	}
	if d.CalculationAssumptions.WeightBasis != "asset_account_including_uninvested_cash" {
		t.Fatal(d.CalculationAssumptions)
	}
}

// R: 환율은 매일 평가에 반영하고 체결 가격의 원통화 값을 남긴다.
func TestDailyFXRevaluation(t *testing.T) {
	stock := series("TEST", flat(40, 130000), nil)
	stock.Currency = "KRW"
	rates := make([]float64, 40)
	for i := range rates {
		rates[i] = 1300
		if i >= 20 {
			rates[i] = 2600
		}
	}
	d := run(t, request(t, `{"portfolio":[{"symbol":"TEST","amount":1000}]}`, 40), stock, series("KRW=X", rates, nil))
	near(t, "final", d.PortfolioStatistics.FinalValue, 500)
	tr := detail(d, "TEST").TradeLog[0]
	near(t, "native", tr.EntryPriceNative, 130000)
	near(t, "usd", tr.EntryPrice, 100)
	if tr.NativeCurrency != "KRW" || tr.PriceCurrency != "USD" || tr.QuantityUnit != "fractional_adjusted_unit" {
		t.Fatalf("%+v", tr)
	}
}

// R: 리밸런싱 예정일이 휴장이면 대상 주식이 모두 거래 가능한 다음 날까지 미룬다.
func TestRebalanceWaitsForAllMarkets(t *testing.T) {
	a := series("AAA", flat(40, 100), nil)
	b := series("BBB", flat(40, 100), nil)
	// BBB는 1/9(월)~1/11 휴장
	b.Bars = append(append([]marketdata.Bar{}, b.Bars[:7]...), b.Bars[10:]...)
	for i := range a.Bars {
		if i >= 3 {
			a.Bars[i].Open, a.Bars[i].Close, a.Bars[i].High, a.Bars[i].Low = 200, 200, 200, 200
		}
	}
	req := request(t, `{"portfolio":[{"symbol":"AAA","amount":1000},{"symbol":"BBB","amount":1000}],"rebalance_frequency":"weekly_1"}`, 40)
	d := run(t, req, a, b)
	if len(d.RebalanceHistory) == 0 || d.RebalanceHistory[0].Date.String() != "2023-01-12" {
		t.Fatalf("first rebalance %v", d.RebalanceHistory)
	}
}

func TestMissingSymbolBecomesWarning(t *testing.T) {
	req := request(t, `{"portfolio":[{"symbol":"TEST","amount":1000},{"symbol":"ZZZZ","amount":1234567.891}]}`, 40)
	d := run(t, req, series("TEST", flat(40, 100), nil))
	if len(d.Warnings) != 1 || d.Warnings[0] != "종목 ZZZZ의 가격 데이터를 불러오지 못해 백테스트에서 제외했습니다 (투자금 $1,234,567.89는 수익률 계산에 포함되지 않음)." {
		t.Fatalf("%q", d.Warnings)
	}
	if code := runErr(t, request(t, `{"portfolio":[{"symbol":"ZZZZ","amount":1}]}`, 40)); code != 422 {
		t.Fatal(code)
	}
}

// T02: 엔진도 불가능한 체결 봉을 거부한다(제공업체 어댑터를 거치지 않아도).
func TestImpossibleBarsAreRejected(t *testing.T) {
	for _, bad := range [][4]float64{{1, 100, 80, 100}, {100, 100, 100, 0}, {100, 90, 80, 100}, {100, 120, 110, 100}} {
		h := series("TEST", flat(40, 100), nil)
		h.Bars[20].Open, h.Bars[20].High, h.Bars[20].Low, h.Bars[20].Close = bad[0], bad[1], bad[2], bad[3]
		if code := runErr(t, request(t, "", 40), h); code != 422 {
			t.Errorf("%v: %d", bad, code)
		}
	}
}

// T02: 환산용 환율은 종가만 본다. 환율 티커를 거래하면 전체 OHLC 검사를 한다.
func TestFXPointRateIsNotATradableBar(t *testing.T) {
	stock := series("TEST", flat(40, 100), nil)
	stock.Currency = "KRW"
	fx := series("KRW=X", flat(40, 1000), nil)
	for i := range fx.Bars {
		fx.Bars[i].High, fx.Bars[i].Low = 1010, 1005
	}
	d := run(t, request(t, "", 40), stock, fx)
	near(t, "final", d.PortfolioStatistics.FinalValue, 10000)
	traded := request(t, `{"portfolio":[{"symbol":"KRW=X","amount":10000}]}`, 40)
	if code := runErr(t, traded, stock, fx); code != 422 {
		t.Fatal(code)
	}
	fx.Bars[0].Close = 0
	if code := runErr(t, request(t, "", 40), stock, fx); code != 422 {
		t.Fatal(code)
	}
}

func TestCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := Run(ctx, request(t, "", 40), histories(series("TEST", flat(40, 100), nil)), testLimits)
	if !errors.Is(err, context.Canceled) {
		t.Fatal(err)
	}
}

func TestOverflowIsRejected(t *testing.T) {
	req := request(t, `{"portfolio":[{"symbol":"A","amount":1e308},{"symbol":"B","amount":1e308}]}`, 40)
	if err := req.Validate(testLimits); apperr.Status(err) != 422 {
		t.Fatal(err)
	}
}

func TestGroupThousands(t *testing.T) {
	for in, want := range map[float64]string{0: "0.00", 999.5: "999.50", 1000: "1,000.00", 1234567.891: "1,234,567.89", -12345: "-12,345.00"} {
		if got := groupThousands(in); got != want {
			t.Errorf("%v: %s", in, got)
		}
	}
}
