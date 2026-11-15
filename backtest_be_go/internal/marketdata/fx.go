package marketdata

import (
	"sort"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// FXLookbackDays는 환율을 시작일보다 이만큼 앞에서부터 가져오는 여유다. 시작일이 환율 휴장일이어도
// 직전 환율이 있도록 한다(Python portfolio_data_loader와 같은 60일).
const FXLookbackDays = 60

type fxPair struct {
	Ticker string
	// Multiply가 참이면 시세가 "1 통화 = X USD"(EURUSD=X 등)라 곱하고,
	// 거짓이면 "1 USD = X 통화"(KRW=X 등)라 나눈다.
	Multiply bool
}

// supportedFX는 Python app/constants/currencies.py와 같은 13개 통화다(USD 포함).
var supportedFX = map[string]fxPair{
	"KRW": {"KRW=X", false},
	"JPY": {"JPY=X", false},
	"EUR": {"EURUSD=X", true},
	"GBP": {"GBPUSD=X", true},
	"CNY": {"CNY=X", false},
	"HKD": {"HKD=X", false},
	"TWD": {"TWD=X", false},
	"SGD": {"SGD=X", false},
	"AUD": {"AUDUSD=X", true},
	"CAD": {"CADUSD=X", true},
	"CHF": {"CHFUSD=X", true},
	"INR": {"INR=X", false},
}

// FXTicker는 통화의 환율 티커다. USD는 ("", true), 지원하지 않는 통화는 ("", false).
func FXTicker(currency string) (string, bool) {
	if currency == "USD" {
		return "", true
	}
	p, ok := supportedFX[currency]
	return p.Ticker, ok
}

// RateOn은 day의 "1 통화 = ? USD" 값이다. day 당일 또는 그 이전의 가장 최근 환율만 쓴다.
// 미래 환율로 메우지 않는다(뒤 채우기 금지). 쓸 수 있는 환율이 없으면 조용히 원통화 가격을 쓰지 않고
// 오류를 돌려준다.
func RateOn(currency string, day civil.Date, data Histories) (float64, error) {
	if currency == "USD" {
		return 1, nil
	}
	p, ok := supportedFX[currency]
	if !ok {
		return 0, apperr.Validation("지원하지 않거나 확인할 수 없는 통화: %s", currency)
	}
	rates, ok := data[p.Ticker]
	if !ok {
		return 0, apperr.Validation("%s: 환율이 없습니다.", currency)
	}
	i := sort.Search(len(rates.Bars), func(i int) bool { return rates.Bars[i].Date > day })
	if i == 0 || !rates.Bars[i-1].ValidRate() {
		return 0, apperr.Validation("%s: %s 이전의 유효한 환율이 없습니다.", currency, day)
	}
	r := rates.Bars[i-1].Close
	if p.Multiply {
		return r, nil
	}
	return 1 / r, nil
}
