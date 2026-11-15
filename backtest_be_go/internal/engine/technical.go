package engine

import (
	"context"
	"math"
	"sort"
	"strconv"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/strategy"
)

// StrategyStats는 기술 전략 경로의 strategy_details 항목이다(종목별 상세 지표와 거래 원장).
type StrategyStats struct {
	InitialCash          float64          `json:"initial_cash"`
	FinalEquity          float64          `json:"final_equity"`
	TotalReturnPct       float64          `json:"total_return_pct"`
	AnnualizedReturnPct  float64          `json:"annualized_return_pct"`
	CAGRPct              float64          `json:"cagr_pct"`
	BuyAndHoldReturnPct  float64          `json:"buy_and_hold_return_pct"`
	VolatilityPct        float64          `json:"volatility_pct"`
	SharpeRatio          float64          `json:"sharpe_ratio"`
	SortinoRatio         float64          `json:"sortino_ratio"`
	CalmarRatio          float64          `json:"calmar_ratio"`
	MaxDrawdownPct       float64          `json:"max_drawdown_pct"`
	AvgDrawdownPct       float64          `json:"avg_drawdown_pct"`
	TotalTrades          int              `json:"total_trades"`
	WinRatePct           float64          `json:"win_rate_pct"`
	ProfitFactor         *float64         `json:"profit_factor"`
	AvgTradePct          float64          `json:"avg_trade_pct"`
	BestTradePct         float64          `json:"best_trade_pct"`
	WorstTradePct        float64          `json:"worst_trade_pct"`
	SQN                  float64          `json:"sqn"`
	AlphaPct             *float64         `json:"alpha_pct"`
	Beta                 *float64         `json:"beta"`
	KellyCriterion       *float64         `json:"kelly_criterion"`
	TradeLog             []Ordered[any]   `json:"trade_log"`
	OpenPositions        []Ordered[any]   `json:"open_positions"`
	Cash                 float64          `json:"cash"`
	EquityCurve          Ordered[float64] `json:"equity_curve"`
	Ticker               string           `json:"ticker"`
	Strategy             string           `json:"strategy"`
	StartDate            civil.Date       `json:"start_date"`
	EndDate              civil.Date       `json:"end_date"`
	DurationDays         int              `json:"duration_days"`
	ExecutionTimeSeconds float64          `json:"execution_time_seconds"`
	Timestamp            string           `json:"timestamp"`
}

// CashStats는 기술 전략 경로에서 현금 항목의 strategy_details다.
type CashStats struct {
	TotalTrades    int     `json:"total_trades"`
	WinRatePct     float64 `json:"win_rate_pct"`
	MaxDrawdownPct float64 `json:"max_drawdown_pct"`
	SharpeRatio    float64 `json:"sharpe_ratio"`
	FinalEquity    float64 `json:"final_equity"`
}

type techAsset struct {
	key    string
	asset  Asset
	amount float64
	equity []float64 // nil이면 기간 내내 amount (현금)
}

