// Package schedule은 적립(DCA)·리밸런싱 예정일을 만든다.
//
// 월 단위 주기는 시작일의 "N번째 요일"을 유지한다(시작일이 셋째 화요일이면 매번 셋째 화요일).
// 그 달에 N번째 요일이 없으면(다섯째 주) 그 달의 마지막 같은 요일로 맞춘다. 주 단위는 7일·14일 간격이다.
// 월을 30일로 근사하지 않는다(rust-migration F03).
package schedule

import (
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Frequency는 주기 이름의 해석이다.
type Frequency struct {
	Weekly   bool
	Interval int
}

var frequencies = map[string]Frequency{
	"weekly_1":   {true, 1},
	"weekly_2":   {true, 2},
	"monthly_1":  {false, 1},
	"monthly_2":  {false, 2},
	"monthly_3":  {false, 3},
	"monthly_6":  {false, 6},
	"monthly_12": {false, 12},
}

// Names는 지원하는 주기 이름이다(Python FREQUENCY_MAP과 같다).
var Names = []string{"weekly_1", "weekly_2", "monthly_1", "monthly_2", "monthly_3", "monthly_6", "monthly_12"}

func Parse(name string) (Frequency, bool) {
	f, ok := frequencies[name]
	return f, ok
}

// Dates는 start 다음의 예정일들(start 제외, end 포함)이다. 주기 이름이 틀리면 nil이다.
func Dates(start, end civil.Date, name string) []civil.Date {
	f, ok := frequencies[name]
	if !ok {
		return nil
	}
	var out []civil.Date
	nth := (start.Day() - 1) / 7
	weekday := start.Weekday()
	cursor := start
	for {
		if f.Weekly {
			cursor = cursor.AddDays(7 * f.Interval)
		} else {
			cursor = nthWeekday(cursor, f.Interval, weekday, nth)
		}
		if cursor > end {
			return out
		}
		out = append(out, cursor)
	}
}

// nthWeekday는 cursor의 달에서 months만큼 뒤 달의 nth(0부터) 번째 weekday다.
func nthWeekday(cursor civil.Date, months int, weekday time.Weekday, nth int) civil.Date {
	t := cursor.Time()
	first := time.Date(t.Year(), t.Month()+time.Month(months), 1, 0, 0, 0, 0, time.UTC)
	offset := (int(weekday) - int(first.Weekday()) + 7) % 7
	candidate := civil.Of(first).AddDays(offset + 7*nth)
	if candidate.Month() != first.Month() {
		candidate = candidate.AddDays(-7)
	}
	return candidate
}
