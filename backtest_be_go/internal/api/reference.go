package api

import (
	"context"
	"encoding/json"
	"errors"
	"math"
	"sort"
	"sync"
	"time"

	"golang.org/x/sync/errgroup"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/engine"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/news"
)

// 참고 데이터 섹션. 계산 결과와 독립이며, 각 섹션은 시간 예산 안에서 따로 성공·실패한다.
// 외부(Yahoo·네이버) 장애가 계산 결과를 막거나 실패시키지 않는다(A-08).

// sectionFields는 섹션이 채우는 응답 키, sectionStatuses는 supplemental_status 키다.
var (
	sectionFields = map[string][]string{
		"prices":         {"ticker_info", "stock_data", "volatility_events"},
		"exchange-rates": {"exchange_rates", "exchange_stats"},
		"benchmarks":     {"sp500_benchmark", "nasdaq_benchmark"},
		"news":           {"latest_news"},
	}
	sectionStatuses = map[string][]string{
		"prices":         {"ticker_info", "stock_data", "volatility_events"},
		"exchange-rates": {"exchange_rates"},
		"benchmarks":     {"benchmarks"},
		"news":           {"news"},
	}
	statusOrder = []string{"ticker_info", "stock_data", "volatility_events", "exchange_rates", "benchmarks", "news"}
)

// emptyValue는 섹션 실패·생략 시 키별 빈 값이다(Python과 같은 모양: 목록 또는 객체).
func emptyValue(key string) any {
	switch key {
	case "exchange_rates", "sp500_benchmark", "nasdaq_benchmark":
		return []any{}
	}
	return map[string]any{}
}

// sectionResult는 한 섹션의 결과다.
type sectionResult struct {
	Fields map[string]any
	Status map[string]string
	// SP500TotalReturn은 benchmarks 섹션의 S&P 500 기간 수익률(%)이다. 계산할 수 없으면 nil.
	SP500TotalReturn *float64
}

func emptySection(section, outcome string) sectionResult {
	r := sectionResult{Fields: map[string]any{}, Status: map[string]string{}}
	for _, k := range sectionFields[section] {
		r.Fields[k] = emptyValue(k)
	}
	for _, k := range sectionStatuses[section] {
		r.Status[k] = outcome
	}
	return r
}

// reference는 섹션 하나를 예산 안에서 모은다. 시간 초과는 "timeout", 그 밖의 실패는 "error"다.
func (s *Service) reference(ctx context.Context, section string, q readQuery) sectionResult {
	began := time.Now()
	ctx, cancel := context.WithTimeout(ctx, s.Cfg.SupplementalDataBudget)
	defer cancel()
	r, err := s.collect(ctx, section, q)
	if err != nil {
		outcome := "error"
		if errors.Is(err, context.DeadlineExceeded) || errors.Is(ctx.Err(), context.DeadlineExceeded) {
			outcome = "timeout"
		}
		s.Log.Warn("reference section failed", "section", section, "outcome", outcome, "error", err)
		r = emptySection(section, outcome)
	}
	for _, stage := range sectionStatuses[section] {
		if stage == "benchmarks" || stage == "news" || stage == "exchange_rates" {
			s.App.ObserveStage(stage, time.Since(began).Seconds())
		}
	}
	if section == "prices" {
		s.App.ObserveStage("price_history", time.Since(began).Seconds())
	}
	return r
}

type tickerInfo struct {
	Symbol         string      `json:"symbol"`
	Currency       string      `json:"currency"`
	CompanyName    string      `json:"company_name"`
	Exchange       string      `json:"exchange"`
	FirstTradeDate *civil.Date `json:"first_trade_date"`
}

type pricePoint struct {
	Date   civil.Date `json:"date"`
	Price  float64    `json:"price"`
	Volume float64    `json:"volume"`
}

type volatilityEvent struct {
	Date        civil.Date `json:"date"`
	DailyReturn float64    `json:"daily_return"`
	ClosePrice  float64    `json:"close_price"`
	Volume      float64    `json:"volume"`
	EventType   string     `json:"event_type"`
}

type ratePoint struct {
	Date civil.Date `json:"date"`
	Rate float64    `json:"rate"`
}

type benchmarkPoint struct {
	Date      civil.Date `json:"date"`
	Close     float64    `json:"close"`
	ReturnPct float64    `json:"return_pct"`
}

func info(h marketdata.History) tickerInfo {
	return tickerInfo{Symbol: h.Symbol, Currency: h.Currency, CompanyName: firstNonEmpty(h.CompanyName, h.Symbol),
		Exchange: h.Exchange, FirstTradeDate: h.FirstTradeDate}
}

func firstNonEmpty(v ...string) string {
	for _, s := range v {
		if s != "" {
			return s
		}
	}
	return ""
}

