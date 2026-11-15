package engine

import (
	"context"
	"math"
	"strconv"
	"strings"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/schedule"
)

// holding은 buy&hold 시뮬레이션의 항목 하나(주식 또는 현금)의 계좌다. 주식 항목도 매수 대기 현금
// (휴장일 납입, 상장 전 납입)을 가진다.
type holding struct {
	asset     Asset
	key       string
	history   *marketdata.History
	cursor    int // history.Bars에서 오늘 이전 마지막 봉의 다음 위치
	planned   float64
	perPeriod float64
	plan      []civil.Date
	executed  int

	shares    float64
	cash      float64
	price     float64 // USD 평가 가격(직전 현지 종가 × 오늘 환율)
	hasPrice  bool
	tradeable bool // 오늘 실제 봉이 있다

	contributed float64
	profit      float64
	previous    float64
	returns     []float64
	trades      []Trade
	buySize     float64
	buyNotional float64
}

func (h *holding) value() float64 {
	if !h.hasPrice {
		return h.cash
	}
	return h.cash + h.shares*h.price
}

func (h *holding) trade(day civil.Date, size, commission, nativePrice float64) {
	if math.Abs(size) <= 1e-12 {
		return
	}
	typ := "BUY"
	if size < 0 {
		typ = "SELL"
	}
	h.trades = append(h.trades, Trade{
		EntryTime: day.String() + "T00:00:00", EntryPrice: h.price, Size: math.Abs(size),
		Commission: math.Abs(size) * h.price * commission, Type: typ,
		PriceCurrency: "USD", NativeCurrency: h.history.Currency, QuantityUnit: "fractional_adjusted_unit",
		EntryPriceNative: nativePrice,
	})
	if size > 0 {
		h.buySize += size
		h.buyNotional += size * h.price
	}
}

