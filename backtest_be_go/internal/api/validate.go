package api

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
	"github.com/kyj0503/backtest/backtest_be_go/internal/engine"
	"github.com/kyj0503/backtest/backtest_be_go/internal/schedule"
	"github.com/kyj0503/backtest/backtest_be_go/internal/strategy"
)

// FastAPI/pydantic의 422 본문 {"detail":[{type, loc, msg, input, ctx}]}를 재현한다. 프론트가 이 형태로
// 오류를 표시하고, rust-migration이 캡처한 Python 응답(testdata/rust/http-boundary.json)이 기준이다.

type fieldError = engine.Ordered[any]

// validationErrors는 pydantic 오류 목록이다(422).
type validationErrors []fieldError

func (v validationErrors) Error() string { return fmt.Sprintf("%d validation errors", len(v)) }

func newFieldError(kind string, loc []any, msg string, input any, ctx any) fieldError {
	var e fieldError
	e.Set("type", kind)
	e.Set("loc", loc)
	e.Set("msg", msg)
	e.Set("input", input)
	if ctx != nil {
		e.Set("ctx", ctx)
	}
	return e
}

func valueError(loc []any, msg string, input any) fieldError {
	return newFieldError("value_error", loc, "Value error, "+msg, input, map[string]any{"error": map[string]any{}})
}

// decodeJSON은 숫자를 입력 그대로(json.Number) 보존해 오류의 input에 원래 값을 돌려준다.
func decodeJSON(body []byte) (any, error) {
	dec := json.NewDecoder(bytes.NewReader(body))
	dec.UseNumber()
	var v any
	if err := dec.Decode(&v); err != nil {
		return nil, invalidJSON(body, err)
	}
	if dec.More() {
		return nil, invalidJSON(body, &json.SyntaxError{Offset: dec.InputOffset() + 1})
	}
	return v, nil
}

// invalidJSON은 Python json 모듈의 오류 위치(문자 인덱스)와 메시지를 흉내 낸다.
func invalidJSON(body []byte, err error) error {
	pos := len([]rune(string(body)))
	msg := "Expecting value"
	var se *json.SyntaxError
	if errors.As(err, &se) {
		pos = len([]rune(string(body[:max(se.Offset-1, 0)])))
		switch m := se.Error(); {
		case strings.Contains(m, "looking for beginning of object key string"):
			msg = "Expecting property name enclosed in double quotes"
		case strings.Contains(m, "after object key"):
			msg = "Expecting ':' delimiter"
		case strings.Contains(m, "after object key:value pair"), strings.Contains(m, "after array element"):
			msg = "Expecting ',' delimiter"
		case strings.Contains(m, "after top-level value"):
			msg = "Extra data"
		}
	}
	return validationErrors{newFieldError("json_invalid", []any{"body", pos}, "JSON decode error",
		map[string]any{}, map[string]any{"error": msg})}
}

func laxNumber(v any) (float64, bool) {
	switch x := v.(type) {
	case json.Number:
		f, err := x.Float64()
		return f, err == nil
	case bool:
		if x {
			return 1, true
		}
		return 0, true
	case string:
		f, err := strconv.ParseFloat(strings.TrimSpace(x), 64)
		return f, err == nil
	}
	return 0, false
}

func laxBool(v any) (bool, bool) {
	switch x := v.(type) {
	case bool:
		return x, true
	case json.Number:
		switch x.String() {
		case "0":
			return false, true
		case "1":
			return true, true
		}
	case string:
		switch strings.ToLower(strings.TrimSpace(x)) {
		case "1", "true", "t", "yes", "y", "on":
			return true, true
		case "0", "false", "f", "no", "n", "off":
			return false, true
		}
	}
	return false, false
}

const (
	strategyList  = "bollinger_strategy, buy_hold_strategy, ema_strategy, macd_strategy, rsi_strategy, sma_strategy"
	frequencyList = "weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12"
)

func isStockSymbol(s string) bool {
	for i := 0; i < len(s); i++ {
		c := s[i]
		if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '.' || c == '-') {
			return false
		}
	}
	return true
}