func ok(nonEmpty bool) string {
	if nonEmpty {
		return "ok"
	}
	return "empty"
}

func (s *Service) collect(ctx context.Context, section string, q readQuery) (sectionResult, error) {
	r := sectionResult{Fields: map[string]any{}, Status: map[string]string{}}
	switch section {
	case "prices":
		infos := engine.Ordered[any]{}
		prices := engine.Ordered[any]{}
		events := engine.Ordered[any]{}
		histories := make([]marketdata.History, len(q.Symbols))
		g, gctx := errgroup.WithContext(ctx)
		g.SetLimit(4)
		for i, sym := range q.Symbols {
			g.Go(func() error {
				h, err := s.Source.History(gctx, sym, q.Start, q.End)
				histories[i] = h
				return err
			})
		}
		if err := g.Wait(); err != nil {
			return r, err
		}
		hasPrices, hasEvents := false, false
		for _, h := range histories {
			infos.Set(h.Symbol, info(h))
			pts := make([]pricePoint, len(h.Bars))
			for i, b := range h.Bars {
				pts[i] = pricePoint{Date: b.Date, Price: b.Close, Volume: b.Volume}
			}
			prices.Set(h.Symbol, pts)
			hasPrices = hasPrices || len(pts) > 0
			ev := volatility(h.Bars, s.Cfg.VolatilityThresholdPct)
			events.Set(h.Symbol, ev)
			hasEvents = hasEvents || len(ev) > 0
		}
		r.Fields["ticker_info"], r.Fields["stock_data"], r.Fields["volatility_events"] = infos, prices, events
		r.Status["ticker_info"], r.Status["stock_data"], r.Status["volatility_events"] = ok(infos.Len() > 0), ok(hasPrices), ok(hasEvents)
	case "exchange-rates":
		h, err := s.Source.History(ctx, s.Cfg.ExchangeRateTicker, q.Start, q.End)
		if err != nil {
			return r, err
		}
		pts := make([]ratePoint, len(h.Bars))
		for i, b := range h.Bars {
			pts[i] = ratePoint{Date: b.Date, Rate: b.Close}
		}
		stats := map[string]any{}
		if len(pts) > 0 {
			hi, lo := pts[0], pts[0]
			for _, p := range pts {
				if p.Rate > hi.Rate {
					hi = p
				}
				if p.Rate < lo.Rate {
					lo = p
				}
			}
			stats = map[string]any{"start_point": pts[0], "end_point": pts[len(pts)-1], "high_point": hi, "low_point": lo}
		}
		r.Fields["exchange_rates"], r.Fields["exchange_stats"] = pts, orderedStats(stats)
		r.Status["exchange_rates"] = ok(len(pts) > 0)
	case "benchmarks":
		var sp, nq marketdata.History
		g, gctx := errgroup.WithContext(ctx)
		g.Go(func() (err error) { sp, err = s.Source.History(gctx, "^GSPC", q.Start, q.End); return })
		g.Go(func() (err error) { nq, err = s.Source.History(gctx, "^IXIC", q.Start, q.End); return })
		if err := g.Wait(); err != nil {
			return r, err
		}
		r.Fields["sp500_benchmark"], r.Fields["nasdaq_benchmark"] = benchmark(sp, q.Start, q.End), benchmark(nq, q.Start, q.End)
		if len(sp.Bars) >= 2 {
			v := (sp.Bars[len(sp.Bars)-1].Close/sp.Bars[0].Close - 1) * 100
			r.SP500TotalReturn = &v
		}
		r.Status["benchmarks"] = ok(len(sp.Bars) > 0 || len(nq.Bars) > 0)
	case "news":
		latest := engine.Ordered[any]{}
		results := make([][]news.Item, len(q.Symbols))
		g, gctx := errgroup.WithContext(ctx)
		g.SetLimit(4)
		for i, sym := range q.Symbols {
			g.Go(func() (err error) { results[i], err = s.News.Latest(gctx, sym, q.Limit); return })
		}
		if err := g.Wait(); err != nil {
			return r, err
		}
		any := false
		for i, sym := range q.Symbols {
			latest.Set(sym, results[i])
			any = any || len(results[i]) > 0
		}
		r.Fields["latest_news"] = latest
		r.Status["news"] = ok(any)
	}
	return r, nil
}

func orderedStats(m map[string]any) any {
	if len(m) == 0 {
		return map[string]any{}
	}
	var o engine.Ordered[any]
	for _, k := range []string{"start_point", "end_point", "high_point", "low_point"} {
		o.Set(k, m[k])
	}
	return o
}

