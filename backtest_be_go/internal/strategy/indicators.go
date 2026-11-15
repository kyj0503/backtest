package strategy

import "math"

// ema는 지수 이동 평균이다. adjust=false는 pandas ewm(adjust=False)의 재귀식,
// adjust=true는 pandas 기본(가중치 정규화)과 같다.
func ema(values []float64, alpha float64, adjust bool) []float64 {
	out := make([]float64, len(values))
	if len(values) == 0 {
		return out
	}
	num, den := values[0], 1.0
	for i, x := range values {
		if i > 0 {
			if adjust {
				num = x + (1-alpha)*num
				den = 1 + (1-alpha)*den
			} else {
				num = alpha*x + (1-alpha)*num
			}
		}
		out[i] = num / den
	}
	return out
}

// rolling은 n개 창의 평균(std=false) 또는 표본 표준편차(std=true)다. 창이 차기 전은 NaN이다.
func rolling(values []float64, n int, std bool) []float64 {
	out := make([]float64, len(values))
	for i := range values {
		if i+1 < n {
			out[i] = math.NaN()
			continue
		}
		w := values[i+1-n : i+1]
		if std {
			out[i] = stddev(w)
		} else {
			out[i] = mean(w)
		}
	}
	return out
}

// rsi는 첫 n개 가격 변화의 산술 평균으로 상승·하락 폭을 시작한 뒤 Wilder 평활을 적용한다(F08).
// 상승·하락이 모두 0인 완전 평탄 구간은 중립값 50이다. 처음 n개는 NaN이다.
func rsi(close []float64, n int) []float64 {
	out := make([]float64, len(close))
	for i := range out {
		out[i] = math.NaN()
	}
	if len(close) <= n {
		return out
	}
	delta := make([]float64, len(close))
	for i := 1; i < len(close); i++ {
		delta[i] = close[i] - close[i-1]
	}
	gain, loss := 0.0, 0.0
	for _, d := range delta[1 : n+1] {
		gain += math.Max(d, 0)
		loss += math.Max(-d, 0)
	}
	gain /= float64(n)
	loss /= float64(n)
	for i := n; i < len(close); i++ {
		if i > n {
			gain = (gain*float64(n-1) + math.Max(delta[i], 0)) / float64(n)
			loss = (loss*float64(n-1) + math.Max(-delta[i], 0)) / float64(n)
		}
		if gain+loss == 0 {
			out[i] = 50
		} else {
			out[i] = 100 * gain / (gain + loss)
		}
	}
	return out
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