// buyHold는 요청 기간의 모든 달력일을 평가하는 일별 시뮬레이션이다.
//
//   - 납입: 시작일과 실제 예정일에만 한다(F04). 휴장일·상장 전 납입금은 현금으로 기다렸다가 다음 거래
//     가능일에 매수한다. 매수 예산 B, 수수료율 c이면 매수 금액은 B/(1+c)다(F02).
//   - 평가: 수량 × 직전 현지 종가 × 그날 환율 + 대기 현금. 휴장일 환율 변동도 반영한다(R).
//   - 리밸런싱: 예정일이 휴장이면 보류하고, 자금이 있는 모든 주식이 거래 가능한 다음 날 실행한다.
//     일부 시장만 열린 날의 부분 리밸런싱은 하지 않는다. 수수료는 실제 회전 금액 기준이고 원장과
//     같다(F06).
//   - 일간 수익률: 납입 전후를 나눈 시간가중 수익률(TWR). 최초 매수 수수료도 첫 수익률에 들어간다(S02).
func buyHold(ctx context.Context, req Request, data marketdata.Histories) (*Data, error) {
	var holdings []*holding
	var warnings []string
	for idx, a := range req.Portfolio {
		h := &holding{asset: a, key: a.ID(idx)}
		if !a.Cash() {
			hist, ok := data[a.Symbol]
			if !ok || len(hist.Bars) == 0 {
				warnings = append(warnings, "종목 "+a.Symbol+"의 가격 데이터를 불러오지 못해 백테스트에서 제외했습니다 (투자금 $"+
					groupThousands(a.Base())+"는 수익률 계산에 포함되지 않음).")
				continue
			}
			h.history = &hist
		}
		h.plan = []civil.Date{req.StartDate}
		if a.DCA() {
			h.plan = append(h.plan, schedule.Dates(req.StartDate, req.EndDate, a.DCAFrequency)...)
		}
		n := float64(len(h.plan))
		switch {
		case a.TotalAmount.set():
			h.planned = *a.TotalAmount.V
			h.perPeriod = math.Floor(h.planned*100/n) / 100 // 센트 단위 기본 회차, 마지막 회차가 잔액
		case a.Weight.set():
			h.planned = a.Base()
			h.perPeriod = h.planned / n
		default:
			h.planned = a.Base() * n
			h.perPeriod = a.Base()
		}
		holdings = append(holdings, h)
	}
	if len(holdings) == 0 {
		return nil, apperr.Validation("[ValidationError] 포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다.")
	}

	days := req.StartDate.DaysUntil(req.EndDate) + 1
	dates := make([]civil.Date, days)
	for i := range dates {
		dates[i] = req.StartDate.AddDays(i)
	}
	plannedTotal := 0.0
	for _, h := range holdings {
		plannedTotal += h.planned
	}
	c := req.Commission
	rebalanceDays := schedule.Dates(req.StartDate, req.EndDate, req.Rebalance())
	rebalanceIdx, rebalancePending := 0, false
	equity := make([]float64, 0, days)
	returns := make([]float64, 0, days)
	weights := make([]Ordered[any], 0, days)
	var rebalances []Rebalance
	tradeCount := 0
	previous := 0.0

	nh := len(holdings)
	before := make([]float64, nh)
	inflows := make([]float64, nh)
	transfers := make([]float64, nh)
	natives := make([]float64, nh)

	for _, day := range dates {
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		for i, h := range holdings {
			if h.asset.Cash() {
				continue
			}
			bars := h.history.Bars
			for h.cursor < len(bars) && bars[h.cursor].Date <= day {
				h.cursor++
			}
			h.tradeable = false
			if h.cursor > 0 {
				bar := bars[h.cursor-1]
				if bar.Close > 0 && !math.IsInf(bar.Close, 0) {
					rate, err := marketdata.RateOn(h.history.Currency, day, data)
					if err != nil {
						return nil, err
					}
					h.price, h.hasPrice = bar.Close*rate, true
					h.tradeable = bar.Date == day
					natives[i] = h.price / rate
				}
			}
		}
		preFlow := 0.0
		for i, h := range holdings {
			before[i] = h.value()
			preFlow += before[i]
			inflows[i], transfers[i] = 0, 0
		}
		for i, h := range holdings {
			h.profit += before[i] - h.previous
			for h.executed < len(h.plan) && h.plan[h.executed] <= day {
				amount := h.perPeriod
				if h.asset.TotalAmount.set() && h.executed+1 == len(h.plan) {
					amount = h.planned - h.contributed
				}
				h.cash += amount
				h.contributed += amount
				inflows[i] += amount
				h.executed++
			}
			if !h.asset.Cash() && h.tradeable && h.cash > 0 {
				size := h.cash / (h.price * (1 + c))
				h.shares += size
				h.cash = 0
				tradeCount++
				h.trade(day, size, c, natives[i])
			}
		}
		for rebalanceIdx < len(rebalanceDays) && rebalanceDays[rebalanceIdx] <= day {
			rebalancePending = len(equity) > 0
			rebalanceIdx++
		}
		if rebalancePending && nh > 1 && allFundedTradeable(holdings) {
			rebalancePending = false
			ev, n := rebalance(holdings, day, c, plannedTotal, transfers, natives)
			tradeCount += n
			if ev != nil {
				rebalances = append(rebalances, *ev)
			}
		}

		value, inflow := 0.0, 0.0
		for i, h := range holdings {
			value += h.value()
			inflow += inflows[i]
		}
		var daily float64
		switch {
		case previous > 0 && inflow > 0:
			daily = preFlow/previous*(value/(preFlow+inflow)) - 1
		case previous > 0:
			daily = (value - previous - inflow) / previous
		case inflow > 0:
			daily = value/inflow - 1
		}
		var row Ordered[any]
		row.Set("date", day)
		for i, h := range holdings {
			after := h.value()
			h.profit += after - before[i] - inflows[i] - transfers[i]
			var r float64
			switch {
			case h.previous > 0 && before[i]+inflows[i] > 0:
				r = before[i]/h.previous*((after-transfers[i])/(before[i]+inflows[i])) - 1
			case inflows[i] > 0:
				r = (after-transfers[i])/inflows[i] - 1
			}
			h.returns = append(h.returns, cleanReturn(r))
			h.previous = after
			if value > 0 {
				k := h.asset.Symbol
				if h.asset.Cash() {
					k = h.key
				}
				w, _ := row.Get(k)
				prev, _ := w.(float64)
				row.Set(k, prev+after/value)
			}
		}
		weights = append(weights, row)
		equity = append(equity, value)
		returns = append(returns, cleanReturn(daily))
		previous = value
	}

	contributed := 0.0
	for _, h := range holdings {
		contributed += h.contributed
	}
	if contributed <= 0 {
		return nil, apperr.Validation("기간 내에 실행된 투자가 없습니다.")
	}
	d := &Data{
		PortfolioStatistics:    statistics(dates, equity, returns, contributed, 1, tradeCount),
		RebalanceHistory:       rebalances,
		WeightHistory:          weights,
		Warnings:               warnings,
		CalculationAssumptions: assumptions,
	}
	if d.RebalanceHistory == nil {
		d.RebalanceHistory = []Rebalance{}
	}
	if d.Warnings == nil {
		d.Warnings = []string{}
	}
	for _, h := range holdings {
		var start, end *float64
		switch {
		case h.buySize > 0:
			start = ptr(h.buyNotional / h.buySize)
		case h.asset.Cash():
			start = ptr(1.0)
		}
		switch {
		case h.asset.Cash():
			end = ptr(1.0)
		case h.hasPrice:
			end = ptr(h.price)
		}
		var periods *int
		if h.asset.DCA() {
			periods = &h.executed
		}
		ret := 0.0
		if h.contributed > 0 {
			ret = h.profit / h.contributed * 100
		}
		item := HoldingReturn{
			AssetID: h.key, Symbol: h.asset.Symbol, Weight: h.contributed / contributed, Amount: h.contributed,
			Return: ret, StartPrice: start, EndPrice: end, InvestmentType: h.asset.InvestmentType,
			DCAPeriods: periods, FinalValue: h.value(), Trades: len(h.trades), SharpeRatio: sharpe(h.returns),
			AssetType: h.asset.AssetType,
		}
		d.IndividualReturns.Set(h.key, item)
		if !h.asset.Cash() {
			log := h.trades
			if log == nil {
				log = []Trade{}
			}
			d.StrategyDetails.Set(h.key, BuyHoldDetail{TradeLog: log})
		}
		d.IndividualResults = append(d.IndividualResults, IndividualResult{
			AssetID: h.key, AssetType: h.asset.AssetType, Ticker: h.asset.Symbol, FinalEquity: item.FinalValue,
			TotalReturnPct: item.Return, SharpeRatio: item.SharpeRatio, Weight: item.Weight, Amount: item.Amount,
			Trades: item.Trades,
		})
		d.PortfolioComposition = append(d.PortfolioComposition, Composition{
			AssetID: h.key, Symbol: h.asset.Symbol, Weight: item.Weight, Amount: item.Amount,
			InvestmentType: h.asset.InvestmentType, DCAPeriods: periods, AssetType: h.asset.AssetType,
		})
	}
	d.PortfolioResult = PortfolioResult{TotalEquity: d.PortfolioStatistics.FinalValue, TotalReturnPct: d.PortfolioStatistics.TotalReturn}
	for i, day := range dates {
		d.EquityCurve.Set(day.String(), equity[i])
		d.DailyReturns.Set(day.String(), returns[i]*100)
	}
	return d, nil
}

