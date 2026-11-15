package api

import (
	"net/url"
	"sort"
	"strconv"
	"strings"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/engine"
)

// readQuery는 GET /api/v1/{prices,exchange-rates,benchmarks,news}의 조회 인자다.
type readQuery struct {
	Symbols    []string
	Start, End civil.Date
	Limit      int
}

var queryFields = map[string][]string{
	"prices":         {"symbols", "start_date", "end_date"},
	"exchange-rates": {"start_date", "end_date"},
	"benchmarks":     {"start_date", "end_date"},
	"news":           {"symbols", "limit"},
}

// parseReadQuery는 Python query 모델(extra='forbid')과 같은 422 목록을 먼저 만들고, 통과하면 값을 검사한다.
// 같은 키가 여러 번 오면 Starlette처럼 마지막 값을 쓴다(symbols만 목록).
func parseReadQuery(section, rawQuery string, limits engine.Limits) (readQuery, error) {
	values, err := url.ParseQuery(rawQuery)
	if err != nil {
		return readQuery{}, apperr.Validation("조회 인자를 해석할 수 없습니다.")
	}
	input := map[string]any{}
	for k, v := range values {
		if k == "symbols" {
			input[k] = v
		} else {
			input[k] = v[len(v)-1]
		}
	}
	allowed := queryFields[section]
	var errs validationErrors
	for _, key := range allowed {
		if key == "limit" {
			continue
		}
		if _, ok := input[key]; !ok {
			errs = append(errs, newFieldError("missing", []any{"query", key}, "Field required", input, nil))
		}
	}
	if section == "news" {
		if v, ok := input["limit"].(string); ok {
			if n, err := strconv.Atoi(v); err == nil && (n < 1 || n > 20) {
				if n > 20 {
					errs = append(errs, newFieldError("less_than_equal", []any{"query", "limit"},
						"Input should be less than or equal to 20", v, map[string]any{"le": 20}))
				} else {
					errs = append(errs, newFieldError("greater_than_equal", []any{"query", "limit"},
						"Input should be greater than or equal to 1", v, map[string]any{"ge": 1}))
				}
			}
		}
	}
	keys := make([]string, 0, len(input))
	for k := range input {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		if !contains(allowed, k) {
			errs = append(errs, newFieldError("extra_forbidden", []any{"query", k}, "Extra inputs are not permitted", input[k], nil))
		}
	}
	if len(errs) > 0 {
		return readQuery{}, errs
	}

	q := readQuery{Limit: 15}
	for _, s := range values["symbols"] {
		if err := engine.ValidateSymbol(s, false, limits.MaxSymbolLen); err != nil {
			return readQuery{}, err
		}
		u := strings.ToUpper(s)
		if !contains(q.Symbols, u) {
			q.Symbols = append(q.Symbols, u)
		}
	}
	sort.Strings(q.Symbols)
	if contains(allowed, "symbols") && (len(q.Symbols) == 0 || len(q.Symbols) > limits.MaxItems) {
		return readQuery{}, apperr.Validation("1~%d개의 종목을 지정해 주세요.", limits.MaxItems)
	}
	if contains(allowed, "start_date") {
		start, err1 := civil.Parse(values.Get("start_date"))
		end, err2 := civil.Parse(values.Get("end_date"))
		if err1 != nil || err2 != nil {
			return readQuery{}, apperr.Validation("날짜 형식이 잘못되었습니다.")
		}
		l := limits
		l.MinPeriodDays = 0
		if err := engine.ValidatePeriod(start, end, l); err != nil {
			return readQuery{}, err
		}
		q.Start, q.End = start, end
	}
	if v, ok := input["limit"].(string); ok {
		n, err := strconv.Atoi(v)
		if err != nil {
			return readQuery{}, validationErrors{newFieldError("int_parsing", []any{"query", "limit"},
				"Input should be a valid integer, unable to parse string as an integer", v, nil)}
		}
		q.Limit = n
	}
	return q, nil
}