// volatility는 일간 변동률 절댓값이 threshold% 이상인 날이다. 최근 10건, 최신순.
func volatility(bars []marketdata.Bar, threshold float64) []volatilityEvent {
	out := []volatilityEvent{}
	for i := len(bars) - 1; i >= 1 && len(out) < 10; i-- {
		r := (bars[i].Close/bars[i-1].Close - 1) * 100
		if math.Abs(r) < threshold {
			continue
		}
		typ := "급락"
		if r > 0 {
			typ = "급등"
		}
		out = append(out, volatilityEvent{Date: bars[i].Date, DailyReturn: r, ClosePrice: bars[i].Close, Volume: bars[i].Volume, EventType: typ})
	}
	return out
}

// benchmark는 요청 기간의 모든 달력일 지수 값(직전 종가 유지)과 전일 대비 수익률이다.
func benchmark(h marketdata.History, start, end civil.Date) []benchmarkPoint {
	out := []benchmarkPoint{}
	if len(h.Bars) == 0 {
		return out
	}
	idx, prev := 0, h.Bars[0].Close
	for d := start; d <= end; d = d.AddDays(1) {
		for idx+1 < len(h.Bars) && h.Bars[idx+1].Date <= d {
			idx++
		}
		c := h.Bars[idx].Close
		out = append(out, benchmarkPoint{Date: d, Close: c, ReturnPct: (c/prev - 1) * 100})
		prev = c
	}
	return out
}

// supplemental은 POST include_*에 따라 섹션을 병렬로 모아 응답 키로 만든다. 끈 섹션은 "skipped"다.
func (s *Service) supplemental(ctx context.Context, req engine.Request, d *engine.Data, loaded marketdata.Histories) {
	began := time.Now()
	var symbols []string
	for _, a := range req.Portfolio {
		if !a.Cash() && !contains(symbols, a.Symbol) {
			symbols = append(symbols, a.Symbol)
		}
	}
	sort.Strings(symbols)
	q := readQuery{Symbols: symbols, Start: req.StartDate, End: req.EndDate, Limit: 15}
	enabled := map[string]bool{
		"prices":         len(symbols) > 0 && (req.IncludeStockData || req.IncludeVolatilityEvents),
		"exchange-rates": req.IncludeExchangeRates,
		"benchmarks":     req.IncludeBenchmarks,
		"news":           req.IncludeNews && len(symbols) > 0,
	}
	fields := map[string]any{}
	status := map[string]string{}
	for _, section := range []string{"prices", "exchange-rates", "benchmarks", "news"} {
		e := emptySection(section, "skipped")
		for k, v := range e.Fields {
			fields[k] = v
		}
		for k, v := range e.Status {
			status[k] = v
		}
	}
	// 계산에 쓴 시세로 종목 정보를 채운다(prices 섹션을 끈 경우에도 정확한 통화·이름을 준다).
	infos := engine.Ordered[any]{}
	for _, sym := range symbols {
		if h, ok := loaded[sym]; ok {
			infos.Set(sym, info(h))
		}
	}
	fields["ticker_info"] = infos

	var mu sync.Mutex
	var wg sync.WaitGroup
	var sp500 *float64
	for section, on := range enabled {
		if !on {
			continue
		}
		wg.Add(1)
		go func() {
			defer wg.Done()
			r := s.reference(ctx, section, q)
			mu.Lock()
			defer mu.Unlock()
			for k, v := range r.Fields {
				fields[k] = v
			}
			for k, v := range r.Status {
				status[k] = v
			}
			if section == "benchmarks" {
				sp500 = r.SP500TotalReturn
			}
		}()
	}
	wg.Wait()
	if !req.IncludeStockData {
		fields["stock_data"], status["stock_data"] = map[string]any{}, "skipped"
	}
	if !req.IncludeVolatilityEvents {
		fields["volatility_events"], status["volatility_events"] = map[string]any{}, "skipped"
	}
	if sp500 != nil {
		d.PortfolioStatistics.SP500TotalReturnPct = engine.Some(*sp500)
		d.PortfolioStatistics.AlphaVsSP500Pct = engine.Some(d.PortfolioStatistics.TimeWeightedReturn - *sp500)
	}
	var st engine.Ordered[string]
	for _, k := range statusOrder {
		st.Set(k, status[k])
		s.App.RecordSupplemental(k, status[k])
	}
	fields["supplemental_status"] = st
	d.Supplemental = map[string]json.RawMessage{}
	for k, v := range fields {
		raw, err := marshal(v)
		if err != nil {
			s.Log.Error("supplemental encoding failed", "key", k, "error", err)
			raw = []byte("null")
		}
		d.Supplemental[k] = raw
	}
	s.App.ObserveStage("supplemental_total", time.Since(began).Seconds())
}
