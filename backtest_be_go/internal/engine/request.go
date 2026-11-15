// Package engine은 포트폴리오 백테스트 계산이다: 요청 검증, buy&hold 일별 시뮬레이션(일시·적립·현금·
// 리밸런싱), 기술적 전략 합산, 통계, 응답 구성.
//
// 계산 계약은 rust-migration 브랜치에서 정합성 수정(F01–F16, R01–R11, S01–S06, T01–T05)을 거친 정의다
// (docs/go-migration-plan.md). develop의 Python 출력은 회귀 기록일 뿐 기준이 아니다.
package engine

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"strconv"
	"strings"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/schedule"
	"github.com/kyj0503/backtest/backtest_be_go/internal/strategy"
)

// errNotNumber는 숫자로 해석할 수 없는 값이다. API 계층이 pydantic 형식 422 메시지로 바꾼다.
var errNotNumber = errors.New("input should be a valid number")

// Number는 pydantic 느슨한 숫자처럼 숫자·숫자 문자열·불리언을 받는다. null과 생략은 nil이다.
type Number struct{ V *float64 }

func (n *Number) UnmarshalJSON(b []byte) error {
	b = bytes.TrimSpace(b)
	if string(b) == "null" {
		n.V = nil
		return nil
	}
	var f float64
	switch {
	case string(b) == "true":
		f = 1
	case string(b) == "false":
		f = 0
	case len(b) > 0 && b[0] == '"':
		var s string
		if err := json.Unmarshal(b, &s); err != nil {
			return err
		}
		v, err := strconv.ParseFloat(strings.TrimSpace(s), 64)
		if err != nil {
			return errNotNumber
		}
		f = v
	default:
		if err := json.Unmarshal(b, &f); err != nil {
			return errNotNumber
		}
	}
	n.V = &f
	return nil
}

func (n Number) MarshalJSON() ([]byte, error) {
	if n.V == nil {
		return []byte("null"), nil
	}
	return json.Marshal(*n.V)
}

func (n Number) set() bool { return n.V != nil }

func (n Number) or(def float64) float64 {
	if n.V == nil {
		return def
	}
	return *n.V
}

// Asset은 포트폴리오 항목이다.
type Asset struct {
	Symbol string `json:"symbol"`
	// Amount는 금액 모드의 회당 금액(USD)이다.
	Amount Number `json:"amount"`
	// TotalAmount는 이 항목의 정확한 총예산이다. 적립이면 센트 단위 기본 회차 금액으로 나누고 마지막
	// 회차에서 잔액을 맞춘다. amount와 함께만 쓰고 weight와는 쓰지 않는다.
	TotalAmount Number `json:"total_amount"`
	// Weight는 비중 모드 값(%)이다. 비중 모드의 기준 총액은 100 USD다(Python과 같다).
	Weight         Number `json:"weight"`
	InvestmentType string `json:"investment_type"`
	DCAFrequency   string `json:"dca_frequency"`
	AssetType      string `json:"asset_type"`
	CustomName     string `json:"custom_name,omitempty"`
}

func (a Asset) Cash() bool { return a.AssetType == "cash" }
func (a Asset) DCA() bool  { return a.InvestmentType == "dca" }

// ID는 응답 안에서 항목을 잇는 키다. 주식은 정규화된 심볼, 현금은 "표시이름__cash_요청순번"이다.
// 같은 이름의 현금 항목을 합치지 않는다(F07: CASH 티커와 현금 충돌).
func (a Asset) ID(index int) string {
	if a.Cash() {
		return fmt.Sprintf("%s__cash_%d", a.Symbol, index+1)
	}
	return a.Symbol
}

// Base는 회당(일시면 전체) 기준 금액이다: 적립이 아니면 total_amount, 다음 amount, 다음 weight.
func (a Asset) Base() float64 {
	if a.TotalAmount.set() && !a.DCA() {
		return *a.TotalAmount.V
	}
	if a.Amount.set() {
		return *a.Amount.V
	}
	return a.Weight.or(0)
}

