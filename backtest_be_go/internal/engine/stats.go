package engine

import (
	"encoding/json"
	"math"
	"strconv"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// 위험 지표는 모든 달력일 평가값으로 계산한다(F09). 휴장일은 직전 가격을 유지한다.
const daysPerYear = 365.0

// cleanReturn은 부동소수점 잡음(|r| ≤ 1e-11)을 0으로 만든다. 가격이 그대로인 적립식에서 가짜
// 상승·하락일을 세지 않기 위해서다(F10).
func cleanReturn(r float64) float64 {
	if math.Abs(r) <= 1e-11 {
		return 0
	}
	return r
}

func mean(v []float64) float64 {
	if len(v) == 0 {
		return 0
	}
	s := 0.0
	for _, x := range v {
		s += x
	}
	return s / float64(len(v))
}

// stddev는 표본 표준편차(n-1)다.
func stddev(v []float64) float64 {
	if len(v) < 2 {
		return 0
	}
	m := mean(v)
	s := 0.0
	for _, x := range v {
		s += (x - m) * (x - m)
	}
	return math.Sqrt(s / float64(len(v)-1))
}

// sharpe는 무위험 수익률 0의 연환산 샤프 비율이다. 변동성이 사실상 0이면 0이다.
func sharpe(v []float64) float64 {
	sd := stddev(v)
	if sd*math.Sqrt(daysPerYear)*100 <= 1e-9 {
		return 0
	}
	return mean(v) / sd * math.Sqrt(daysPerYear)
}

// dailyReturns는 평가액 곡선의 단순 일간 수익률이다(납입 흐름이 없는 기술 전략 합산용).
func dailyReturns(equity []float64) []float64 {
	out := make([]float64, len(equity))
	for i := 1; i < len(equity); i++ {
		if equity[i-1] > 0 {
			out[i] = cleanReturn(equity[i]/equity[i-1] - 1)
		}
	}
	return out
}

// profitFactor는 청산 거래의 수수료 차감 USD 이익 합 / 손실 합의 절댓값이다. 손실이 없으면 정의되지
// 않으므로 nil이다(임의 상수로 대체하지 않는다).
func profitFactor(pnl []float64) *float64 {
	gains, losses := 0.0, 0.0
	for _, p := range pnl {
		if p > 0 {
			gains += p
		} else if p < 0 {
			losses -= p
		}
	}
	if losses <= 0 {
		return nil
	}
	r := gains / losses
	if math.IsInf(r, 0) || math.IsNaN(r) {
		return nil
	}
	return &r
}

// Optional은 필드가 없음(omitzero로 생략) / null / 값을 구분한다.
type Optional struct {
	present bool
	v       *float64
}

func Some(v float64) Optional        { return Optional{present: true, v: &v} }
func Null() Optional                 { return Optional{present: true} }
func OptionalOf(v *float64) Optional { return Optional{present: true, v: v} }
func (o Optional) IsZero() bool      { return !o.present }
func (o Optional) MarshalJSON() ([]byte, error) {
	if o.v == nil {
		return []byte("null"), nil
	}
	return json.Marshal(*o.v)
}

// Statistics는 portfolio_statistics다. 필드 순서는 Python 응답 순서를 따르고(프론트 표의 순서),
// rust 계약에서 추가된 필드는 의미가 가까운 자리에 둔다.
type Statistics struct {
	Start                        civil.Date `json:"Start"`
	End                          civil.Date `json:"End"`
	Duration                     string     `json:"Duration"`
	InitialValue                 float64    `json:"Initial_Value"`
	FinalValue                   float64    `json:"Final_Value"`
	PeakValue                    float64    `json:"Peak_Value"`
	TotalReturn                  float64    `json:"Total_Return"`
	AnnualReturn                 float64    `json:"Annual_Return"`
	TimeWeightedReturn           float64    `json:"Time_Weighted_Return"`
	AnnualVolatility             float64    `json:"Annual_Volatility"`
	ReturnObservationDaysPerYear int        `json:"Return_Observation_Days_Per_Year"`
	AnnualizationBasis           string     `json:"Annualization_Basis"`
	SharpeRatio                  float64    `json:"Sharpe_Ratio"`
	MaxDrawdown                  float64    `json:"Max_Drawdown"`
	AvgDrawdown                  float64    `json:"Avg_Drawdown"`
	MaxConsecutiveGains          int        `json:"Max_Consecutive_Gains"`
	MaxConsecutiveLosses         int        `json:"Max_Consecutive_Losses"`
	TotalTradingDays             int        `json:"Total_Trading_Days"`
	TotalTrades                  int        `json:"Total_Trades"`
	PositiveDays                 int        `json:"Positive_Days"`
	NegativeDays                 int        `json:"Negative_Days"`
	WinRate                      float64    `json:"Win_Rate"`
	TradeWinRate                 Optional   `json:"Trade_Win_Rate,omitzero"`
	ProfitFactor                 Optional   `json:"Profit_Factor"`
	SP500TotalReturnPct          Optional   `json:"sp500_total_return_pct,omitzero"`
	AlphaVsSP500Pct              Optional   `json:"alpha_vs_sp500_pct,omitzero"`
}

// statistics는 일별 평가액(equity)과 납입 흐름을 제거한 일간 수익률(returns)로 지표를 낸다.
//
//   - Total_Return: 최종 자산 / 실제 총 납입금 − 1 (납입 기준)
//   - Time_Weighted_Return: 일간 수익률의 기하 연결(startRatio에서 시작) − 1
//   - Annual_Return: TWR을 기간 일수와 365.25일/년으로 연복리화
//   - 변동성·샤프: 표본 표준편차·평균 × √365
//   - 낙폭: TWR 지수 기준(납입이 부풀린 평가액 기준이 아니다)
func statistics(dates []civil.Date, equity, returns []float64, contributed, startRatio float64, trades int) Statistics {
	r := make([]float64, len(returns))
	for i, x := range returns {
		r[i] = cleanReturn(x)
	}
	duration := dates[0].DaysUntil(dates[len(dates)-1])
	growth := startRatio
	for _, x := range r {
		growth *= 1 + x
	}
	index, peak := startRatio, 1.0
	var drawdowns []float64
	maxDD := 0.0
	gain, loss, maxGain, maxLoss, pos, neg := 0, 0, 0, 0, 0, 0
	for _, x := range r {
		index *= 1 + x
		peak = math.Max(peak, index)
		d := 0.0
		if peak > 0 {
			d = (index/peak - 1) * 100
		}
		if d < -1e-9 {
			drawdowns = append(drawdowns, d)
			maxDD = math.Min(maxDD, d)
		}
		if x > 0 {
			gain++
			pos++
		} else {
			gain = 0
		}
		if x < 0 {
			loss++
			neg++
		} else {
			loss = 0
		}
		maxGain, maxLoss = max(maxGain, gain), max(maxLoss, loss)
	}
	vol := stddev(r) * math.Sqrt(daysPerYear) * 100
	if vol <= 1e-9 {
		vol = 0
	}
	annual := 0.0
	if duration > 0 {
		annual = (math.Pow(math.Max(growth, 0), 365.25/float64(duration)) - 1) * 100
	}
	peakValue := 0.0
	for _, v := range equity {
		peakValue = math.Max(peakValue, v)
	}
	final := equity[len(equity)-1]
	winRate := 0.0
	if len(r) > 0 {
		winRate = float64(pos) / float64(len(r)) * 100
	}
	return Statistics{
		Start: dates[0], End: dates[len(dates)-1],
		Duration:                     strconv.Itoa(duration) + " days",
		InitialValue:                 contributed,
		FinalValue:                   final,
		PeakValue:                    peakValue,
		TotalReturn:                  (final/contributed - 1) * 100,
		AnnualReturn:                 annual,
		TimeWeightedReturn:           cleanReturn(growth-1) * 100,
		AnnualVolatility:             vol,
		ReturnObservationDaysPerYear: int(daysPerYear),
		AnnualizationBasis:           "calendar_daily",
		SharpeRatio:                  sharpe(r),
		MaxDrawdown:                  maxDD,
		AvgDrawdown:                  mean(drawdowns),
		MaxConsecutiveGains:          maxGain,
		MaxConsecutiveLosses:         maxLoss,
		TotalTradingDays:             len(dates),
		TotalTrades:                  trades,
		PositiveDays:                 pos,
		NegativeDays:                 neg,
		WinRate:                      winRate,
		ProfitFactor:                 Null(),
	}
}
