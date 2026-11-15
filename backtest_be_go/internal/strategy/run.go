package strategy

import (
	"context"
	"encoding/json"
	"math"
	"sort"
	"strconv"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// Valuation은 달력일 평가 가격이다(직전 현지 종가 × 그날 환율, USD).
type Valuation struct {
	Date  civil.Date
	Price float64
}

// ClosedTrade는 청산된 거래다. 가격은 USD, 수량은 수정 주가 기준 소수 단위다.
type ClosedTrade struct {
	EntryBar, ExitBar     int
	EntryDate, ExitDate   civil.Date
	EntryPrice, ExitPrice float64
	Size                  float64
	EntryFee, ExitFee     float64
	PnL                   float64 // size × (exit − entry) − 진입·청산 수수료
	Return                float64 // PnL / (size × entry + 진입 수수료)
}

// OpenPosition은 기간 끝에 남은 포지션이다. 마지막 종가로 평가하며 청산하지 않는다.
type OpenPosition struct {
	EntryBar   int
	EntryDate  civil.Date
	EntryPrice float64
	Size       float64
	Fee        float64
}

// Indicator는 거래 원장에 남기는 지표 값(backtesting.py의 공개 지표 이름과 같다)이다.
type Indicator struct {
	Name   string
	Values []float64
}

type Output struct {
	Equity     []float64 // 달력일 평가액 (valuations와 같은 길이)
	Trades     []ClosedTrade
	Open       *OpenPosition
	Cash       float64
	Indicators []Indicator
	// FirstClose는 보유 비교 수익률(buy_and_hold_return_pct)의 기준 종가다(지표가 처음 완성된 봉).
	FirstClose float64
}

// Run은 바 단위 시뮬레이션이다.
//
//   - 신호는 봉의 종가로 만들고 다음 봉 시가에 체결한다. 신호 봉에서 체결하지 않는다(F01 look-ahead 제거).
//     마지막 봉의 신호는 다음 봉이 없으므로 체결하지 않는다.
//   - 매수 수량 = 평가액 × 0.95 / (종가 × (1 + 수수료율)), 소수 단위(S01). 체결 시 현금이 모자라면 취소.
//   - 수수료는 매수·매도 각각의 체결 금액 × 수수료율(F02).
//   - 볼린저는 첫 완성 창의 봉부터, 교차 전략은 직전 지표도 필요하므로 그다음 봉부터 신호를 본다(T03).
//
// bars는 USD로 환산한 거래일 봉이고, valuations는 모든 달력일의 평가 가격이다.
func Run(ctx context.Context, name string, input map[string]json.RawMessage, bars []marketdata.Bar,
	valuations []Valuation, initial, commission float64) (*Output, error) {
	if len(bars) < 2 || len(valuations) < 2 {
		return nil, apperr.Validation("전략 실행에 필요한 시세가 부족합니다.")
	}
	p, err := Parameters(name, input)
	if err != nil {
		return nil, err
	}
	close := make([]float64, len(bars))
	for i, b := range bars {
		close[i] = b.Close
	}
	var a, b []float64
	warmup := 0
	var indicators []Indicator
	f := func(v float64) string { return strconv.FormatFloat(v, 'f', -1, 64) }
	switch name {
	case "sma_strategy":
		a, b = rolling(close, int(p["short_window"]), false), rolling(close, int(p["long_window"]), false)
		warmup = int(p["long_window"]) - 1
		indicators = []Indicator{{"_sma_help…(C," + f(p["short_window"]) + ")", a}, {"_sma_help…(C," + f(p["long_window"]) + ")", b}}
	case "ema_strategy":
		a, b = ema(close, 2/(p["fast_window"]+1), false), ema(close, 2/(p["slow_window"]+1), false)
		indicators = []Indicator{{"_ema(C," + f(p["fast_window"]) + ")", a}, {"_ema(C," + f(p["slow_window"]) + ")", b}}
	case "macd_strategy":
		fast, slow := ema(close, 2/(p["fast_period"]+1), true), ema(close, 2/(p["slow_period"]+1), true)
		a = make([]float64, len(close))
		for i := range a {
			a[i] = fast[i] - slow[i]
		}
		b = ema(a, 2/(p["signal_period"]+1), true)
		indicators = []Indicator{
			{"_macd_line(C," + f(p["fast_period"]) + "," + f(p["slow_period"]) + ")", a},
			{"_signal_l…(C," + f(p["fast_period"]) + "," + f(p["slow_period"]) + "," + f(p["signal_period"]) + ")", b},
		}
	case "rsi_strategy":
		a = rsi(close, int(p["rsi_period"]))
		indicators = []Indicator{{"_rsi(C," + f(p["rsi_period"]) + ")", a}}
	case "bollinger_strategy":
		n := int(p["period"])
		a, b = rolling(close, n, false), rolling(close, n, true)
		warmup = n - 1
		lower := make([]float64, len(close))
		for i := range lower {
			lower[i] = a[i] - p["std_dev"]*b[i]
		}
		indicators = []Indicator{{"SMA(C," + f(p["period"]) + ")", a}, {"_std(C," + f(p["period"]) + ")", b}, {"λ", lower}}
	default:
		return nil, apperr.Validation("지원하지 않는 전략입니다.")
	}

	n := len(bars)
	cashAt := make([]float64, n)
	sizeAt := make([]float64, n)
	for i := range cashAt {
		cashAt[i] = initial
	}
	cash := initial
	var pos *OpenPosition
	order := 0.0
	out := &Output{Indicators: indicators, FirstClose: close[min(warmup, n-1)]}
	first := warmup + 1
	if name == "bollinger_strategy" {
		first = warmup
	}
	for i := first; i < n; i++ {
		if i%64 == 0 {
			if err := ctx.Err(); err != nil {
				return nil, err
			}
		}
		switch {
		case order < 0 && pos != nil:
			exit := bars[i].Open
			exitFee := pos.Size * exit * commission
			cash += pos.Size*exit - exitFee
			profit := pos.Size*(exit-pos.EntryPrice) - pos.Fee - exitFee
			out.Trades = append(out.Trades, ClosedTrade{
				EntryBar: pos.EntryBar, ExitBar: i, EntryDate: pos.EntryDate, ExitDate: bars[i].Date,
				EntryPrice: pos.EntryPrice, ExitPrice: exit, Size: pos.Size, EntryFee: pos.Fee, ExitFee: exitFee,
				PnL: profit, Return: profit / (pos.Size*pos.EntryPrice + pos.Fee),
			})
			pos = nil
		case order > 0 && pos == nil:
			price := bars[i].Open
			fee := order * price * commission
			if order*price+fee <= cash {
				cash -= order*price + fee
				pos = &OpenPosition{EntryBar: i, EntryDate: bars[i].Date, EntryPrice: price, Size: order, Fee: fee}
			}
		}
		order = 0
		equity := cash
		if pos != nil {
			equity += pos.Size * bars[i].Close
			sizeAt[i] = pos.Size
		}
		cashAt[i] = cash
		if !finite(equity) || !finite(cash) || !finite(sizeAt[i]) {
			return nil, apperr.Validation("계산 결과가 표현 가능한 범위를 벗어났습니다.")
		}
		var buy, sell bool
		switch name {
		case "sma_strategy", "ema_strategy", "macd_strategy":
			buy = a[i-1] < b[i-1] && a[i] > b[i]
			sell = b[i-1] < a[i-1] && b[i] > a[i]
		case "rsi_strategy":
			period := int(p["rsi_period"])
			buy = i >= period && a[i] < p["rsi_oversold"]
			sell = i >= period && (a[i] > p["rsi_overbought"] || (a[i] >= 50 && a[i-1] < 50))
		default:
			buy = close[i] < a[i]-p["std_dev"]*b[i]
			sell = close[i] > a[i]+p["std_dev"]*b[i] || close[i] >= a[i]
		}
		if pos != nil && sell {
			order = -1
		} else if pos == nil && buy {
			// 수정 OHLC는 총수익 가격 단위이지 과거 실제 주식 수가 아니다. 소수 단위가 단위 변경에도
			// 자산 가치를 보존한다.
			order = equity * 0.95 / (close[i] * (1 + commission))
		}
	}
	// 달력일 평가: 그날 이전 마지막 거래일의 현금·수량 × 그날 평가 가격.
	out.Equity = make([]float64, len(valuations))
	for k, v := range valuations {
		j := sort.Search(n, func(i int) bool { return bars[i].Date > v.Date })
		value := initial
		if j > 0 {
			value = cashAt[j-1] + sizeAt[j-1]*v.Price
		}
		if !finite(value) {
			return nil, apperr.Validation("계산 결과가 표현 가능한 범위를 벗어났습니다.")
		}
		out.Equity[k] = value
	}
	out.Cash = cash
	out.Open = pos
	return out, nil
}

func finite(v float64) bool { return !math.IsNaN(v) && !math.IsInf(v, 0) }
