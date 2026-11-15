package engine

import (
	"context"
	"encoding/json"
	"math"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// reconcile은 계산 결과 하나의 회계 불변식을 검사한다(상대 오차 1e-7):
//   - 개별 최종 평가액의 합 = 포트폴리오 최종 평가액
//   - Total_Return = 최종 / 총 납입 − 1
//   - 원장의 수수료 = 체결 금액 × 수수료율
//   - 청산 거래의 PnL = 수량 × (청산 − 진입) − 수수료, 청산 봉 > 진입 봉(인과성)
//   - 일간 수익률의 기하 연결 = TWR
//   - 리밸런싱 이벤트의 수수료 합 = 이벤트 거래 수수료 합
func reconcile(t *testing.T, name string, req Request, d *Data) {
	t.Helper()
	s := d.PortfolioStatistics
	tol := func(x float64) float64 { return 1e-7 * math.Max(1, math.Abs(x)) }
	if !(s.FinalValue >= 0) || !(s.InitialValue > 0) {
		t.Errorf("%s: final %v initial %v", name, s.FinalValue, s.InitialValue)
	}
	sum := 0.0
	for _, r := range d.IndividualResults {
		sum += r.FinalEquity
	}
	if math.Abs(sum-s.FinalValue) > tol(s.FinalValue) {
		t.Errorf("%s: assets %v != total %v", name, sum, s.FinalValue)
	}
	if math.Abs(s.TotalReturn-(s.FinalValue/s.InitialValue-1)*100) > 1e-7 {
		t.Errorf("%s: total return", name)
	}
	growth := 1.0
	for _, k := range d.DailyReturns.Keys() {
		v, _ := d.DailyReturns.Get(k)
		growth *= 1 + v/100
	}
	if math.Abs((growth-1)*100-s.TimeWeightedReturn) > 1e-6*math.Max(1, math.Abs(s.TimeWeightedReturn)) {
		t.Errorf("%s: product of daily returns %v != TWR %v", name, (growth-1)*100, s.TimeWeightedReturn)
	}
	for _, key := range d.StrategyDetails.Keys() {
		v, _ := d.StrategyDetails.Get(key)
		raw, _ := json.Marshal(v)
		var detail struct {
			TradeLog []Trade `json:"trade_log"`
		}
		_ = json.Unmarshal(raw, &detail)
		for _, tr := range detail.TradeLog {
			exit := 0.0
			if tr.ExitPrice != nil {
				exit = *tr.ExitPrice
			}
			notional := tr.Size * (tr.EntryPrice + exit)
			if math.Abs(tr.Commission-notional*req.Commission) > tol(notional) {
				t.Errorf("%s %s: commission %v != %v", name, key, tr.Commission, notional*req.Commission)
			}
			if tr.ExitPrice != nil {
				if math.Abs(*tr.PnL-(tr.Size*(exit-tr.EntryPrice)-tr.Commission)) > tol(notional) {
					t.Errorf("%s %s: PnL identity", name, key)
				}
				if tr.EntryBar == nil || tr.ExitBar == nil || *tr.ExitBar <= *tr.EntryBar {
					t.Errorf("%s %s: exit must come after entry", name, key)
				}
			}
		}
	}
	for _, rb := range d.RebalanceHistory {
		fees := 0.0
		for _, tr := range rb.Trades {
			fees += tr.Commission
		}
		if math.Abs(fees-rb.CommissionCost) > tol(rb.CommissionCost) {
			t.Errorf("%s %s: rebalance fees %v != %v", name, rb.Date, fees, rb.CommissionCost)
		}
	}
}

type parityCase struct {
	Name    string          `json:"name"`
	Request json.RawMessage `json:"request"`
}

// rust-migration이 보존한 64개 입력(Python 시절 사례)을 그대로 돌려 불변식을 확인한다.
// 기대값(Python 출력)은 합격 기준이 아니다.
func TestParityInputsObeyInvariants(t *testing.T) {
	var data marketdata.Histories
	readJSON(t, "../../testdata/rust/histories.json", &data)
	var cases []parityCase
	readJSON(t, "../../testdata/rust/parity.json", &cases)
	if len(cases) != 64 {
		t.Fatalf("expected 64 cases, got %d", len(cases))
	}
	for _, c := range cases {
		req := decodeRequest(t, c.Request)
		d, err := Run(context.Background(), req, data, testLimits)
		if err != nil {
			t.Errorf("%s: %v", c.Name, err)
			continue
		}
		reconcile(t, c.Name, req, d)
	}
}

func TestRealMarketInputsObeyInvariants(t *testing.T) {
	var fixture struct {
		Histories marketdata.Histories `json:"histories"`
		Cases     []parityCase         `json:"cases"`
	}
	readJSON(t, "../../testdata/rust/real-market-python.json", &fixture)
	for _, c := range fixture.Cases {
		req := decodeRequest(t, c.Request)
		data := marketdata.Histories{}
		for sym, h := range fixture.Histories {
			var bars []marketdata.Bar
			for _, b := range h.Bars {
				if b.Date <= req.EndDate && (marketdata.IsFX(sym) || b.Date >= req.StartDate) {
					bars = append(bars, b)
				}
			}
			h.Bars = bars
			data[sym] = h
		}
		d, err := Run(context.Background(), req, data, testLimits)
		if err != nil {
			t.Errorf("%s: %v", c.Name, err)
			continue
		}
		reconcile(t, c.Name, req, d)
	}
}
