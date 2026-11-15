package monitoring

import (
	"strings"
	"sync"

	"github.com/prometheus/client_golang/prometheus"
)

// App은 백테스트 업무 지표다. 이름·라벨·버킷은 Python app/monitoring/custom_metrics.py와 같다.
type App struct {
	Executions   *prometheus.CounterVec   // backtest_execution_total{strategy_type,status}
	Processing   *prometheus.HistogramVec // backtest_processing_seconds{strategy_type}
	Stages       *prometheus.HistogramVec // backtest_stage_duration_seconds{stage}
	Supplemental *prometheus.CounterVec   // backtest_supplemental_outcome_total{section,outcome}
	popularity   *prometheus.CounterVec   // ticker_popularity_total{ticker}
	tickers      *tickerLabels
}

// Stages는 stage 라벨의 고정 집합이다.
var Stages = map[string]bool{"simulation": true, "ticker_info": true, "price_history": true,
	"exchange_rates": true, "benchmarks": true, "news": true, "stock_data": true,
	"volatility_events": true, "supplemental_total": true}

var supplementalSections = map[string]bool{"ticker_info": true, "stock_data": true,
	"volatility_events": true, "exchange_rates": true, "benchmarks": true, "news": true}
var supplementalOutcomes = map[string]bool{"ok": true, "empty": true, "skipped": true, "timeout": true, "error": true}

// Gauges는 실행 슬롯 상태를 /metrics 수집 시점에 읽는 함수들이다.
type Gauges struct {
	BacktestRunning, BacktestWaiting, MarketRunning, MarketWaiting func() float64
}

func (r *Registry) NewApp(allowlist []string, g Gauges) *App {
	a := &App{
		Executions: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "backtest_execution_total", Help: "Total number of executed backtests",
		}, []string{"strategy_type", "status"}),
		Processing: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Name: "backtest_processing_seconds", Help: "Time spent processing backtest logic",
			Buckets: []float64{0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0},
		}, []string{"strategy_type"}),
		Stages: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Name: "backtest_stage_duration_seconds", Help: "Duration of each backtest request stage",
			Buckets: []float64{0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0},
		}, []string{"stage"}),
		Supplemental: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "backtest_supplemental_outcome_total",
			Help: "Outcome of each supplemental data section attached to a backtest response",
		}, []string{"section", "outcome"}),
		popularity: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "ticker_popularity_total", Help: "Total count of tickers included in backtests",
		}, []string{"ticker"}),
		tickers: newTickerLabels(allowlist, 30, 3, 500),
	}
	r.MustRegister(a.Executions, a.Processing, a.Stages, a.Supplemental, a.popularity,
		gauge("backtest_jobs_running", "Backtest jobs holding an execution slot", g.BacktestRunning),
		gauge("backtest_jobs_waiting", "Backtest requests waiting for an execution slot", g.BacktestWaiting),
		gauge("market_data_jobs_running", "Reference data reads holding a slot", g.MarketRunning),
		gauge("market_data_jobs_waiting", "Reference data reads waiting for a slot", g.MarketWaiting),
	)
	return a
}

func gauge(name, help string, f func() float64) prometheus.Collector {
	if f == nil {
		f = func() float64 { return 0 }
	}
	return prometheus.NewGaugeFunc(prometheus.GaugeOpts{Name: name, Help: help}, f)
}

func (a *App) ObserveStage(stage string, seconds float64) {
	if a != nil && Stages[stage] {
		a.Stages.WithLabelValues(stage).Observe(seconds)
	}
}

func (a *App) RecordSupplemental(section, outcome string) {
	if a != nil && supplementalSections[section] && supplementalOutcomes[outcome] {
		a.Supplemental.WithLabelValues(section, outcome).Inc()
	}
}

func (a *App) RecordTicker(ticker string) {
	if a != nil {
		a.popularity.WithLabelValues(a.tickers.label(ticker)).Inc()
	}
}

// tickerLabels는 티커를 라벨 값으로 바꾼다(Python TickerLabelPolicy). 허용 목록은 항상 자기 라벨,
// 나머지는 Space-Saving 후보 표에서 보장 횟수가 minCount 이상이면 동적 슬롯(최대 maxDynamic)에
// 올린다. 그 밖은 "other". 동적 라벨은 강등하지 않는다. 라벨 수 상한이 고정된다.
type tickerLabels struct {
	mu         sync.Mutex
	allow      map[string]bool
	promoted   map[string]bool
	counts     map[string]int
	errs       map[string]int
	maxDynamic int
	minCount   int
	capacity   int
}

func newTickerLabels(allowlist []string, maxDynamic, minCount, capacity int) *tickerLabels {
	t := &tickerLabels{allow: map[string]bool{}, promoted: map[string]bool{}, counts: map[string]int{},
		errs: map[string]int{}, maxDynamic: maxDynamic, minCount: minCount, capacity: capacity}
	for _, s := range allowlist {
		t.allow[strings.ToUpper(strings.TrimSpace(s))] = true
	}
	return t
}

func (t *tickerLabels) label(ticker string) string {
	ticker = strings.ToUpper(strings.TrimSpace(ticker))
	if ticker == "" {
		return "other"
	}
	if t.allow[ticker] {
		return ticker
	}
	t.mu.Lock()
	defer t.mu.Unlock()
	if t.promoted[ticker] {
		return ticker
	}
	if _, ok := t.counts[ticker]; ok {
		t.counts[ticker]++
	} else if len(t.counts) < t.capacity {
		t.counts[ticker], t.errs[ticker] = 1, 0
	} else {
		var victim string
		floor := -1
		for k, c := range t.counts {
			if floor < 0 || c < floor {
				victim, floor = k, c
			}
		}
		delete(t.counts, victim)
		delete(t.errs, victim)
		t.counts[ticker], t.errs[ticker] = floor+1, floor
	}
	if t.counts[ticker]-t.errs[ticker] >= t.minCount && len(t.promoted) < t.maxDynamic {
		t.promoted[ticker] = true
		return ticker
	}
	return "other"
}