// Request는 POST /api/v1/backtest 본문이다. 기본값은 Python 스키마와 같다.
type Request struct {
	Portfolio          []Asset                    `json:"portfolio"`
	StartDate          civil.Date                 `json:"start_date"`
	EndDate            civil.Date                 `json:"end_date"`
	Strategy           string                     `json:"strategy"`
	StrategyParams     map[string]json.RawMessage `json:"strategy_params"`
	Commission         float64                    `json:"commission"`
	RebalanceFrequency *string                    `json:"rebalance_frequency"`

	IncludeStockData        bool `json:"include_stock_data"`
	IncludeVolatilityEvents bool `json:"include_volatility_events"`
	IncludeExchangeRates    bool `json:"include_exchange_rates"`
	IncludeBenchmarks       bool `json:"include_benchmarks"`
	IncludeNews             bool `json:"include_news"`
}

// Defaults는 생략된 필드에 Python 기본값을 채운 요청이다. JSON 디코딩 전에 쓴다.
func Defaults() Request {
	return Request{
		Strategy:                strategy.BuyHold,
		Commission:              0.002,
		IncludeStockData:        true,
		IncludeVolatilityEvents: true,
		IncludeExchangeRates:    true,
		IncludeBenchmarks:       true,
		IncludeNews:             true,
	}
}

// UnmarshalJSON은 portfolio 항목의 기본값(lump_sum, monthly_1, stock)을 채운다.
func (a *Asset) UnmarshalJSON(b []byte) error {
	type plain Asset
	p := plain{InvestmentType: "lump_sum", DCAFrequency: "monthly_1", AssetType: "stock"}
	if err := json.Unmarshal(b, &p); err != nil {
		return err
	}
	*a = Asset(p)
	return nil
}

func (r Request) BuyHold() bool { return r.Strategy == strategy.BuyHold }

// Rebalance는 리밸런싱 주기다. 생략하면 buy&hold는 monthly_1, 기술 전략은 none이다. 명시한 값과
// 생략을 구분해야 기술 전략에 rebalance_frequency를 명시한 요청을 거부할 수 있다.
func (r Request) Rebalance() string {
	if r.RebalanceFrequency != nil {
		return *r.RebalanceFrequency
	}
	if r.BuyHold() {
		return "monthly_1"
	}
	return "none"
}

// Limits는 검증 한도다(config에서 온다).
type Limits struct {
	MinPeriodDays int
	MaxPeriodDays int
	MaxItems      int
	MaxSymbolLen  int
	Today         civil.Date
}

const maxPlannedUSD = 1e12

