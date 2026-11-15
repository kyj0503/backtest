package marketdata

import (
	"encoding/json"
	"fmt"
	"slices"
	"time"
	_ "time/tzdata" // 거래소 IANA 시간대를 이미지의 tzdata 유무와 상관없이 쓴다

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Yahoo v8 chart 응답 중 쓰는 부분. null을 0과 구별하려고 값은 모두 포인터로 받는다.
type chartResponse struct {
	Chart struct {
		Result []chartResult `json:"result"`
		Error  *struct {
			Code        string `json:"code"`
			Description string `json:"description"`
		} `json:"error"`
	} `json:"chart"`
}

type chartResult struct {
	Meta struct {
		Currency             string `json:"currency"`
		Symbol               string `json:"symbol"`
		ExchangeName         string `json:"exchangeName"`
		ExchangeTimezoneName string `json:"exchangeTimezoneName"`
		LongName             string `json:"longName"`
		ShortName            string `json:"shortName"`
		FirstTradeDate       *int64 `json:"firstTradeDate"`
		GMTOffset            int64  `json:"gmtoffset"`
	} `json:"meta"`
	Timestamp  []int64 `json:"timestamp"`
	Indicators struct {
		Quote []struct {
			Open   []*float64 `json:"open"`
			High   []*float64 `json:"high"`
			Low    []*float64 `json:"low"`
			Close  []*float64 `json:"close"`
			Volume []*float64 `json:"volume"`
		} `json:"quote"`
		AdjClose []struct {
			AdjClose []*float64 `json:"adjclose"`
		} `json:"adjclose"`
	} `json:"indicators"`
}

func notFound(symbol string) *apperr.Error {
	return apperr.NotFound("가격 데이터가 없습니다: %s", symbol)
}

// ParseChart는 Yahoo chart 응답을 수정 주가 일봉으로 바꾼다.
//
//   - 날짜는 각 타임스탬프를 그 날짜의 거래소 IANA 시간대 규칙(과거 서머타임 포함)으로 해석한다.
//     시간대 이름이 없는 응답만 gmtoffset을 쓴다.
//   - 주식은 adjclose/close 비율을 OHLC에 한 번 곱한다. 수정종가가 하나라도 없으면 가격 기준이
//     섞이므로 503이다(T01). 환율은 수정종가가 없으면 원종가를 쓴다.
//   - OHLC가 전부 null인 봉(휴장)은 건너뛴다. 일부만 null이거나 0·음수·모순인 봉은 지표 창을
//     조용히 줄이지 않도록 503이다(T02).
func ParseChart(symbol string, body []byte) (History, error) {
	var resp chartResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return History{}, apperr.Unavailable("%s: 시세 응답 형식을 해석할 수 없습니다.", symbol).Wrap(err)
	}
	if e := resp.Chart.Error; e != nil {
		if e.Code == "Not Found" {
			return History{}, notFound(symbol)
		}
		return History{}, apperr.Unavailable("%s: 시세 제공업체의 응답을 사용할 수 없습니다.", symbol).
			Wrap(fmt.Errorf("yahoo error %s: %s", e.Code, e.Description))
	}
	if len(resp.Chart.Result) == 0 || len(resp.Chart.Result[0].Timestamp) == 0 {
		return History{}, notFound(symbol)
	}
	r := resp.Chart.Result[0]
	if len(r.Indicators.Quote) == 0 {
		return History{}, apperr.Unavailable("%s: 시세 응답에 OHLC가 없습니다.", symbol)
	}
	q := r.Indicators.Quote[0]
	n := len(r.Timestamp)
	if len(q.Open) != n || len(q.High) != n || len(q.Low) != n || len(q.Close) != n ||
		(q.Volume != nil && len(q.Volume) != n) {
		return History{}, apperr.Unavailable("%s: 시세 배열 길이가 일치하지 않습니다.", symbol)
	}
	var adj []*float64
	if len(r.Indicators.AdjClose) > 0 {
		adj = r.Indicators.AdjClose[0].AdjClose
		if adj != nil && len(adj) != n {
			return History{}, apperr.Unavailable("%s: 수정 종가 배열 길이가 일치하지 않습니다.", symbol)
		}
	}

	var loc *time.Location
	if name := r.Meta.ExchangeTimezoneName; name != "" {
		l, err := time.LoadLocation(name)
		if err != nil {
			return History{}, apperr.Unavailable("%s: 시세의 거래소 시간대를 확인할 수 없습니다.", symbol).Wrap(err)
		}
		loc = l
	} else {
		loc = time.FixedZone("gmtoffset", int(r.Meta.GMTOffset))
	}

	fx := IsFX(symbol)
	bars := make([]Bar, 0, n)
	var repairs []civil.Date
	for i, ts := range r.Timestamp {
		fields := [4]*float64{q.Open[i], q.High[i], q.Low[i], q.Close[i]}
		if fields[0] == nil && fields[1] == nil && fields[2] == nil && fields[3] == nil {
			continue
		}
		var v [4]float64
		for k, p := range fields {
			if p == nil || !positive(*p) {
				return History{}, apperr.Unavailable("%s: 불완전하거나 유효하지 않은 OHLC 시세입니다.", symbol)
			}
			v[k] = *p
		}
		date := civil.Of(time.Unix(ts, 0).In(loc))
		raw := Bar{Date: date, Open: v[0], High: v[1], Low: v[2], Close: v[3]}
		if !raw.ValidFor(symbol) {
			repaired, ok := repairRange(raw)
			if !ok {
				return History{}, apperr.Unavailable("%s: 시세의 OHLC 범위가 일치하지 않습니다.", symbol)
			}
			raw = repaired
			v[1], v[2] = raw.High, raw.Low
			repairs = append(repairs, date)
		}

		adjusted := v[3]
		switch {
		case adj != nil && adj[i] != nil:
			adjusted = *adj[i]
		case !fx:
			return History{}, apperr.Unavailable("%s: 수정 종가가 누락되어 일관된 가격 기준을 확인할 수 없습니다.", symbol)
		}
		ratio := adjusted / v[3]
		if !positive(ratio) {
			return History{}, apperr.Unavailable("%s: 유효하지 않은 수정 주가입니다.", symbol)
		}
		bar := Bar{Date: date, Open: v[0] * ratio, High: v[1] * ratio, Low: v[2] * ratio, Close: adjusted}
		if !positive(bar.Open) || !positive(bar.High) || !positive(bar.Low) {
			return History{}, apperr.Unavailable("%s: 수정 주가가 수치 범위를 벗어났습니다.", symbol)
		}
		if !bar.ValidFor(symbol) {
			return History{}, apperr.Unavailable("%s: 유효하지 않은 수정 OHLC 시세입니다.", symbol)
		}
		if q.Volume != nil && q.Volume[i] != nil && *q.Volume[i] > 0 {
			bar.Volume = *q.Volume[i]
		}
		bars = append(bars, bar)
	}
	slices.SortStableFunc(bars, func(a, b Bar) int { return int(a.Date) - int(b.Date) })
	bars = slices.CompactFunc(bars, func(a, b Bar) bool { return a.Date == b.Date })

	h := History{
		Symbol:      symbol,
		Currency:    r.Meta.Currency,
		CompanyName: firstNonEmpty(r.Meta.LongName, r.Meta.ShortName, symbol),
		Exchange:    r.Meta.ExchangeName,
		Bars:        bars,
		Repaired:    repairs,
	}
	if r.Meta.FirstTradeDate != nil {
		d := civil.Of(time.Unix(*r.Meta.FirstTradeDate, 0).UTC())
		h.FirstTradeDate = &d
	}
	return h, nil
}

