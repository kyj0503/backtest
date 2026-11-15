// Package strategy는 기술적 전략(SMA, EMA, MACD, RSI, Bollinger)의 지표와 바 단위 체결 엔진이다.
// backtesting.py를 대체한다.
package strategy

import (
	"encoding/json"
	"fmt"
	"math"
	"strconv"
	"strings"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
)

// Names는 요청에서 받는 전략 이름이다(Python StrategyType 값과 같다).
var Names = []string{"buy_hold_strategy", "sma_strategy", "ema_strategy", "rsi_strategy", "bollinger_strategy", "macd_strategy"}

const BuyHold = "buy_hold_strategy"

type spec struct {
	key           string
	def, min, max float64
}

// specs는 Python strategy_service.py STRATEGIES와 같은 공개 파라미터 이름·기본값·범위다.
// 이름이 다르면 사용자 값이 조용히 무시되고 기본값으로 돌던 버그가 있었다(AGENTS 규칙 11).
var specs = map[string][]spec{
	"sma_strategy":       {{"short_window", 10, 2, 50}, {"long_window", 20, 10, 200}},
	"ema_strategy":       {{"fast_window", 12, 5, 50}, {"slow_window", 26, 10, 200}},
	"macd_strategy":      {{"fast_period", 12, 5, 50}, {"slow_period", 26, 10, 100}, {"signal_period", 9, 2, 20}},
	"rsi_strategy":       {{"rsi_period", 14, 2, 50}, {"rsi_oversold", 30, 10, 40}, {"rsi_overbought", 70, 60, 90}},
	"bollinger_strategy": {{"period", 20, 5, 100}, {"std_dev", 2, 0.5, 4}},
	BuyHold:              nil,
}

var orderedPairs = [][2]string{
	{"short_window", "long_window"},
	{"fast_window", "slow_window"},
	{"fast_period", "slow_period"},
	{"rsi_oversold", "rsi_overbought"},
}

// Known는 지원하는 전략 이름인지다.
func Known(name string) bool {
	_, ok := specs[name]
	return ok
}

// Parameters는 사용자 입력을 검증한 파라미터다. 정의되지 않은 키는 무시한다(Python과 같다).
// std_dev를 뺀 값은 정수로 자른다.
func Parameters(name string, input map[string]json.RawMessage) (map[string]float64, error) {
	ss, ok := specs[name]
	if !ok {
		return nil, apperr.Validation("지원하지 않는 전략입니다.")
	}
	out := make(map[string]float64, len(ss))
	for _, s := range ss {
		v := s.def
		if raw, ok := input[s.key]; ok && string(raw) != "null" {
			n, err := number(raw)
			if err != nil {
				return nil, apperr.Validation("%s: 숫자를 입력해 주세요.", s.key)
			}
			v = n
		}
		if s.key != "std_dev" {
			v = math.Trunc(v)
		}
		if math.IsNaN(v) || math.IsInf(v, 0) || v < s.min || v > s.max {
			return nil, apperr.Validation("%s: 허용 범위는 %s~%s입니다.", s.key, format(s.min), format(s.max))
		}
		out[s.key] = v
	}
	for _, p := range orderedPairs {
		a, okA := out[p[0]]
		b, okB := out[p[1]]
		if okA && okB && a >= b {
			return nil, apperr.Validation("%s은 %s보다 작아야 합니다.", p[0], p[1])
		}
	}
	return out, nil
}

func number(raw json.RawMessage) (float64, error) {
	var f float64
	if err := json.Unmarshal(raw, &f); err == nil {
		return f, nil
	}
	var s string
	if err := json.Unmarshal(raw, &s); err != nil {
		return 0, fmt.Errorf("not a number")
	}
	return strconv.ParseFloat(strings.TrimSpace(s), 64)
}

func format(v float64) string { return strconv.FormatFloat(v, 'f', -1, 64) }