// allFundedTradeable: 자금이 배정된 모든 주식이 오늘 거래 가능하다.
func allFundedTradeable(hs []*holding) bool {
	for _, h := range hs {
		if !h.asset.Cash() && h.planned != 0 && !h.tradeable {
			return false
		}
	}
	return true
}

// rebalance는 목표 비중(계획 예산 비율)으로 맞춘다. 수수료는 실제 회전 금액 × 수수료율이며,
// 수수료 차감 후 총액 V가 V + fees(V) = V_before를 만족하도록 이분법으로 푼다(c < 0.1이라 단조).
// transfers에는 항목별 (목표 − 현재 + 수수료)를 기록해 개별 손익에서 내부 이동을 뺀다.
func rebalance(hs []*holding, day civil.Date, c, plannedTotal float64, transfers, natives []float64) (*Rebalance, int) {
	n := len(hs)
	current := make([]float64, n)
	eligible := make([]bool, n)
	total, allocated, targetSum := 0.0, 0.0, 0.0
	for i, h := range hs {
		current[i] = h.value()
		total += current[i]
		eligible[i] = h.asset.Cash() || h.tradeable
		if eligible[i] {
			allocated += current[i]
			targetSum += h.planned / plannedTotal
		}
	}
	if total <= 0 || targetSum <= 0 {
		return nil, 0
	}
	weights := make([]float64, n)
	for i, h := range hs {
		weights[i] = h.planned / plannedTotal / targetSum
	}
	lo, hi := 0.0, allocated
	for range 80 {
		mid := (lo + hi) / 2
		fees := 0.0
		for i, h := range hs {
			if eligible[i] && !h.asset.Cash() {
				fees += math.Abs(mid*weights[i]-current[i]) * c
			}
		}
		if mid+fees > allocated {
			hi = mid
		} else {
			lo = mid
		}
	}
	net := (lo + hi) / 2
	ev := Rebalance{Date: day}
	trades := 0
	for i, h := range hs {
		ev.WeightsBefore.Set(h.key, current[i]/total)
		if !eligible[i] {
			continue
		}
		target := net * weights[i]
		diff := target - current[i]
		fee := 0.0
		if !h.asset.Cash() {
			fee = math.Abs(diff) * c
		}
		ev.CommissionCost += fee
		transfers[i] = diff + fee
		if h.asset.Cash() {
			h.cash = target
			if math.Abs(diff) > 1e-9 {
				ev.Trades = append(ev.Trades, RebalanceTrade{AssetID: h.key, Symbol: h.asset.Symbol,
					Action: action(diff, "increase", "decrease"), Amount: ptr(math.Abs(diff)), Price: 1})
			}
			continue
		}
		shares := target / h.price
		size := shares - h.shares
		if math.Abs(size) > 1e-12 {
			trades++
			h.trade(day, size, c, natives[i])
			ev.Trades = append(ev.Trades, RebalanceTrade{AssetID: h.key, Symbol: h.asset.Symbol,
				Action: action(size, "buy", "sell"), Shares: ptr(math.Abs(size)), Price: h.price, Commission: fee})
		}
		h.shares = shares
	}
	afterTotal := 0.0
	for _, h := range hs {
		afterTotal += h.value()
	}
	for _, h := range hs {
		ev.WeightsAfter.Set(h.key, h.value()/afterTotal)
	}
	if len(ev.Trades) == 0 {
		return nil, trades
	}
	return &ev, trades
}

func action(v float64, pos, neg string) string {
	if v > 0 {
		return pos
	}
	return neg
}

func ptr[T any](v T) *T { return &v }

// groupThousands는 1234567.891 → "1,234,567.89".
func groupThousands(v float64) string {
	s := strconv.FormatFloat(v, 'f', 2, 64)
	neg := strings.HasPrefix(s, "-")
	s = strings.TrimPrefix(s, "-")
	whole, frac, _ := strings.Cut(s, ".")
	var b strings.Builder
	for i, ch := range whole {
		if i > 0 && (len(whole)-i)%3 == 0 {
			b.WriteByte(',')
		}
		b.WriteRune(ch)
	}
	out := b.String() + "." + frac
	if neg {
		return "-" + out
	}
	return out
}
