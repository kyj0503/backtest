package engine

import (
	"bytes"
	"encoding/json"
	"errors"
	"math"
	"strconv"
	"unicode/utf8"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// 계산 응답 전용 JSON 인코더.
//
// encoding/json은 MarshalJSON 결과를 중첩 단계마다 다시 파싱·재포맷하고, 값마다 Encoder를 만들면
// 할당이 폭증한다. 프로파일에서 응답 직렬화가 CPU의 58%·할당의 70%를 차지했다(엔진 계산은 8%).
// 이 인코더는 바이트를 바로 이어 붙인다. 출력은 encoding/json(SetEscapeHTML(false))과 바이트 단위로
// 같아야 한다: 숫자 형식(f/e 규칙)과 문자열 이스케이프를 표준 인코더와 비교하는 테스트가 있고,
// 64개 사례 전체 응답의 바이트 비교 도구(encode_golden_test.go)로 확인했다.

var errNonFinite = errors.New("json: unsupported value: non-finite float")

type jw struct {
	b   []byte
	err error
}

// appender는 빠른 인코더로 자신을 쓸 수 있는 타입이다.
type appender interface{ appendJSON(w *jw) }

func (w *jw) byte(c byte)  { w.b = append(w.b, c) }
func (w *jw) raw(s string) { w.b = append(w.b, s...) }
func (w *jw) null()        { w.b = append(w.b, "null"...) }
func (w *jw) int(n int)    { w.b = strconv.AppendInt(w.b, int64(n), 10) }
func (w *jw) date(d civil.Date) {
	w.b = append(w.b, '"')
	w.b = d.AppendFormat(w.b)
	w.b = append(w.b, '"')
}

// float는 encoding/json과 같은 형식이다: |f|가 1e-6 미만(0 제외)이거나 1e21 이상이면 지수 표기,
// 지수가 한 자리면 0을 뺀다(e-07 → e-7).
func (w *jw) float(f float64) {
	if math.IsNaN(f) || math.IsInf(f, 0) {
		if w.err == nil {
			w.err = errNonFinite
		}
		w.null()
		return
	}
	abs := math.Abs(f)
	format := byte('f')
	if abs != 0 && (abs < 1e-6 || abs >= 1e21) {
		format = 'e'
	}
	w.b = strconv.AppendFloat(w.b, f, format, -1, 64)
	if format == 'e' {
		n := len(w.b)
		if n >= 4 && w.b[n-4] == 'e' && w.b[n-3] == '-' && w.b[n-2] == '0' {
			w.b[n-2] = w.b[n-1]
			w.b = w.b[:n-1]
		}
	}
}

func (w *jw) floatPtr(f *float64) {
	if f == nil {
		w.null()
		return
	}
	w.float(*f)
}

const hexDigits = "0123456789abcdef"

// str는 HTML 이스케이프 없는 encoding/json 문자열 규칙이다.
func (w *jw) str(s string) {
	w.b = append(w.b, '"')
	start := 0
	for i := 0; i < len(s); {
		c := s[i]
		if c < utf8.RuneSelf {
			if c >= 0x20 && c != '"' && c != '\\' {
				i++
				continue
			}
			w.b = append(w.b, s[start:i]...)
			switch c {
			case '"', '\\':
				w.b = append(w.b, '\\', c)
			case '\b':
				w.b = append(w.b, '\\', 'b')
			case '\f':
				w.b = append(w.b, '\\', 'f')
			case '\n':
				w.b = append(w.b, '\\', 'n')
			case '\r':
				w.b = append(w.b, '\\', 'r')
			case '\t':
				w.b = append(w.b, '\\', 't')
			default:
				w.b = append(w.b, '\\', 'u', '0', '0', hexDigits[c>>4], hexDigits[c&0xf])
			}
			i++
			start = i
			continue
		}
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError && size == 1 {
			w.b = append(w.b, s[start:i]...)
			w.b = append(w.b, `�`...)
			i += size
			start = i
			continue
		}
		if r == ' ' || r == ' ' {
			w.b = append(w.b, s[start:i]...)
			w.b = append(w.b, '\\', 'u', '2', '0', '2', hexDigits[r&0xf])
			i += size
			start = i
			continue
		}
		i += size
	}
	w.b = append(w.b, s[start:]...)
	w.b = append(w.b, '"')
}

// obj는 객체 필드를 쓰는 도우미다. 첫 필드 앞에는 쉼표를 쓰지 않는다.
type objw struct {
	w     *jw
	first bool
}

func (w *jw) obj() objw { w.byte(0x7b); return objw{w: w, first: true} }

func (o *objw) key(k string) {
	if !o.first {
		o.w.byte(',')
	}
	o.first = false
	o.w.byte('"')
	o.w.raw(k) // 정적 키는 이스케이프가 필요 없는 ASCII다
	o.w.raw(`":`)
}

func (o *objw) dynKey(k string) {
	if !o.first {
		o.w.byte(',')
	}
	o.first = false
	o.w.str(k)
	o.w.byte(':')
}

func (o *objw) end() { o.w.byte('}') }

func (o *objw) str(k, v string)           { o.key(k); o.w.str(v) }
func (o *objw) float(k string, v float64) { o.key(k); o.w.float(v) }
func (o *objw) int(k string, v int)       { o.key(k); o.w.int(v) }
func (o *objw) floatPtr(k string, v *float64) {
	o.key(k)
	o.w.floatPtr(v)
}
func (o *objw) val(k string, v any) { o.key(k); o.w.value(v) }

// value는 응답에 나오는 값을 쓴다. 모르는 타입은 encoding/json으로 넘긴다(드문 경로).
func (w *jw) value(v any) {
	switch x := v.(type) {
	case nil:
		w.null()
	case appender:
		x.appendJSON(w)
	case string:
		w.str(x)
	case float64:
		w.float(x)
	case int:
		w.int(x)
	case bool:
		if x {
			w.raw("true")
		} else {
			w.raw("false")
		}
	case civil.Date:
		w.date(x)
	case *float64:
		w.floatPtr(x)
	case *int:
		if x == nil {
			w.null()
		} else {
			w.int(*x)
		}
	case *string:
		if x == nil {
			w.null()
		} else {
			w.str(*x)
		}
	case []string:
		if x == nil {
			w.null()
			return
		}
		w.byte('[')
		for i, s := range x {
			if i > 0 {
				w.byte(',')
			}
			w.str(s)
		}
		w.byte(']')
	case json.RawMessage:
		if x == nil {
			w.null()
		} else {
			w.b = append(w.b, x...)
		}
	default:
		b, err := marshalNoEscape(v)
		if err != nil {
			if w.err == nil {
				w.err = err
			}
			w.null()
			return
		}
		w.b = append(w.b, b...)
	}
}

func list[T any](w *jw, xs []T, each func(T)) {
	if xs == nil {
		w.null()
		return
	}
	w.byte('[')
	for i, x := range xs {
		if i > 0 {
			w.byte(',')
		}
		each(x)
	}
	w.byte(']')
}

func encode(a appender) ([]byte, error) {
	w := &jw{b: make([]byte, 0, 4096)}
	a.appendJSON(w)
	return w.b, w.err
}

// AppendJSON은 응답을 b 뒤에 붙인다(api.writeJSON이 쓴다).
func (r Response) AppendJSON(b []byte) ([]byte, error) {
	w := &jw{b: b}
	r.appendJSON(w)
	return w.b, w.err
}

func (r Response) MarshalJSON() ([]byte, error) { return encode(r) }

func (r Response) appendJSON(w *jw) {
	o := w.obj()
	o.str("status", r.Status)
	o.key("data")
	if r.Data == nil {
		w.null()
	} else {
		r.Data.appendJSON(w)
	}
	o.end()
}

func (d Data) MarshalJSON() ([]byte, error) { return encode(d) }

func (d Data) appendJSON(w *jw) {
	o := w.obj()
	o.key("portfolio_statistics")
	d.PortfolioStatistics.appendJSON(w)
	o.val("individual_returns", d.IndividualReturns)
	o.key("individual_results")
	list(w, d.IndividualResults, func(x IndividualResult) { x.appendJSON(w) })
	o.key("portfolio_result")
	d.PortfolioResult.appendJSON(w)
	o.key("portfolio_composition")
	list(w, d.PortfolioComposition, func(x Composition) { x.appendJSON(w) })
	o.val("equity_curve", d.EquityCurve)
	o.val("daily_returns", d.DailyReturns)
	o.val("strategy_details", d.StrategyDetails)
	o.key("rebalance_history")
	list(w, d.RebalanceHistory, func(x Rebalance) { x.appendJSON(w) })
	o.key("weight_history")
	list(w, d.WeightHistory, func(x Ordered[any]) { x.appendJSON(w) })
	o.val("warnings", d.Warnings)
	o.key("calculation_assumptions")
	d.CalculationAssumptions.appendJSON(w)
	for _, k := range SupplementalKeys {
		if v, ok := d.Supplemental[k]; ok {
			o.key(k)
			w.b = append(w.b, bytes.TrimSpace(v)...)
		}
	}
	o.end()
}

func (o Ordered[V]) MarshalJSON() ([]byte, error) { return encode(o) }

func (o Ordered[V]) appendJSON(w *jw) {
	ob := w.obj()
	for i, k := range o.keys {
		ob.dynKey(k)
		switch v := any(o.vals[i]).(type) {
		case float64:
			w.float(v)
		default:
			w.value(v)
		}
	}
	ob.end()
}

func (s Statistics) appendJSON(w *jw) {
	o := w.obj()
	o.key("Start")
	w.date(s.Start)
	o.key("End")
	w.date(s.End)
	o.str("Duration", s.Duration)
	o.float("Initial_Value", s.InitialValue)
	o.float("Final_Value", s.FinalValue)
	o.float("Peak_Value", s.PeakValue)
	o.float("Total_Return", s.TotalReturn)
	o.float("Annual_Return", s.AnnualReturn)
	o.float("Time_Weighted_Return", s.TimeWeightedReturn)
	o.float("Annual_Volatility", s.AnnualVolatility)
	o.int("Return_Observation_Days_Per_Year", s.ReturnObservationDaysPerYear)
	o.str("Annualization_Basis", s.AnnualizationBasis)
	o.float("Sharpe_Ratio", s.SharpeRatio)
	o.float("Max_Drawdown", s.MaxDrawdown)
	o.float("Avg_Drawdown", s.AvgDrawdown)
	o.int("Max_Consecutive_Gains", s.MaxConsecutiveGains)
	o.int("Max_Consecutive_Losses", s.MaxConsecutiveLosses)
	o.int("Total_Trading_Days", s.TotalTradingDays)
	o.int("Total_Trades", s.TotalTrades)
	o.int("Positive_Days", s.PositiveDays)
	o.int("Negative_Days", s.NegativeDays)
	o.float("Win_Rate", s.WinRate)
	if !s.TradeWinRate.IsZero() {
		o.floatPtr("Trade_Win_Rate", s.TradeWinRate.v)
	}
	o.floatPtr("Profit_Factor", s.ProfitFactor.v)
	if !s.SP500TotalReturnPct.IsZero() {
		o.floatPtr("sp500_total_return_pct", s.SP500TotalReturnPct.v)
	}
	if !s.AlphaVsSP500Pct.IsZero() {
		o.floatPtr("alpha_vs_sp500_pct", s.AlphaVsSP500Pct.v)
	}
	o.end()
}

func (r PortfolioResult) appendJSON(w *jw) {
	o := w.obj()
	o.float("total_equity", r.TotalEquity)
	o.float("total_return_pct", r.TotalReturnPct)
	o.end()
}

func (c CalculationAssumptions) appendJSON(w *jw) {
	o := w.obj()
	o.str("quantity_unit", c.QuantityUnit)
	o.str("account_currency", c.AccountCurrency)
	o.str("weight_basis", c.WeightBasis)
	o.str("price_basis", c.PriceBasis)
	o.end()
}

func (h HoldingReturn) appendJSON(w *jw) {
	o := w.obj()
	o.str("asset_id", h.AssetID)
	o.str("symbol", h.Symbol)
	o.float("weight", h.Weight)
	o.float("amount", h.Amount)
	o.float("return", h.Return)
	o.floatPtr("start_price", h.StartPrice)
	o.floatPtr("end_price", h.EndPrice)
	o.str("investment_type", h.InvestmentType)
	o.val("dca_periods", h.DCAPeriods)
	o.float("final_value", h.FinalValue)
	o.int("trades", h.Trades)
	o.float("sharpe_ratio", h.SharpeRatio)
	o.str("asset_type", h.AssetType)
	o.end()
}

func (s StrategyReturn) appendJSON(w *jw) {
	o := w.obj()
	o.str("asset_id", s.AssetID)
	o.str("asset_type", s.AssetType)
	o.str("symbol", s.Symbol)
	o.float("weight", s.Weight)
	o.float("amount", s.Amount)
	o.float("return", s.Return)
	o.float("initial_value", s.InitialValue)
	o.float("final_value", s.FinalValue)
	o.int("trades", s.Trades)
	o.floatPtr("win_rate", s.WinRate)
	o.end()
}

func (r IndividualResult) appendJSON(w *jw) {
	o := w.obj()
	o.str("asset_id", r.AssetID)
	o.str("asset_type", r.AssetType)
	o.str("ticker", r.Ticker)
	o.float("final_equity", r.FinalEquity)
	o.float("total_return_pct", r.TotalReturnPct)
	o.float("sharpe_ratio", r.SharpeRatio)
	o.float("weight", r.Weight)
	o.float("amount", r.Amount)
	o.int("trades", r.Trades)
	o.floatPtr("win_rate", r.WinRate)
	o.end()
}

func (c Composition) appendJSON(w *jw) {
	o := w.obj()
	o.str("asset_id", c.AssetID)
	o.str("symbol", c.Symbol)
	o.float("weight", c.Weight)
	o.float("amount", c.Amount)
	if c.buyHold {
		o.str("investment_type", c.InvestmentType)
		o.val("dca_periods", c.DCAPeriods)
	}
	o.str("asset_type", c.AssetType)
	o.end()
}

func (t Trade) appendJSON(w *jw) {
	o := w.obj()
	if t.EntryBar != nil {
		o.int("EntryBar", *t.EntryBar)
	}
	if t.ExitBar != nil {
		o.int("ExitBar", *t.ExitBar)
	}
	o.str("EntryTime", t.EntryTime)
	o.float("EntryPrice", t.EntryPrice)
	o.float("Size", t.Size)
	o.float("Commission", t.Commission)
	if t.Type != "" {
		o.str("Type", t.Type)
	}
	o.val("ExitTime", t.ExitTime)
	o.floatPtr("ExitPrice", t.ExitPrice)
	o.floatPtr("PnL", t.PnL)
	o.floatPtr("ReturnPct", t.ReturnPct)
	o.val("Duration", t.Duration)
	o.str("PriceCurrency", t.PriceCurrency)
	o.str("NativeCurrency", t.NativeCurrency)
	o.str("QuantityUnit", t.QuantityUnit)
	o.float("EntryPriceNative", t.EntryPriceNative)
	if t.ExitPriceNative != nil {
		o.float("ExitPriceNative", *t.ExitPriceNative)
	}
	o.end()
}

func (d BuyHoldDetail) appendJSON(w *jw) {
	o := w.obj()
	o.key("trade_log")
	list(w, d.TradeLog, func(t Trade) { t.appendJSON(w) })
	o.key("open_positions")
	list(w, d.OpenPositions, func(t Trade) { t.appendJSON(w) })
	o.end()
}

func (r Rebalance) appendJSON(w *jw) {
	o := w.obj()
	o.key("date")
	w.date(r.Date)
	o.key("trades")
	list(w, r.Trades, func(t RebalanceTrade) { t.appendJSON(w) })
	o.val("weights_before", r.WeightsBefore)
	o.val("weights_after", r.WeightsAfter)
	o.float("commission_cost", r.CommissionCost)
	o.end()
}

func (t RebalanceTrade) appendJSON(w *jw) {
	o := w.obj()
	o.str("asset_id", t.AssetID)
	o.str("symbol", t.Symbol)
	o.str("action", t.Action)
	if t.Shares != nil {
		o.float("shares", *t.Shares)
	}
	if t.Amount != nil {
		o.float("amount", *t.Amount)
	}
	o.float("price", t.Price)
	o.float("commission", t.Commission)
	o.end()
}

func (c CashStats) appendJSON(w *jw) {
	o := w.obj()
	o.int("total_trades", c.TotalTrades)
	o.float("win_rate_pct", c.WinRatePct)
	o.float("max_drawdown_pct", c.MaxDrawdownPct)
	o.float("sharpe_ratio", c.SharpeRatio)
	o.float("final_equity", c.FinalEquity)
	o.end()
}

func (s StrategyStats) appendJSON(w *jw) {
	o := w.obj()
	o.float("initial_cash", s.InitialCash)
	o.float("final_equity", s.FinalEquity)
	o.float("total_return_pct", s.TotalReturnPct)
	o.float("annualized_return_pct", s.AnnualizedReturnPct)
	o.float("cagr_pct", s.CAGRPct)
	o.float("buy_and_hold_return_pct", s.BuyAndHoldReturnPct)
	o.float("volatility_pct", s.VolatilityPct)
	o.float("sharpe_ratio", s.SharpeRatio)
	o.float("sortino_ratio", s.SortinoRatio)
	o.float("calmar_ratio", s.CalmarRatio)
	o.float("max_drawdown_pct", s.MaxDrawdownPct)
	o.float("avg_drawdown_pct", s.AvgDrawdownPct)
	o.int("total_trades", s.TotalTrades)
	o.float("win_rate_pct", s.WinRatePct)
	o.floatPtr("profit_factor", s.ProfitFactor)
	o.float("avg_trade_pct", s.AvgTradePct)
	o.float("best_trade_pct", s.BestTradePct)
	o.float("worst_trade_pct", s.WorstTradePct)
	o.float("sqn", s.SQN)
	o.floatPtr("alpha_pct", s.AlphaPct)
	o.floatPtr("beta", s.Beta)
	o.floatPtr("kelly_criterion", s.KellyCriterion)
	o.key("trade_log")
	list(w, s.TradeLog, func(x Ordered[any]) { x.appendJSON(w) })
	o.key("open_positions")
	list(w, s.OpenPositions, func(x Ordered[any]) { x.appendJSON(w) })
	o.float("cash", s.Cash)
	o.val("equity_curve", s.EquityCurve)
	o.str("ticker", s.Ticker)
	o.str("strategy", s.Strategy)
	o.key("start_date")
	w.date(s.StartDate)
	o.key("end_date")
	w.date(s.EndDate)
	o.int("duration_days", s.DurationDays)
	o.float("execution_time_seconds", s.ExecutionTimeSeconds)
	o.str("timestamp", s.Timestamp)
	o.end()
}

func (op Optional) appendJSON(w *jw) { w.floatPtr(op.v) }
