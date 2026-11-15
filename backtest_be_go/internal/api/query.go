package api

import (
	"fmt"
	"net/url"
	"strconv"
	"strings"
	"unicode/utf8"

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

// queryFields는 Python query 모델의 필드 순서다(PricesQuery(PeriodQuery, SymbolsQuery)는 symbols가 먼저).
var queryFields = map[string][]string{
	"prices":         {"symbols", "start_date", "end_date"},
	"exchange-rates": {"start_date", "end_date"},
	"benchmarks":     {"start_date", "end_date"},
	"news":           {"symbols", "limit"},
}

// parseReadQuery는 Python query 모델(pydantic, extra='forbid')과 같은 422 목록을 만든다.
//   - 필드 오류(필드 순서) → extra_forbidden(쿼리 순서). 필드 오류가 있으면 모델 검사(기간)는 하지 않는다.
//   - symbols: 목록 길이(too_long) → 항목별 PortfolioStock 검사(첫 오류에서 멈춤) → 대문자·중복 제거(입력 순서).
//   - 같은 키가 여러 번 오면 Starlette처럼 마지막 값을 쓴다(symbols만 목록).
func parseReadQuery(section, rawQuery string, limits engine.Limits) (readQuery, error) {
	values, order, err := parseQueryOrdered(rawQuery)
	if err != nil {
		return readQuery{}, apperr.Validation("조회 인자를 해석할 수 없습니다.")
	}
	allowed := queryFields[section]
	// FastAPI가 모델에 넘기는 입력: 모델 필드(있는 것만, 필드 순서) 다음에 나머지 키(쿼리 순서).
	var input engine.Ordered[any]
	value := func(k string) any {
		if k == "symbols" {
			return values[k]
		}
		return values[k][len(values[k])-1]
	}
	for _, k := range allowed {
		if _, ok := values[k]; ok {
			input.Set(k, value(k))
		}
	}
	for _, k := range order {
		if !contains(allowed, k) {
			input.Set(k, value(k))
		}
	}

	q := readQuery{Limit: 15}
	var errs validationErrors
	dates := map[string]civil.Date{}
	for _, key := range allowed {
		raw, present := values[key]
		if !present {
			if key != "limit" {
				errs = append(errs, newFieldError("missing", []any{"query", key}, "Field required", input, nil))
			}
			continue
		}
		switch key {
		case "symbols":
			syms, ferr := validateQuerySymbols(raw, limits)
			if ferr != nil {
				errs = append(errs, *ferr)
			}
			q.Symbols = syms
		case "start_date", "end_date":
			s := raw[len(raw)-1]
			d, ferr := parseQueryDate(key, s)
			if ferr != nil {
				errs = append(errs, *ferr)
			}
			dates[key] = d
		case "limit":
			n, ferr := parseQueryLimit(raw[len(raw)-1])
			if ferr != nil {
				errs = append(errs, *ferr)
			}
			q.Limit = n
		}
	}
	for _, k := range order {
		if !contains(allowed, k) {
			errs = append(errs, newFieldError("extra_forbidden", []any{"query", k}, "Extra inputs are not permitted", value(k), nil))
		}
	}
	if len(errs) > 0 {
		return readQuery{}, errs
	}

	if contains(allowed, "start_date") {
		q.Start, q.End = dates["start_date"], dates["end_date"]
		msg := ""
		switch {
		case q.End < q.Start:
			msg = "종료일은 시작일 이후여야 합니다."
		case q.End > limits.Today:
			msg = "미래 날짜는 조회할 수 없습니다."
		case q.Start.DaysUntil(q.End) > limits.MaxPeriodDays:
			msg = "조회 기간이 최대 허용 기간을 초과했습니다."
		}
		if msg != "" {
			return readQuery{}, validationErrors{valueError([]any{"query"}, msg, input)}
		}
	}
	return q, nil
}

// parseQueryOrdered는 url.ParseQuery와 같지만 키가 처음 나온 순서를 함께 돌려준다.
func parseQueryOrdered(raw string) (url.Values, []string, error) {
	values, err := url.ParseQuery(raw)
	if err != nil {
		return nil, nil, err
	}
	var order []string
	seen := map[string]bool{}
	for _, part := range strings.Split(raw, "&") {
		if part == "" {
			continue
		}
		k, _, _ := strings.Cut(part, "=")
		key, err := url.QueryUnescape(k)
		if err != nil || seen[key] {
			continue
		}
		seen[key] = true
		order = append(order, key)
	}
	return values, order, nil
}

// validateQuerySymbols는 SymbolsQuery.symbols(list[str], 1~MaxItems개, 항목마다 PortfolioStock(symbol=...))다.
func validateQuerySymbols(raw []string, limits engine.Limits) ([]string, *fieldError) {
	if len(raw) > limits.MaxItems {
		e := newFieldError("too_long", []any{"query", "symbols"},
			fmt.Sprintf("List should have at most %d items after validation, not %d", limits.MaxItems, len(raw)), raw,
			orderedCtx("field_type", "List", "max_length", limits.MaxItems, "actual_length", len(raw)))
		return nil, &e
	}
	var out []string
	for _, s := range raw {
		n := utf8.RuneCountInString(s)
		if n < 1 {
			e := newFieldError("string_too_short", []any{"query", "symbols", "symbol"}, "String should have at least 1 character", s,
				map[string]any{"min_length": 1})
			return nil, &e
		}
		if n > limits.MaxSymbolLen {
			e := newFieldError("string_too_long", []any{"query", "symbols", "symbol"},
				fmt.Sprintf("String should have at most %d characters", limits.MaxSymbolLen), s,
				map[string]any{"max_length": limits.MaxSymbolLen})
			return nil, &e
		}
		if !strings.EqualFold(s, "CASH") && !isStockSymbol(s) {
			e := valueError([]any{"query", "symbols"}, "주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.",
				map[string]any{"symbol": s})
			return nil, &e
		}
		if u := strings.ToUpper(s); !contains(out, u) {
			out = append(out, u)
		}
	}
	return out, nil
}

func orderedCtx(kv ...any) engine.Ordered[any] {
	var o engine.Ordered[any]
	for i := 0; i+1 < len(kv); i += 2 {
		o.Set(kv[i].(string), kv[i+1])
	}
	return o
}

// parseQueryLimit은 NewsQuery.limit(int, 1~20)이다.
func parseQueryLimit(s string) (int, *fieldError) {
	n, err := strconv.Atoi(strings.TrimSpace(s))
	if err != nil {
		e := newFieldError("int_parsing", []any{"query", "limit"},
			"Input should be a valid integer, unable to parse string as an integer", s, nil)
		return 0, &e
	}
	switch {
	case n > 20:
		e := newFieldError("less_than_equal", []any{"query", "limit"}, "Input should be less than or equal to 20", s,
			map[string]any{"le": 20})
		return 0, &e
	case n < 1:
		e := newFieldError("greater_than_equal", []any{"query", "limit"}, "Input should be greater than or equal to 1", s,
			map[string]any{"ge": 1})
		return 0, &e
	}
	return n, nil
}

// parseQueryDate는 pydantic(speedate)의 date 검사를 흔한 입력에 대해 재현한다(YYYY-MM-DD, 선택적 00:00:00 시각).
func parseQueryDate(key, s string) (civil.Date, *fieldError) {
	fail := func(reason string) (civil.Date, *fieldError) {
		e := newFieldError("date_from_datetime_parsing", []any{"query", key},
			"Input should be a valid date or datetime, "+reason, s, map[string]any{"error": reason})
		return 0, &e
	}
	digits := func(t string) bool {
		for i := 0; i < len(t); i++ {
			if t[i] < '0' || t[i] > '9' {
				return false
			}
		}
		return true
	}
	if len(s) < 10 {
		return fail("input is too short")
	}
	switch {
	case !digits(s[0:4]):
		return fail("invalid character in year")
	case s[4] != '-':
		return fail("invalid date separator, expected `-`")
	case !digits(s[5:7]):
		return fail("invalid character in month")
	case s[7] != '-':
		return fail("invalid date separator, expected `-`")
	case !digits(s[8:10]):
		return fail("invalid character in day")
	}
	y, _ := strconv.Atoi(s[0:4])
	m, _ := strconv.Atoi(s[5:7])
	d, _ := strconv.Atoi(s[8:10])
	if m < 1 || m > 12 {
		return fail("month value is outside expected range of 1-12")
	}
	if d < 1 || d > daysIn(y, m) {
		return fail("day value is outside expected range")
	}
	if len(s) > 10 {
		switch s[10] {
		case 'T', 't', '_', ' ':
		default:
			return fail("invalid datetime separator, expected `T`, `t`, `_` or space")
		}
		if t := s[11:]; t != "00:00" && t != "00:00:00" && t != "00:00:00Z" {
			e := newFieldError("date_from_datetime_inexact", []any{"query", key},
				"Datetimes provided to dates should have zero time - e.g. be exact dates", s, nil)
			return 0, &e
		}
	}
	date, err := civil.Parse(s[:10])
	if err != nil {
		return fail("input is too short")
	}
	return date, nil
}

func daysIn(y, m int) int {
	switch m {
	case 4, 6, 9, 11:
		return 30
	case 2:
		if y%4 == 0 && (y%100 != 0 || y%400 == 0) {
			return 29
		}
		return 28
	}
	return 31
}