// technical은 종목별로 전략을 돌리고 평가액을 더한다. 리밸런싱·적립은 없다(검증에서 거부).
func technical(ctx context.Context, req Request, data marketdata.Histories) (*Data, error) {
	days := req.StartDate.DaysUntil(req.EndDate) + 1
	dates := make([]civil.Date, days)
	for i := range dates {
		dates[i] = req.StartDate.AddDays(i)
	}
	d := &Data{CalculationAssumptions: assumptions, RebalanceHistory: []Rebalance{}, Warnings: []string{}}
	var assets []techAsset
	wins, trades := 0, 0
	var realized []float64
	for idx, a := range req.Portfolio {
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		amount := a.Base()
		if amount <= 0 {
			d.Warnings = append(d.Warnings, "종목 "+a.Symbol+" 백테스트 실패: 투자금액은 0보다 커야 합니다.")
			continue
		}
		key := a.ID(idx)
		if a.Cash() {
			d.StrategyDetails.Set(key, CashStats{FinalEquity: amount})
			d.IndividualReturns.Set(key, StrategyReturn{AssetID: key, AssetType: a.AssetType, Symbol: a.Symbol,
				Amount: amount, InitialValue: amount, FinalValue: amount})
			assets = append(assets, techAsset{key: key, asset: a, amount: amount})
			continue
		}
		h, ok := data[a.Symbol]
		if !ok {
			d.Warnings = append(d.Warnings, "종목 "+a.Symbol+" 백테스트 실패: 가격 데이터가 없습니다.")
			continue
		}
		began := time.Now()
		stats, out, err := runStrategy(ctx, req, h, data, dates, amount)
		if err != nil {
			return nil, err
		}
		stats.ExecutionTimeSeconds = time.Since(began).Seconds()
		for _, t := range out.Trades {
			realized = append(realized, t.PnL)
			if t.PnL > 0 {
				wins++
			}
		}
		n := len(out.Trades)
		trades += n
		var winRate *float64
		if n > 0 {
			winRate = ptr(float64(stats.WinRatePct))
		}
		d.StrategyDetails.Set(key, stats)
		d.IndividualReturns.Set(key, StrategyReturn{AssetID: key, AssetType: a.AssetType, Symbol: a.Symbol,
			Amount: amount, Return: (stats.FinalEquity/amount - 1) * 100, InitialValue: amount,
			FinalValue: stats.FinalEquity, Trades: n, WinRate: winRate})
		assets = append(assets, techAsset{key: key, asset: a, amount: amount, equity: out.Equity})
	}
	total := 0.0
	for _, a := range assets {
		total += a.amount
	}
	if total <= 0 {
		return nil, apperr.Validation("모든 종목의 백테스트가 실패했습니다.")
	}

	equity := make([]float64, days)
	d.WeightHistory = make([]Ordered[any], days)
	values := make([]float64, len(assets))
	for i, day := range dates {
		sum := 0.0
		for k, a := range assets {
			values[k] = a.amount
			if a.equity != nil {
				values[k] = a.equity[i]
			}
			sum += values[k]
		}
		equity[i] = sum
		row := newOrdered[any](len(assets) + 1)
		row.Set("date", day)
		for k, a := range assets {
			w := 0.0
			if sum > 0 {
				w = values[k] / sum
			}
			row.Set(a.key, w)
		}
		d.WeightHistory[i] = row
	}
	returns := dailyReturns(equity)
	s := statistics(dates, equity, returns, total, equity[0]/total, trades)
	duration := req.StartDate.DaysUntil(req.EndDate)
	s.AnnualReturn = math.Pow(equity[days-1]/total, 365.25/float64(duration))*100 - 100
	if trades > 0 {
		s.TradeWinRate = Some(float64(wins) / float64(trades) * 100)
	} else {
		s.TradeWinRate = Null()
	}
	s.ProfitFactor = OptionalOf(profitFactor(realized))
	d.PortfolioStatistics = s
	d.PortfolioResult = PortfolioResult{TotalEquity: s.FinalValue, TotalReturnPct: s.TotalReturn}

	for _, a := range assets {
		v, _ := d.IndividualReturns.Get(a.key)
		item := v.(StrategyReturn)
		item.Weight = a.amount / total
		d.IndividualReturns.Set(a.key, item)
		sharpeRatio := 0.0
		if v, _ := d.StrategyDetails.Get(a.key); v != nil {
			if st, ok := v.(StrategyStats); ok {
				sharpeRatio = st.SharpeRatio
			}
		}
		d.IndividualResults = append(d.IndividualResults, IndividualResult{
			AssetID: a.key, AssetType: a.asset.AssetType, Ticker: a.asset.Symbol, FinalEquity: item.FinalValue,
			TotalReturnPct: item.Return, SharpeRatio: sharpeRatio, Weight: item.Weight, Amount: item.Amount,
			Trades: item.Trades, WinRate: item.WinRate,
		})
		d.PortfolioComposition = append(d.PortfolioComposition, Composition{
			AssetID: a.key, Symbol: a.asset.Symbol, Weight: item.Weight, Amount: item.Amount, AssetType: a.asset.AssetType,
		})
	}
	d.EquityCurve, d.DailyReturns = curves(dates, equity, returns)
	return d, nil
}

