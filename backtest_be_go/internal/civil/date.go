// Package civil은 시간대 없는 달력 날짜를 다룬다.
//
// 시세·납입·리밸런싱은 모두 거래소 현지 날짜 단위다. time.Time을 쓰면 UTC 변환이나 서머타임에서
// 날짜가 하루 밀리는 버그가 생기기 쉬우므로(rust-migration Yahoo 회귀), 날짜는 1970-01-01부터의
// 일 수로만 표현한다. 비교·차이·요일 계산이 정수 연산이 된다.
package civil

import (
	"encoding/json"
	"fmt"
	"time"
)

// Date는 1970-01-01을 0으로 하는 일 수다.
type Date int32

const layout = "2006-01-02"

// Of는 t의 (t가 가진 시간대 기준) 날짜다.
func Of(t time.Time) Date {
	y, m, d := t.Date()
	return New(y, m, d)
}

func New(year int, month time.Month, day int) Date {
	return Date(time.Date(year, month, day, 0, 0, 0, 0, time.UTC).Unix() / 86400)
}

// Parse는 YYYY-MM-DD만 받는다. 존재하지 않는 날짜(2023-02-30)는 오류다.
func Parse(s string) (Date, error) {
	t, err := time.Parse(layout, s)
	if err != nil {
		return 0, fmt.Errorf("invalid date %q (want YYYY-MM-DD)", s)
	}
	return Of(t), nil
}

func MustParse(s string) Date {
	d, err := Parse(s)
	if err != nil {
		panic(err)
	}
	return d
}

func (d Date) Time() time.Time { return time.Unix(int64(d)*86400, 0).UTC() }

func (d Date) String() string { return string(d.AppendFormat(make([]byte, 0, 10))) }

// civil은 일 수를 (연, 월, 일)로 바꾼다(Howard Hinnant의 civil_from_days). time 패키지를 거치지 않아
// 일별 곡선 수천 개를 직렬화할 때 할당이 없다.
func (d Date) civil() (y, m, day int) {
	z := int(d) + 719468
	era := z / 146097
	if z < 0 && z%146097 != 0 {
		era--
	}
	doe := z - era*146097
	yoe := (doe - doe/1460 + doe/36524 - doe/146096) / 365
	y = yoe + era*400
	doy := doe - (365*yoe + yoe/4 - yoe/100)
	mp := (5*doy + 2) / 153
	day = doy - (153*mp+2)/5 + 1
	if mp < 10 {
		m = mp + 3
	} else {
		m = mp - 9
	}
	if m <= 2 {
		y++
	}
	return y, m, day
}

// AppendFormat은 YYYY-MM-DD를 b 뒤에 붙인다. 0000~9999년만 쓴다(그 밖은 time 형식으로 대신한다).
func (d Date) AppendFormat(b []byte) []byte {
	y, m, day := d.civil()
	if y < 0 || y > 9999 {
		return d.Time().AppendFormat(b, layout)
	}
	return append(b, byte('0'+y/1000), byte('0'+y/100%10), byte('0'+y/10%10), byte('0'+y%10), '-',
		byte('0'+m/10), byte('0'+m%10), '-', byte('0'+day/10), byte('0'+day%10))
}

func (d Date) AddDays(n int) Date { return d + Date(n) }

// AddMonths는 월을 더하고 말일을 넘으면 그 달 말일로 맞춘다(1/31 + 1개월 = 2/28 또는 2/29).
func (d Date) AddMonths(n int) Date {
	y, m, day := d.Time().Date()
	first := time.Date(y, m+time.Month(n), 1, 0, 0, 0, 0, time.UTC)
	last := first.AddDate(0, 1, -1).Day()
	return New(first.Year(), first.Month(), min(day, last))
}

func (d Date) Weekday() time.Weekday { return d.Time().Weekday() }

func (d Date) Year() int { return d.Time().Year() }

func (d Date) Month() time.Month { return d.Time().Month() }

func (d Date) Day() int { return d.Time().Day() }

// DaysUntil은 e - d (일)이다.
func (d Date) DaysUntil(e Date) int { return int(e - d) }

func (d Date) MarshalJSON() ([]byte, error) { return json.Marshal(d.String()) }

func (d *Date) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return fmt.Errorf("date must be a string: %w", err)
	}
	v, err := Parse(s)
	if err != nil {
		return err
	}
	*d = v
	return nil
}

func (d Date) MarshalText() ([]byte, error) { return []byte(d.String()), nil }

func (d *Date) UnmarshalText(b []byte) error {
	v, err := Parse(string(b))
	if err != nil {
		return err
	}
	*d = v
	return nil
}
