package engine

import (
	"bytes"
	"encoding/json"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Ordered는 키 삽입 순서를 지키는 JSON 객체다(Go map은 키를 정렬해 출력한다).
//
// 값은 슬라이스에 둔다. 일별 평가액처럼 키가 수천 개이고 새 키만 붙는 곡선은 Append로 중복 검사 없이
// 쌓는다. Set은 같은 키를 덮어쓰며, 키가 적으면 선형 탐색하고 많아지면 색인을 만든다.
type Ordered[V any] struct {
	keys  []string
	vals  []V
	index map[string]int
}

const orderedIndexThreshold = 16

func (o *Ordered[V]) find(key string) int {
	if o.index != nil {
		if i, ok := o.index[key]; ok {
			return i
		}
		return -1
	}
	for i, k := range o.keys {
		if k == key {
			return i
		}
	}
	return -1
}

func (o *Ordered[V]) Set(key string, v V) {
	if i := o.find(key); i >= 0 {
		o.vals[i] = v
		return
	}
	o.Append(key, v)
}

// Append는 새 키를 끝에 붙인다. 호출자가 키가 겹치지 않음을 보장한다(날짜 곡선).
func (o *Ordered[V]) Append(key string, v V) {
	o.keys = append(o.keys, key)
	o.vals = append(o.vals, v)
	switch {
	case o.index != nil:
		o.index[key] = len(o.keys) - 1
	case len(o.keys) > orderedIndexThreshold:
		o.index = make(map[string]int, len(o.keys)*2)
		for i, k := range o.keys {
			o.index[k] = i
		}
	}
}

// Grow는 n개를 더 넣을 자리를 미리 잡는다.
func (o *Ordered[V]) Grow(n int) {
	o.keys = append(make([]string, 0, len(o.keys)+n), o.keys...)
	o.vals = append(make([]V, 0, len(o.vals)+n), o.vals...)
}

func (o *Ordered[V]) Get(key string) (V, bool) {
	if i := o.find(key); i >= 0 {
		return o.vals[i], true
	}
	var zero V
	return zero, false
}

func (o *Ordered[V]) Keys() []string { return o.keys }
func (o *Ordered[V]) Len() int       { return len(o.keys) }

func marshalNoEscape(v any) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	return bytes.TrimRight(buf.Bytes(), "\n"), nil
}

// Response는 계산 응답 {"status":"success","data":{...}}이다.
type Response struct {
	Status string `json:"status"`
	Data   *Data  `json:"data"`
}

// Data는 계산 결과다. 키 순서는 Python buy&hold 응답 순서를 따른다. 부가 데이터(include_*)는
// API 계층이 Supplemental에 채운다.
type Data struct {
	PortfolioStatistics    Statistics                 `json:"portfolio_statistics"`
	IndividualReturns      Ordered[any]               `json:"individual_returns"`
	IndividualResults      []IndividualResult         `json:"individual_results"`
	PortfolioResult        PortfolioResult            `json:"portfolio_result"`
	PortfolioComposition   []Composition              `json:"portfolio_composition"`
	EquityCurve            Ordered[float64]           `json:"equity_curve"`
	DailyReturns           Ordered[float64]           `json:"daily_returns"`
	StrategyDetails        Ordered[any]               `json:"strategy_details"`
	RebalanceHistory       []Rebalance                `json:"rebalance_history"`
	WeightHistory          []Ordered[any]             `json:"weight_history"`
	Warnings               []string                   `json:"warnings"`
	CalculationAssumptions CalculationAssumptions     `json:"calculation_assumptions"`
	Supplemental           map[string]json.RawMessage `json:"-"`
}

// Data의 JSON은 jsonenc.go가 쓴다(계산 결과 뒤에 부가 데이터 키를 Python과 같은 순서로 붙인다).

// SupplementalKeys는 POST include_*가 붙이는 키의 순서다(Python unified_data_service).
var SupplementalKeys = []string{"ticker_info", "stock_data", "exchange_rates", "exchange_stats",
	"volatility_events", "sp500_benchmark", "nasdaq_benchmark", "latest_news", "supplemental_status"}

type PortfolioResult struct {
	TotalEquity    float64 `json:"total_equity"`
	TotalReturnPct float64 `json:"total_return_pct"`
}

type CalculationAssumptions struct {
	QuantityUnit    string `json:"quantity_unit"`
	AccountCurrency string `json:"account_currency"`
	WeightBasis     string `json:"weight_basis"`
	PriceBasis      string `json:"price_basis"`
}

var assumptions = CalculationAssumptions{
	QuantityUnit:    "fractional_adjusted_unit",
	AccountCurrency: "USD",
	WeightBasis:     "asset_account_including_uninvested_cash",
	PriceBasis:      "adjusted_total_return",
}

// HoldingReturn은 buy&hold 경로의 individual_returns 항목이다.
type HoldingReturn struct {
	AssetID        string   `json:"asset_id"`
	Symbol         string   `json:"symbol"`
	Weight         float64  `json:"weight"`
	Amount         float64  `json:"amount"`
	Return         float64  `json:"return"`
	StartPrice     *float64 `json:"start_price"`
	EndPrice       *float64 `json:"end_price"`
	InvestmentType string   `json:"investment_type"`
	DCAPeriods     *int     `json:"dca_periods"`
	FinalValue     float64  `json:"final_value"`
	Trades         int      `json:"trades"`
	SharpeRatio    float64  `json:"sharpe_ratio"`
	AssetType      string   `json:"asset_type"`
}