// runStrategy는 한 종목의 전략을 돌리고 상세 지표를 만든다. 신호·체결은 USD 환산 거래일 봉으로,
// 평가는 모든 달력일의 (직전 현지 종가 × 그날 환율)로 한다(R).
func runStrategy(ctx context.Context, req Request, h marketdata.History, data marketdata.Histories,
	dates []civil.Date, amount float64) (StrategyStats, *strategy.Output, error) {
	var bars []marketdata.Bar
	for _, b := range h.Bars {
		if b.Date < req.StartDate || b.Date > req.EndDate {
			continue
		}
		rate, err := marketdata.RateOn(h.Currency, b.Date, data)
		if err != nil {
			return StrategyStats{}, nil, err
		}
		b.Open, b.High, b.Low, b.Close = b.Open*rate, b.High*rate, b.Low*rate, b.Close*rate
		bars = append(bars, b)
	}
	valuations := make([]strategy.Valuation, len(dates))
	for i, day := range dates {
		j := sort.Search(len(h.Bars), func(k int) bool { return h.Bars[k].Date > day })
		price := 0.0
		if j > 0 {
			rate, err := marketdata.RateOn(h.Currency, day, data)
			if err != nil {
				return StrategyStats{}, nil, err
			}
			price = h.Bars[j-1].Close * rate
		}
		valuations[i] = strategy.Valuation{Date: day, Price: price}
	}
	out, err := strategy.Run(ctx, req.Strategy, req.StrategyParams, bars, valuations, amount, req.Commission)
	if err != nil {
		return StrategyStats{}, nil, err
	}

	eq := out.Equity
	last := len(eq) - 1
	finalPrice := valuations[last].Price
	headline := statistics(dates, eq, dailyReturns(eq), amount, 1, len(out.Trades))
	for _, v := range []float64{headline.AnnualReturn, headline.AnnualVolatility} {
		if math.IsNaN(v) || math.IsInf(v, 0) {
			return StrategyStats{}, nil, apperr.Validation("계산 결과가 표현 가능한 범위를 벗어났습니다.")
		}
	}
	annual := headline.AnnualReturn / 100
	calRet := dailyReturns(eq)
	down := 0.0
	for _, r := range calRet {
		down += math.Min(r, 0) * math.Min(r, 0)
	}
	downside := math.Sqrt(down/float64(len(calRet))) * math.Sqrt(daysPerYear)

	var pnl, rets []float64
	wins := 0
	for _, t := range out.Trades {
		pnl = append(pnl, t.PnL)
		rets = append(rets, t.Return)
		if t.PnL > 0 {
			wins++
		}
	}
	n := len(out.Trades)
	st := StrategyStats{
		InitialCash: amount, FinalEquity: eq[last], TotalReturnPct: (eq[last]/amount - 1) * 100,
		AnnualizedReturnPct: annual * 100, CAGRPct: annual * 100,
		BuyAndHoldReturnPct: (finalPrice/out.FirstClose - 1) * 100,
		VolatilityPct:       headline.AnnualVolatility, SharpeRatio: headline.SharpeRatio,
		MaxDrawdownPct: headline.MaxDrawdown, AvgDrawdownPct: -mean(drawdownPeaks(eq)) * 100,
		TotalTrades: n, ProfitFactor: profitFactor(pnl), Cash: out.Cash,
		Ticker: h.Symbol, Strategy: req.Strategy, StartDate: req.StartDate, EndDate: req.EndDate,
		DurationDays: req.StartDate.DaysUntil(req.EndDate),
		Timestamp:    time.Now().UTC().Format(time.RFC3339Nano),
	}
	if downside > 0 {
		st.SortinoRatio = annual / downside
	}
	if headline.MaxDrawdown < 0 {
		st.CalmarRatio = annual / (-headline.MaxDrawdown / 100)
	}
	if n > 0 {
		st.WinRatePct = float64(wins) / float64(n) * 100
		g := 1.0
		best, worst := math.Inf(-1), math.Inf(1)
		for _, r := range rets {
			g *= 1 + r
			best, worst = math.Max(best, r), math.Min(worst, r)
		}
		st.AvgTradePct = (math.Pow(g, 1/float64(n)) - 1) * 100
		st.BestTradePct, st.WorstTradePct = best*100, worst*100
	}
	if sd := stddev(pnl); sd > 0 {
		st.SQN = math.Sqrt(float64(n)) * mean(pnl) / sd
	}
	st.EquityCurve = Ordered[float64]{keys: dateKeys(dates), vals: eq}

	native := func(usd float64, day civil.Date) (float64, error) {
		rate, err := marketdata.RateOn(h.Currency, day, data)
		if err != nil {
			return 0, err
		}
		return usd / rate, nil
	}
	st.TradeLog = make([]Ordered[any], 0, n)
	for _, t := range out.Trades {
		var row Ordered[any]
		row.Set("Size", t.Size)
		row.Set("EntryBar", t.EntryBar)
		row.Set("ExitBar", t.ExitBar)
		row.Set("EntryPrice", t.EntryPrice)
		row.Set("ExitPrice", t.ExitPrice)
		row.Set("SL", 0.0)
		row.Set("TP", 0.0)
		row.Set("PnL", t.PnL)
		row.Set("Commission", t.EntryFee+t.ExitFee)
		row.Set("ReturnPct", t.Return)
		row.Set("EntryTime", t.EntryDate.String()+"T00:00:00")
		row.Set("ExitTime", t.ExitDate.String()+"T00:00:00")
		row.Set("Duration", "P"+strconv.Itoa(t.EntryDate.DaysUntil(t.ExitDate))+"DT0H0M0S")
		row.Set("Tag", 0.0)
		for _, side := range []struct {
			prefix string
			bar    int
		}{{"Entry", t.EntryBar}, {"Exit", t.ExitBar}} {
			for _, ind := range out.Indicators {
				row.Set(side.prefix+"_"+ind.Name, nanToNil(ind.Values[side.bar]))
			}
		}
		row.Set("PriceCurrency", "USD")
		row.Set("NativeCurrency", h.Currency)
		row.Set("QuantityUnit", "fractional_adjusted_unit")
		entryNative, err := native(t.EntryPrice, t.EntryDate)
		if err != nil {
			return StrategyStats{}, nil, err
		}
		exitNative, err := native(t.ExitPrice, t.ExitDate)
		if err != nil {
			return StrategyStats{}, nil, err
		}
		row.Set("EntryPriceNative", entryNative)
		row.Set("ExitPriceNative", exitNative)
		st.TradeLog = append(st.TradeLog, row)
	}
	st.OpenPositions = []Ordered[any]{}
	if p := out.Open; p != nil {
		var row Ordered[any]
		row.Set("EntryTime", p.EntryDate.String())
		row.Set("EntryPrice", p.EntryPrice)
		row.Set("Size", p.Size)
		row.Set("Commission", p.Fee)
		row.Set("MarketPrice", finalPrice)
		row.Set("MarketValue", p.Size*finalPrice)
		row.Set("PriceCurrency", "USD")
		row.Set("NativeCurrency", h.Currency)
		row.Set("QuantityUnit", "fractional_adjusted_unit")
		entryNative, err := native(p.EntryPrice, p.EntryDate)
		if err != nil {
			return StrategyStats{}, nil, err
		}
		row.Set("EntryPriceNative", entryNative)
		st.OpenPositions = append(st.OpenPositions, row)
	}
	return st, out, nil
}

// drawdownPeaks는 고점 회복 구간별 최대 낙폭(비율)이다. 회복 구간이 없으면 0 초과 낙폭 전부다.
func drawdownPeaks(equity []float64) []float64 {
	peak := equity[0]
	dd := make([]float64, len(equity))
	var recoveries []int
	for i, v := range equity {
		peak = math.Max(peak, v)
		dd[i] = 1 - v/peak
		if dd[i] == 0 || i == len(equity)-1 {
			recoveries = append(recoveries, i)
		}
	}
	var peaks []float64
	for k := 1; k < len(recoveries); k++ {
		a, b := recoveries[k-1], recoveries[k]
		if b > a+1 {
			m := 0.0
			for _, x := range dd[a : b+1] {
				m = math.Max(m, x)
			}
			peaks = append(peaks, m)
		}
	}
	if len(peaks) == 0 {
		for _, x := range dd {
			if x > 0 {
				peaks = append(peaks, x)
			}
		}
	}
	return peaks
}

func nanToNil(v float64) *float64 {
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return nil
	}
	return &v
}