// parseBacktest는 본문을 검증해 엔진 요청으로 바꾼다. 오류는 validationErrors(422 목록) 또는
// *apperr.Error(422 문자열)다.
func parseBacktest(body []byte, limits engine.Limits) (engine.Request, error) {
	decoded, err := decodeJSON(body)
	if err != nil {
		return engine.Request{}, err
	}
	raw, ok := decoded.(map[string]any)
	if !ok {
		return engine.Request{}, validationErrors{newFieldError("model_attributes_type", []any{"body"},
			"Input should be a valid dictionary or object to extract fields from", decoded, nil)}
	}
	var errs validationErrors
	normalized := map[string]any{}
	for k, v := range raw {
		normalized[k] = v
	}

	if items, ok := raw["portfolio"].([]any); ok {
		normItems := make([]any, len(items))
		assetsOK := true
		for i, it := range items {
			before := len(errs)
			item, isObj := it.(map[string]any)
			if !isObj {
				errs = append(errs, newFieldError("model_attributes_type", []any{"body", "portfolio", i},
					"Input should be a valid dictionary or object to extract fields from", it, nil))
				assetsOK = false
				continue
			}
			norm := map[string]any{}
			for k, v := range item {
				norm[k] = v
			}
			sym, present := item["symbol"]
			switch s, isStr := sym.(string); {
			case !present:
				errs = append(errs, newFieldError("missing", []any{"body", "portfolio", i, "symbol"}, "Field required", item, nil))
			case !isStr:
				errs = append(errs, newFieldError("string_type", []any{"body", "portfolio", i, "symbol"}, "Input should be a valid string", sym, nil))
			case s == "":
				errs = append(errs, newFieldError("string_too_short", []any{"body", "portfolio", i, "symbol"},
					"String should have at least 1 character", sym, map[string]any{"min_length": 1}))
			case len([]rune(s)) > limits.MaxSymbolLen:
				errs = append(errs, newFieldError("string_too_long", []any{"body", "portfolio", i, "symbol"},
					fmt.Sprintf("String should have at most %d characters", limits.MaxSymbolLen), sym,
					map[string]any{"max_length": limits.MaxSymbolLen}))
			case item["asset_type"] != "cash" && !isStockSymbol(s):
				errs = append(errs, valueError([]any{"body", "portfolio", i}, "주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.", item))
			}
			for _, key := range []string{"amount", "weight", "total_amount"} {
				v, present := item[key]
				if !present || v == nil {
					continue
				}
				n, ok := laxNumber(v)
				if !ok || math.IsNaN(n) || math.IsInf(n, 0) {
					errs = append(errs, newFieldError("float_parsing", []any{"body", "portfolio", i, key},
						"Input should be a valid number, unable to parse string as a number", v, nil))
					continue
				}
				norm[key] = n
				switch {
				case (key == "amount" || key == "total_amount") && n <= 0:
					errs = append(errs, newFieldError("greater_than", []any{"body", "portfolio", i, key},
						"Input should be greater than 0", v, map[string]any{"gt": 0.0}))
				case key == "weight" && n < 0:
					errs = append(errs, newFieldError("greater_than_equal", []any{"body", "portfolio", i, key},
						"Input should be greater than or equal to 0", v, map[string]any{"ge": 0.0}))
				case key == "weight" && n > 100:
					errs = append(errs, newFieldError("less_than_equal", []any{"body", "portfolio", i, key},
						"Input should be less than or equal to 100", v, map[string]any{"le": 100.0}))
				}
			}
			for _, rule := range []struct {
				key     string
				allowed []string
				msg     string
			}{
				{"investment_type", []string{"lump_sum", "dca"}, "투자 방식은 lump_sum 또는 dca만 가능합니다."},
				{"asset_type", []string{"stock", "cash"}, "자산 타입은 stock 또는 cash만 가능합니다."},
				{"dca_frequency", schedule.Names, "DCA 주기는 " + frequencyList + " 중 하나여야 합니다."},
			} {
				v, present := item[rule.key]
				if !present {
					continue
				}
				if s, ok := v.(string); !ok || !contains(rule.allowed, s) {
					errs = append(errs, valueError([]any{"body", "portfolio", i, rule.key}, rule.msg, v))
				}
			}
			normItems[i] = norm
			assetsOK = assetsOK && len(errs) == before
		}
		normalized["portfolio"] = normItems
		if assetsOK {
			errs = append(errs, portfolioRules(items, limits)...)
		}
	} else {
		v, present := raw["portfolio"]
		if !present {
			errs = append(errs, newFieldError("missing", []any{"body", "portfolio"}, "Field required", raw, nil))
		} else {
			errs = append(errs, newFieldError("list_type", []any{"body", "portfolio"}, "Input should be a valid list", v, nil))
		}
	}

	var dates [2]*civil.Date
	for i, key := range []string{"start_date", "end_date"} {
		v, present := raw[key]
		if !present {
			errs = append(errs, newFieldError("missing", []any{"body", key}, "Field required", raw, nil))
			continue
		}
		s, _ := v.(string)
		if d, err := civil.Parse(s); err == nil {
			dates[i] = &d
		} else {
			errs = append(errs, valueError([]any{"body", key}, "날짜는 YYYY-MM-DD 형식이어야 합니다.", v))
		}
	}
	if end := dates[1]; end != nil {
		var msg string
		switch start := dates[0]; {
		case *end > limits.Today:
			msg = fmt.Sprintf("종료 날짜는 미래일 수 없습니다: %s (오늘: %s)", end, limits.Today)
		case start != nil && *end <= *start:
			msg = "종료 날짜는 시작 날짜보다 이후여야 합니다."
		case start != nil && start.DaysUntil(*end) > limits.MaxPeriodDays:
			msg = "백테스트 기간은 최대 10년으로 제한됩니다."
		}
		if msg != "" {
			errs = append(errs, valueError([]any{"body", "end_date"}, msg, raw["end_date"]))
		}
	}
	if v, present := raw["commission"]; present {
		n, ok := laxNumber(v)
		switch {
		case !ok || math.IsNaN(n) || math.IsInf(n, 0):
			errs = append(errs, newFieldError("float_type", []any{"body", "commission"}, "Input should be a valid number", v, nil))
		case n < 0:
			normalized["commission"] = n
			errs = append(errs, newFieldError("greater_than_equal", []any{"body", "commission"},
				"Input should be greater than or equal to 0", v, map[string]any{"ge": 0.0}))
		case n >= 0.1:
			normalized["commission"] = n
			errs = append(errs, newFieldError("less_than", []any{"body", "commission"},
				"Input should be less than 0.1", v, map[string]any{"lt": 0.1}))
		default:
			normalized["commission"] = n
		}
	}
	if v, present := raw["rebalance_frequency"]; present {
		s, ok := v.(string)
		switch {
		case !ok:
			errs = append(errs, newFieldError("string_type", []any{"body", "rebalance_frequency"}, "Input should be a valid string", v, nil))
		case s != "none":
			if _, known := schedule.Parse(s); !known {
				errs = append(errs, valueError([]any{"body", "rebalance_frequency"},
					"유효하지 않은 리밸런싱 주기입니다: "+s+". 허용된 값: monthly_1, monthly_12, monthly_2, monthly_3, monthly_6, none, weekly_1, weekly_2", v))
			}
		}
	}
	if v, present := raw["strategy"]; present {
		s, _ := v.(string)
		if !contains(strategy.Names, s) {
			errs = append(errs, valueError([]any{"body", "strategy"}, "유효하지 않은 전략입니다: "+s+". 허용된 값: "+strategyList, v))
		}
	}
	if v, present := raw["strategy_params"]; present && v != nil {
		if _, ok := v.(map[string]any); !ok {
			errs = append(errs, newFieldError("dict_type", []any{"body", "strategy_params"}, "Input should be a valid dictionary", v, nil))
		}
	}
	for _, key := range []string{"include_stock_data", "include_volatility_events", "include_exchange_rates", "include_benchmarks", "include_news"} {
		v, present := raw[key]
		if !present {
			continue
		}
		b, ok := laxBool(v)
		if !ok {
			errs = append(errs, newFieldError("bool_parsing", []any{"body", key}, "Input should be a valid boolean, unable to interpret input", v, nil))
			continue
		}
		normalized[key] = b
	}
	if len(errs) > 0 {
		return engine.Request{}, errs
	}

	encoded, err := json.Marshal(normalized)
	if err != nil {
		return engine.Request{}, validationErrors{newFieldError("value_error", []any{"body"}, err.Error(), raw, nil)}
	}
	req := engine.Defaults()
	if err := json.Unmarshal(encoded, &req); err != nil {
		return engine.Request{}, validationErrors{newFieldError("value_error", []any{"body"}, err.Error(), raw, nil)}
	}

	if !req.BuyHold() {
		var dca []string
		for _, a := range req.Portfolio {
			if !a.Cash() && a.DCA() {
				dca = append(dca, strings.ToUpper(a.Symbol))
			}
		}
		switch {
		case len(dca) > 0:
			return engine.Request{}, validationErrors{valueError([]any{"body"}, fmt.Sprintf(
				"%s는 분할 매수(DCA)를 지원하지 않습니다 (DCA 종목: %s). DCA는 buy_hold_strategy에서만 사용할 수 있습니다.",
				req.Strategy, strings.Join(dca, ", ")), raw)}
		case req.RebalanceFrequency != nil && *req.RebalanceFrequency != "none":
			return engine.Request{}, validationErrors{valueError([]any{"body"}, fmt.Sprintf(
				"%s는 리밸런싱을 지원하지 않습니다 (rebalance_frequency=%s). rebalance_frequency를 none으로 보내거나 buy_hold_strategy를 사용하세요.",
				req.Strategy, *req.RebalanceFrequency), raw)}
		}
	}
	if days := req.StartDate.DaysUntil(req.EndDate); days < limits.MinPeriodDays {
		return engine.Request{}, apperr.Validation("백테스트 기간이 너무 짧습니다: %d일 (최소 %d일 필요)", days, limits.MinPeriodDays)
	}
	if err := req.Validate(limits); err != nil {
		if !req.BuyHold() {
			if _, perr := strategy.Parameters(req.Strategy, req.StrategyParams); perr != nil {
				// Python은 잘못된 전략 파라미터를 종목별 실패로 처리해 이 문구를 돌려줬다.
				return engine.Request{}, apperr.Validation("[ValidationError] 모든 종목의 백테스트가 실패했습니다.")
			}
		}
		return engine.Request{}, err
	}
	return req, nil
}

