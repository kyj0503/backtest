package schedule

import (
	"strings"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

func join(ds []civil.Date) string {
	s := make([]string, len(ds))
	for i, d := range ds {
		s[i] = d.String()
	}
	return strings.Join(s, " ")
}

func TestMonthlyKeepsNthWeekday(t *testing.T) {
	// 2023-01-17은 셋째 화요일이다.
	got := join(Dates(civil.MustParse("2023-01-17"), civil.MustParse("2023-06-30"), "monthly_1"))
	want := "2023-02-21 2023-03-21 2023-04-18 2023-05-16 2023-06-20"
	if got != want {
		t.Fatalf("got %s\nwant %s", got, want)
	}
}

func TestFifthWeekdayFallsBackToLastSameWeekday(t *testing.T) {
	// 2023-01-31은 다섯째 화요일. 2월에는 다섯째 화요일이 없어 마지막 화요일(28일).
	got := join(Dates(civil.MustParse("2023-01-31"), civil.MustParse("2023-05-31"), "monthly_1"))
	want := "2023-02-28 2023-03-28 2023-04-25 2023-05-30"
	if got != want {
		t.Fatalf("got %s\nwant %s", got, want)
	}
}

func TestIntervalsAndEndInclusive(t *testing.T) {
	start := civil.MustParse("2023-01-02") // 첫째 월요일
	if got := join(Dates(start, civil.MustParse("2023-01-30"), "weekly_2")); got != "2023-01-16 2023-01-30" {
		t.Fatal(got)
	}
	if got := join(Dates(start, civil.MustParse("2023-01-08"), "weekly_1")); got != "" {
		t.Fatal(got)
	}
	// 2024-01-01은 1월 첫째 월요일이고 종료일은 포함한다.
	if got := join(Dates(start, civil.MustParse("2024-01-01"), "monthly_6")); got != "2023-07-03 2024-01-01" {
		t.Fatal(got)
	}
	if got := join(Dates(start, civil.MustParse("2025-01-06"), "monthly_12")); got != "2024-01-01 2025-01-06" {
		t.Fatal(got)
	}
	if got := join(Dates(start, civil.MustParse("2023-12-31"), "monthly_3")); got != "2023-04-03 2023-07-03 2023-10-02" {
		t.Fatal(got)
	}
	if Dates(start, civil.MustParse("2024-01-01"), "daily") != nil {
		t.Fatal("unknown frequency")
	}
}

// 월을 30일로 근사하지 않는다: 2023-01-02(첫째 월요일)부터 30일(2/1까지)에는 다음 예정일(2/6 첫째
// 월요일)이 없다. 30일 근사였다면 2/1을 예정일로 셌을 것이다.
func TestNoThirtyDayApproximation(t *testing.T) {
	start := civil.MustParse("2023-01-02")
	if got := Dates(start, start.AddDays(30), "monthly_1"); len(got) != 0 {
		t.Fatalf("2023-01-02 + 30 days must not contain a monthly date, got %s", join(got))
	}
	if got := Dates(start, civil.MustParse("2023-02-06"), "monthly_1"); join(got) != "2023-02-06" {
		t.Fatal(join(got))
	}
}
