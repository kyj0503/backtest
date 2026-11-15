// Package marketdata는 일봉 시세를 Yahoo에서 가져오고 MySQL에 캐시하며 환율을 제공한다.
//
// 모든 가격은 원래 통화 그대로 저장·반환한다. USD 변환은 계산 시점에 RateOn으로 한다.
// 주식의 OHLC는 Yahoo 수정종가 비율(adjclose/close)을 한 번만 적용한 수정 주가다. 분할·배당
// 이벤트를 그 위에 다시 적용하지 않는다.
package marketdata

import (
	"math"
	"strings"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Bar는 하루치 시세다. JSON 이름은 testdata/rust/histories.json과 같다.
type Bar struct {
	Date   civil.Date `json:"date"`
	Open   float64    `json:"open"`
	High   float64    `json:"high"`
	Low    float64    `json:"low"`
	Close  float64    `json:"close"`
	Volume float64    `json:"volume"`
}

// History는 한 종목의 시세와 메타데이터다. Bars는 날짜 오름차순이고 날짜가 겹치지 않는다.
type History struct {
	Symbol         string      `json:"symbol"`
	Currency       string      `json:"currency"`
	CompanyName    string      `json:"company_name"`
	Exchange       string      `json:"exchange"`
	FirstTradeDate *civil.Date `json:"first_trade_date"`
	Bars           []Bar       `json:"bars"`
	// Repaired는 제공업체 응답의 고가·저가를 조금 넓혀 고친 날짜다(G01, 로그용). 저장·응답에는 싣지 않는다.
	Repaired []civil.Date `json:"-"`
}

// Histories는 심볼 → 시세다. 환율 티커(KRW=X 등)도 같은 맵에 들어간다.
type Histories map[string]History

// IsFX는 환율 티커인지다. 환율은 기업 행사가 없어 수정종가가 없어도 원종가를 그대로 쓴다.
func IsFX(symbol string) bool { return strings.HasSuffix(symbol, "=X") }

func positive(v float64) bool { return !math.IsNaN(v) && !math.IsInf(v, 0) && v > 0 }

// ValidRate는 환율 하루치가 쓸 수 있는 값인지다. 환율은 체결 가능한 OHLC가 아니라 일별 기준값이다.
func (b Bar) ValidRate() bool { return positive(b.Close) }

// ValidPrices는 OHLC가 모두 양의 유한수이고 서로 모순되지 않는지다. 원 OHLC에 보정 비율을 곱하면
// 고가·저가 경계에서 제공업체 수정종가와 몇 ulp 차이가 날 수 있어 그만큼만 허용한다.
func (b Bar) ValidPrices() bool {
	if !positive(b.Open) || !positive(b.High) || !positive(b.Low) || !positive(b.Close) {
		return false
	}
	tol := max(b.High, b.Close, b.Open) * 2.220446049250313e-16 * 8
	return b.High >= b.Low &&
		min(b.Open, b.Close) >= b.Low-tol &&
		max(b.Open, b.Close) <= b.High+tol
}

// ValidFor는 심볼 종류에 맞는 검사다.
func (b Bar) ValidFor(symbol string) bool {
	if IsFX(symbol) {
		return b.ValidRate()
	}
	return b.ValidPrices()
}

// Between은 [start, end] 범위의 봉만 남긴 사본이다.
func (h History) Between(start, end civil.Date) History {
	out := h
	out.Bars = nil
	for _, b := range h.Bars {
		if b.Date >= start && b.Date <= end {
			out.Bars = append(out.Bars, b)
		}
	}
	return out
}