// StrategyReturn은 기술 전략 경로의 individual_returns 항목이다.
type StrategyReturn struct {
	AssetID      string   `json:"asset_id"`
	AssetType    string   `json:"asset_type"`
	Symbol       string   `json:"symbol"`
	Weight       float64  `json:"weight"`
	Amount       float64  `json:"amount"`
	Return       float64  `json:"return"`
	InitialValue float64  `json:"initial_value"`
	FinalValue   float64  `json:"final_value"`
	Trades       int      `json:"trades"`
	WinRate      *float64 `json:"win_rate"`
}

type IndividualResult struct {
	AssetID        string   `json:"asset_id"`
	AssetType      string   `json:"asset_type"`
	Ticker         string   `json:"ticker"`
	FinalEquity    float64  `json:"final_equity"`
	TotalReturnPct float64  `json:"total_return_pct"`
	SharpeRatio    float64  `json:"sharpe_ratio"`
	Weight         float64  `json:"weight"`
	Amount         float64  `json:"amount"`
	Trades         int      `json:"trades"`
	WinRate        *float64 `json:"win_rate"`
}

// Composition은 portfolio_composition 항목이다. buy&hold 경로는 investment_type과 dca_periods(일시
// 투자는 null)를 싣고, 기술 전략 경로는 싣지 않는다(Python·rust와 같다).
type Composition struct {
	AssetID        string `json:"asset_id"`
	Symbol         string `json:"symbol"`
	Weight         float64
	Amount         float64
	InvestmentType string
	DCAPeriods     *int
	AssetType      string
	buyHold        bool
}

func (c Composition) MarshalJSON() ([]byte, error) { return encode(c) }

// Trade는 거래 원장 한 줄이다. 가격은 USD이고 *Native는 체결일 환율로 환산한 종목 통화 가격이다.
// 수량은 수정 주가 기준 소수 단위다(S01).
type Trade struct {
	EntryBar         *int     `json:"EntryBar,omitempty"`
	ExitBar          *int     `json:"ExitBar,omitempty"`
	EntryTime        string   `json:"EntryTime"`
	EntryPrice       float64  `json:"EntryPrice"`
	Size             float64  `json:"Size"`
	Commission       float64  `json:"Commission"`
	Type             string   `json:"Type,omitempty"`
	ExitTime         *string  `json:"ExitTime"`
	ExitPrice        *float64 `json:"ExitPrice"`
	PnL              *float64 `json:"PnL"`
	ReturnPct        *float64 `json:"ReturnPct"`
	Duration         *string  `json:"Duration"`
	PriceCurrency    string   `json:"PriceCurrency"`
	NativeCurrency   string   `json:"NativeCurrency"`
	QuantityUnit     string   `json:"QuantityUnit"`
	EntryPriceNative float64  `json:"EntryPriceNative"`
	ExitPriceNative  *float64 `json:"ExitPriceNative,omitempty"`
}

// BuyHoldDetail은 buy&hold 경로의 strategy_details 항목이다. open_positions는 이 경로에 없는 개념이라
// 항상 null이다(rust 계약의 키를 유지).
type BuyHoldDetail struct {
	TradeLog      []Trade `json:"trade_log"`
	OpenPositions []Trade `json:"open_positions"`
}

type Rebalance struct {
	Date           civil.Date       `json:"date"`
	Trades         []RebalanceTrade `json:"trades"`
	WeightsBefore  Ordered[float64] `json:"weights_before"`
	WeightsAfter   Ordered[float64] `json:"weights_after"`
	CommissionCost float64          `json:"commission_cost"`
}

type RebalanceTrade struct {
	AssetID    string   `json:"asset_id"`
	Symbol     string   `json:"symbol"`
	Action     string   `json:"action"`
	Shares     *float64 `json:"shares,omitempty"`
	Amount     *float64 `json:"amount,omitempty"`
	Price      float64  `json:"price"`
	Commission float64  `json:"commission"`
}

// dateKeys는 날짜 곡선의 키(YYYY-MM-DD)다. 한 번의 할당으로 모든 키를 만든다.
func dateKeys(dates []civil.Date) []string {
	buf := make([]byte, 0, len(dates)*10)
	for _, d := range dates {
		buf = d.AppendFormat(buf)
	}
	s := string(buf)
	keys := make([]string, len(dates))
	for i := range keys {
		keys[i] = s[i*10 : i*10+10]
	}
	return keys
}

// curves는 equity_curve(USD)와 daily_returns(%)다. 두 곡선은 같은 날짜 키를 공유한다(읽기 전용).
func curves(dates []civil.Date, equity, returns []float64) (Ordered[float64], Ordered[float64]) {
	keys := dateKeys(dates)
	pct := make([]float64, len(returns))
	for i, r := range returns {
		pct[i] = r * 100
	}
	return Ordered[float64]{keys: keys, vals: equity}, Ordered[float64]{keys: keys, vals: pct}
}

// newOrdered는 n개 자리를 미리 잡은 Ordered다(일별 비중 행처럼 크기를 아는 경우).
func newOrdered[V any](n int) Ordered[V] {
	return Ordered[V]{keys: make([]string, 0, n), vals: make([]V, 0, n)}
}
