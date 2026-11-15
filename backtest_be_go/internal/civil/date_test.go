package civil

import (
	"encoding/json"
	"testing"
	"time"
)

func TestParseRejectsNonDates(t *testing.T) {
	for _, s := range []string{"2023-02-30", "2023-1-05", "20230105", "", "2023-01-05T00:00:00Z"} {
		if _, err := Parse(s); err == nil {
			t.Errorf("%q accepted", s)
		}
	}
}

func TestArithmetic(t *testing.T) {
	d := MustParse("2024-02-28")
	if got := d.AddDays(1).String(); got != "2024-02-29" {
		t.Fatal(got)
	}
	if got := d.AddDays(2).String(); got != "2024-03-01" {
		t.Fatal(got)
	}
	if got := MustParse("2023-01-31").AddMonths(1).String(); got != "2023-02-28" {
		t.Fatal(got)
	}
	if got := MustParse("2024-01-31").AddMonths(1).String(); got != "2024-02-29" {
		t.Fatal(got)
	}
	if got := MustParse("2023-11-30").AddMonths(3).String(); got != "2024-02-29" {
		t.Fatal(got)
	}
	if MustParse("2026-11-15").Weekday() != time.Sunday {
		t.Fatal("weekday")
	}
	if MustParse("2023-01-01").DaysUntil(MustParse("2024-01-01")) != 365 {
		t.Fatal("days")
	}
	if MustParse("1969-12-31") != -1 {
		t.Fatal("pre-epoch")
	}
}

func TestOfUsesTheValuesZone(t *testing.T) {
	seoul, _ := time.LoadLocation("Asia/Seoul")
	instant := time.Date(2024, 1, 1, 15, 30, 0, 0, time.UTC) // 서울 2024-01-02 00:30
	if got := Of(instant.In(seoul)).String(); got != "2024-01-02" {
		t.Fatal(got)
	}
	if got := Of(instant).String(); got != "2024-01-01" {
		t.Fatal(got)
	}
}

func TestJSON(t *testing.T) {
	var v struct {
		D Date            `json:"d"`
		M map[Date]string `json:"m"`
	}
	if err := json.Unmarshal([]byte(`{"d":"2023-10-31","m":{"2023-01-02":"x"}}`), &v); err != nil {
		t.Fatal(err)
	}
	out, _ := json.Marshal(v)
	if string(out) != `{"d":"2023-10-31","m":{"2023-01-02":"x"}}` {
		t.Fatal(string(out))
	}
	if err := json.Unmarshal([]byte(`{"d":"2023-13-01"}`), &v); err == nil {
		t.Fatal("invalid month accepted")
	}
}
