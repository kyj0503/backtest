package engine

import (
	"context"
	"math"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// Run은 검증된 요청과 시세로 계산한다. req는 복사본으로 다시 검증한다(심볼 대문자화 포함).
// ctx가 취소되면 일 단위로 확인해 멈추고 ctx.Err()를 돌려준다.
func Run(ctx context.Context, req Request, data marketdata.Histories, limits Limits) (*Data, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	req.Portfolio = append([]Asset(nil), req.Portfolio...)
	if err := req.Validate(limits); err != nil {
		return nil, err
	}
	// 거래 대상 시세는 체결 가능한 OHLC여야 한다. 환산에만 쓰는 환율은 일별 기준값(종가)만 본다.
	// 환율 티커 자체를 거래 자산으로 쓰면 전체 OHLC 검사를 한다(T02).
	traded := map[string]bool{}
	for _, a := range req.Portfolio {
		if !a.Cash() {
			traded[a.Symbol] = true
		}
	}
	for symbol, h := range data {
		conversionOnly := marketdata.IsFX(symbol) && !traded[symbol]
		for _, b := range h.Bars {
			if (conversionOnly && !b.ValidRate()) || (!conversionOnly && !b.ValidPrices()) {
				return nil, apperr.Validation("유효하지 않은 가격 데이터입니다.")
			}
		}
	}

	var d *Data
	var err error
	if req.BuyHold() {
		d, err = buyHold(ctx, req, data)
	} else {
		d, err = technical(ctx, req, data)
	}
	if err != nil {
		return nil, err
	}
	s := d.PortfolioStatistics
	for _, v := range []float64{s.InitialValue, s.FinalValue, s.TotalReturn, s.AnnualReturn, s.AnnualVolatility} {
		if math.IsNaN(v) || math.IsInf(v, 0) {
			return nil, apperr.Validation("계산 결과가 지원하는 숫자 범위를 초과했습니다.")
		}
	}
	return d, nil
}