// Validate는 업무 규칙을 검사하고 주식 심볼을 대문자로 정규화한다(r을 바꾼다).
func (r *Request) Validate(l Limits) error {
	if err := ValidatePeriod(r.StartDate, r.EndDate, l); err != nil {
		return err
	}
	if len(r.Portfolio) == 0 || len(r.Portfolio) > l.MaxItems {
		return apperr.Validation("포트폴리오는 1~%d개 항목이어야 합니다.", l.MaxItems)
	}
	if math.IsNaN(r.Commission) || r.Commission < 0 || r.Commission >= 0.1 {
		return apperr.Validation("수수료는 0 이상 0.1 미만이어야 합니다.")
	}
	if !strategy.Known(r.Strategy) {
		return apperr.Validation("지원하지 않는 전략입니다.")
	}
	if reb := r.Rebalance(); reb != "none" {
		if _, ok := schedule.Parse(reb); !ok {
			return apperr.Validation("유효하지 않은 리밸런싱 주기입니다.")
		}
	}
	seen := map[string]bool{}
	for i := range r.Portfolio {
		a := &r.Portfolio[i]
		if (a.AssetType != "cash" && a.AssetType != "stock") || (a.InvestmentType != "lump_sum" && a.InvestmentType != "dca") {
			return apperr.Validation("유효하지 않은 자산 또는 투자 방식입니다.")
		}
		if err := ValidateSymbol(a.Symbol, a.Cash(), l.MaxSymbolLen); err != nil {
			return err
		}
		if !a.Cash() {
			a.Symbol = strings.ToUpper(a.Symbol)
			if seen[a.Symbol] {
				return apperr.Validation("중복된 종목입니다.")
			}
			seen[a.Symbol] = true
		}
		if badAmount(a.Amount) || badAmount(a.TotalAmount) || badWeight(a.Weight) {
			return apperr.Validation("금액 또는 비중이 유효하지 않습니다.")
		}
		if a.Amount.set() && a.Weight.set() {
			return apperr.Validation("각 항목에 amount 또는 weight 중 하나를 입력해 주세요.")
		}
		if a.TotalAmount.set() && (!a.Amount.set() || a.Weight.set()) {
			return apperr.Validation("total_amount는 amount와 함께만 사용할 수 있습니다.")
		}
		if _, ok := schedule.Parse(a.DCAFrequency); !ok {
			return apperr.Validation("유효하지 않은 DCA 주기입니다.")
		}
		if a.DCA() && len(schedule.Dates(r.StartDate, r.EndDate, a.DCAFrequency)) == 0 {
			return apperr.Validation("DCA 주기가 백테스트 기간보다 깁니다.")
		}
	}
	planned := 0.0
	for _, a := range r.Portfolio {
		planned += r.plannedBudget(a)
	}
	if math.IsNaN(planned) || math.IsInf(planned, 0) || planned <= 0 || planned > maxPlannedUSD {
		return apperr.Validation("총 예정 납입액은 0 초과 1조 USD 이하여야 합니다.")
	}
	weights, amounts := false, false
	sum := 0.0
	for _, a := range r.Portfolio {
		weights = weights || a.Weight.set()
		amounts = amounts || a.Amount.set()
		sum += a.Base()
	}
	if weights && amounts {
		return apperr.Validation("금액과 비중을 혼합할 수 없습니다.")
	}
	if weights && (sum < 95 || sum > 105) {
		return apperr.Validation("비중 합계는 95~105%%여야 합니다.")
	}
	if !r.BuyHold() {
		dca := false
		for _, a := range r.Portfolio {
			dca = dca || a.DCA()
		}
		if r.Rebalance() != "none" || dca {
			return apperr.Validation("DCA와 리밸런싱은 buy_hold_strategy에서만 지원합니다.")
		}
	}
	_, err := strategy.Parameters(r.Strategy, r.StrategyParams)
	return err
}

// plannedBudget은 항목의 총 예정 납입액이다.
func (r Request) plannedBudget(a Asset) float64 {
	if a.TotalAmount.set() {
		return *a.TotalAmount.V
	}
	if a.DCA() && !a.Weight.set() {
		return a.Base() * float64(1+len(schedule.Dates(r.StartDate, r.EndDate, a.DCAFrequency)))
	}
	return a.Base()
}

// badAmount: 금액은 0 초과 1조 이하의 유한수여야 한다.
func badAmount(n Number) bool {
	if !n.set() {
		return false
	}
	v := *n.V
	return math.IsNaN(v) || math.IsInf(v, 0) || v <= 0 || v > maxPlannedUSD
}

func badWeight(n Number) bool {
	if !n.set() {
		return false
	}
	v := *n.V
	return math.IsNaN(v) || v < 0 || v > 100
}

// ValidateSymbol: 1~maxLen자, 주식은 영문·숫자·'.'·'-'만.
func ValidateSymbol(symbol string, cash bool, maxLen int) error {
	n := len([]rune(symbol))
	if n == 0 || n > maxLen {
		return apperr.Validation("유효하지 않은 종목 심볼입니다.")
	}
	if !cash {
		for i := 0; i < len(symbol); i++ {
			c := symbol[i]
			if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '.' || c == '-') {
				return apperr.Validation("유효하지 않은 종목 심볼입니다.")
			}
		}
	}
	return nil
}

// ValidatePeriod: 기간 min~max일, 종료일은 미래일 수 없다.
func ValidatePeriod(start, end civil.Date, l Limits) error {
	days := start.DaysUntil(end)
	if days < l.MinPeriodDays || days > l.MaxPeriodDays || end > l.Today {
		return apperr.Validation("조회 기간은 %d~%d일이며 종료일은 미래일 수 없습니다.", l.MinPeriodDays, l.MaxPeriodDays)
	}
	return nil
}
