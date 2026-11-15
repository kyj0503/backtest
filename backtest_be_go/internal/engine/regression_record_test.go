package engine

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"math"
	"os"
	"strconv"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// Python(develop) 회귀 기록과의 비교. 합격 기준은 불변식(reconcile)이고, Python과의 차이는
// 아래 expectSame에 적은 "같아야 하는 값"만 검사한다. 나머지 차이는 로그로 남기고
// docs/go-migration.md의 지표 정의 변경표로 설명한다(go test -v -run Record).

type recordCase struct {
	Request   json.RawMessage `json:"request"`
	Histories map[string]struct {
		Currency string `json:"currency"`
		Bars     []struct {
			Date  civil.Date `json:"date"`
			Close float64    `json:"close"`
		} `json:"bars"`
	} `json:"histories"`
	FXRates map[string]map[string]float64 `json:"fx_rates"`
}

func (c recordCase) data(t *testing.T) marketdata.Histories {
	t.Helper()
	out := marketdata.Histories{}
	for sym, h := range c.Histories {
		mh := marketdata.History{Symbol: sym, Currency: h.Currency}
		for _, b := range h.Bars {
			mh.Bars = append(mh.Bars, marketdata.Bar{Date: b.Date, Open: b.Close, High: b.Close, Low: b.Close, Close: b.Close})
		}
		out[sym] = mh
	}
	// Python 테스트의 환율 표: KRW는 1 USD당 원, EUR는 1 EUR당 USD. 같은 방향의 티커로 옮긴다.
	for cur, table := range c.FXRates {
		ticker, _ := marketdata.FXTicker(cur)
		mh := marketdata.History{Symbol: ticker, Currency: cur}
		for day, rate := range table {
			mh.Bars = append(mh.Bars, marketdata.Bar{Date: civil.MustParse(day), Open: rate, High: rate, Low: rate, Close: rate})
		}
		sortBars(mh.Bars)
		out[ticker] = mh
	}
	return out
}

func sortBars(b []marketdata.Bar) {
	for i := 1; i < len(b); i++ {
		for j := i; j > 0 && b[j].Date < b[j-1].Date; j-- {
			b[j], b[j-1] = b[j-1], b[j]
		}
	}
}

func TestRecordPythonSnapshotScenarios(t *testing.T) {
	var inputs struct {
		Scenarios map[string]recordCase `json:"scenarios"`
	}
	readJSON(t, "../../testdata/python/snapshot/inputs.json", &inputs)
	var expected map[string]map[string]any
	readJSON(t, "../../testdata/python/snapshot/portfolio_manager_response_snapshot.json", &expected)

	// 수수료 0, 리밸런싱 없음, 일시 투자만 있는 시나리오는 정합성 수정과 무관하게 최종 평가액이 같아야 한다.
	expectSameFinal := map[string]bool{"buy_hold_cash_only": true, "buy_hold_failed_symbol": true}

	for name, c := range inputs.Scenarios {
		req := decodeRequest(t, c.Request)
		d, err := Run(context.Background(), req, c.data(t), testLimits)
		if err != nil {
			t.Errorf("%s: %v", name, err)
			continue
		}
		reconcile(t, name, req, d)
		py := obj(expected[name], "data", "portfolio_statistics").(map[string]any)
		s := d.PortfolioStatistics
		for _, f := range []struct {
			key string
			got float64
		}{
			{"Initial_Value", s.InitialValue}, {"Final_Value", s.FinalValue}, {"Total_Return", s.TotalReturn},
			{"Annual_Return", s.AnnualReturn}, {"Annual_Volatility", s.AnnualVolatility}, {"Sharpe_Ratio", s.SharpeRatio},
			{"Max_Drawdown", s.MaxDrawdown}, {"Win_Rate", s.WinRate},
		} {
			want, _ := py[f.key].(float64)
			t.Logf("%-26s %-18s go=%-22.12g python=%-22.12g diff=%.3g", name, f.key, f.got, want, f.got-want)
		}
		if expectSameFinal[name] {
			want := py["Final_Value"].(float64)
			if math.Abs(s.FinalValue-want) > 1e-6*math.Max(1, want) {
				t.Errorf("%s: final value %v != python %v (no fee/rebalance/DCA: must match)", name, s.FinalValue, want)
			}
		}
		if len(d.Warnings) != len(obj(expected[name], "data", "warnings").([]any)) {
			t.Errorf("%s: warnings %q", name, d.Warnings)
		}
	}
}

func TestRecordPythonGoldenMaster(t *testing.T) {
	var golden struct {
		Request json.RawMessage `json:"request"`
	}
	readJSON(t, "../../testdata/python/golden/request.json", &golden)
	req := decodeRequest(t, golden.Request)
	f, err := os.Open("../../testdata/python/golden/AAPL.csv")
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	rows, err := csv.NewReader(f).ReadAll()
	if err != nil {
		t.Fatal(err)
	}
	h := marketdata.History{Symbol: "AAPL", Currency: "USD"}
	for _, r := range rows[1:] {
		v := make([]float64, 4)
		for i := range v {
			v[i], _ = strconv.ParseFloat(r[i+1], 64)
		}
		adj, _ := strconv.ParseFloat(r[5], 64)
		ratio := adj / v[3]
		h.Bars = append(h.Bars, marketdata.Bar{Date: civil.MustParse(r[0]), Open: v[0] * ratio, High: v[1] * ratio,
			Low: v[2] * ratio, Close: adj})
	}
	d, err := Run(context.Background(), req, histories(h), testLimits)
	if err != nil {
		t.Fatal(err)
	}
	reconcile(t, "golden", req, d)
	var expected map[string]any
	readJSON(t, "../../testdata/python/golden/expected_dca_output.json", &expected)
	py := obj(expected, "data", "portfolio_statistics").(map[string]any)
	s := d.PortfolioStatistics
	// 납입 회차(9회)는 일정 정의가 같으므로 같아야 한다.
	if s.InitialValue != py["Initial_Value"].(float64) {
		t.Errorf("initial %v != python %v", s.InitialValue, py["Initial_Value"])
	}
	t.Logf("golden Final_Value go=%.10g python=%.10g, Total_Return go=%.6g python=%.6g, Total_Trades go=%d python=%v",
		s.FinalValue, py["Final_Value"], s.TotalReturn, py["Total_Return"], s.TotalTrades, py["Total_Trades"])
}