// portfolioRules는 항목별 검사를 통과한 포트폴리오 전체 규칙이다(개수, 중복, 금액/비중 혼합, 합계).
func portfolioRules(items []any, limits engine.Limits) validationErrors {
	if len(items) == 0 {
		return validationErrors{newFieldError("too_short", []any{"body", "portfolio"},
			"List should have at least 1 item after validation, not 0", items,
			map[string]any{"field_type": "List", "min_length": 1, "actual_length": 0})}
	}
	if len(items) > limits.MaxItems {
		return validationErrors{newFieldError("too_long", []any{"body", "portfolio"},
			fmt.Sprintf("List should have at most %d items after validation, not %d", limits.MaxItems, len(items)), items,
			map[string]any{"field_type": "List", "max_length": limits.MaxItems, "actual_length": len(items)})}
	}
	seen := map[string]bool{}
	var dups []string
	hasAmount, hasWeight := false, false
	for _, it := range items {
		item := it.(map[string]any)
		if item["asset_type"] != "cash" {
			s := strings.ToUpper(item["symbol"].(string))
			if seen[s] && !contains(dups, s) {
				dups = append(dups, s)
			}
			seen[s] = true
		}
		hasAmount = hasAmount || (item["amount"] != nil)
		hasWeight = hasWeight || (item["weight"] != nil)
	}
	key := "amount"
	if hasWeight {
		key = "weight"
	}
	total := 0.0
	for _, it := range items {
		if n, ok := laxNumber(it.(map[string]any)[key]); ok {
			total += n
		}
	}
	var msg string
	switch {
	case len(dups) > 0:
		sortStrings(dups)
		msg = "중복된 종목이 있습니다: " + strings.Join(dups, ", ") + ". 같은 종목은 한 번만 추가할 수 있습니다."
	case hasAmount && hasWeight:
		msg = "포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다. 혼합 입력 불가."
	case hasWeight && (total < 95 || total > 105):
		msg = fmt.Sprintf("종목 비중 합계가 95-105%% 범위를 벗어났습니다. 현재: %.1f%%", total)
	case !hasWeight && total <= 0:
		msg = "총 투자 금액은 0보다 커야 합니다."
	}
	if msg == "" {
		return nil
	}
	return validationErrors{valueError([]any{"body", "portfolio"}, msg, items)}
}

func contains(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}

func sortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
}