// maxRangeRepair는 고가·저가 범위를 넓혀 고칠 수 있는 최대 상대 이탈이다.
const maxRangeRepair = 0.01

// repairRange는 고가·저가가 시가·종가를 조금(1% 이내) 벗어난 봉을 고친다(G01).
//
// 실제 Yahoo 일봉에는 종가가 저가보다 0.17% 낮은 봉 같은 제공업체 오류가 있다(005930.KS
// 2024-10-14: 시가 59,500 고가 61,200 저가 59,400 종가 59,300). T02 원칙대로 모두 거부하면 그 종목이
// 들어간 기간 전체를 계산할 수 없다. 체결·평가에 쓰는 시가·종가는 제공업체 값을 그대로 두고, 범위만
// 시가·종가를 포함하도록 넓힌다. 이탈이 크면(시가 1 대 범위 80~120처럼 단위가 틀린 값) 고치지 않고
// 거부한다. 0·음수·부분 누락은 이 함수에 오기 전에 거부된다.
func repairRange(b Bar) (Bar, bool) {
	lo := min(b.Open, b.High, b.Low, b.Close)
	hi := max(b.Open, b.High, b.Low, b.Close)
	if b.High < b.Low {
		return b, false
	}
	if (b.Low-lo)/b.Low > maxRangeRepair || (hi-b.High)/b.High > maxRangeRepair {
		return b, false
	}
	b.Low, b.High = lo, hi
	return b, b.ValidPrices()
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if v != "" {
			return v
		}
	}
	return ""
}
