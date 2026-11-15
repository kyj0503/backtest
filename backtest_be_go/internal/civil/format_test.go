package civil

import (
	"testing"
	"time"
)

// AppendFormat(일 수 → 연월일 직접 계산)이 time 패키지 형식과 모든 날짜에서 같아야 한다.
func TestAppendFormatMatchesTime(t *testing.T) {
	for d := New(1900, 1, 1); d <= New(2200, 12, 31); d++ {
		if got, want := d.String(), d.Time().Format("2006-01-02"); got != want {
			t.Fatalf("%d: %s != %s", d, got, want)
		}
	}
	if got := New(1, 1, 1).String(); got != time.Date(1, 1, 1, 0, 0, 0, 0, time.UTC).Format("2006-01-02") {
		t.Fatal(got)
	}
}
