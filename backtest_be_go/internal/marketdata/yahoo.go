package marketdata

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"strconv"
	"time"

	"golang.org/x/time/rate"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Fetcher는 외부(또는 고정 픽스처)에서 시세를 가져온다.
type Fetcher interface {
	Fetch(ctx context.Context, symbol string, start, end civil.Date) (History, error)
}

// Yahoo는 Yahoo v8 chart API 클라이언트다. 이 경로는 쿠키·crumb 인증이 필요 없다.
// 요청 속도는 프로세스 전체에서 하나의 limiter로 제한한다(제공업체가 보장한 허용량은 아니다).
type Yahoo struct {
	HTTP    *http.Client
	BaseURL string
	Limiter *rate.Limiter
	Log     *slog.Logger
	// Backoff는 n번째 재시도 전 대기 시간이다(Python과 같은 2/4/6초). 테스트가 줄인다.
	Backoff  func(attempt int) time.Duration
	Attempts int
	// Budget은 재시도를 포함한 종목 하나의 전체 조회 상한이다.
	Budget time.Duration
}

const maxChartBody = 32 << 20 // 10년 일봉 응답은 수 MB다. 비정상적으로 큰 응답은 거부한다.

func NewYahoo(timeout time.Duration, log *slog.Logger) *Yahoo {
	return &Yahoo{
		HTTP: &http.Client{
			Timeout: timeout,
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				if len(via) >= 3 || req.URL.Scheme != "https" {
					return errors.New("unexpected redirect")
				}
				return nil
			},
		},
		BaseURL:  "https://query2.finance.yahoo.com/v8/finance/chart/",
		Limiter:  rate.NewLimiter(rate.Limit(10), 10),
		Log:      log,
		Backoff:  func(attempt int) time.Duration { return time.Duration(2*attempt) * time.Second },
		Attempts: 3,
		Budget:   45 * time.Second,
	}
}

// requestBounds는 Yahoo 요청 구간이다. 끝은 배타적이고, 거래소 현지 날짜가 UTC 앞뒤로 걸칠 수 있어
// 시작 -1일, 끝 +2일을 더한다. 결과는 호출자가 요청 날짜로 다시 자른다.
func requestBounds(start, end civil.Date) (int64, int64) {
	return start.AddDays(-1).Time().Unix(), end.AddDays(2).Time().Unix()
}

func (y *Yahoo) Fetch(ctx context.Context, symbol string, start, end civil.Date) (History, error) {
	ctx, cancel := context.WithTimeout(ctx, y.Budget)
	defer cancel()
	p1, p2 := requestBounds(start, end)
	u := y.BaseURL + url.PathEscape(symbol) + "?" + url.Values{
		"period1":              {strconv.FormatInt(p1, 10)},
		"period2":              {strconv.FormatInt(p2, 10)},
		"interval":             {"1d"},
		"events":               {"div,splits"},
		"includeAdjustedClose": {"true"},
	}.Encode()

	var lastErr error
	for attempt := 1; attempt <= y.Attempts; attempt++ {
		if attempt > 1 {
			select {
			case <-ctx.Done():
				return History{}, y.timeoutError(ctx, symbol, lastErr)
			case <-time.After(y.Backoff(attempt - 1)):
			}
		}
		h, retry, err := y.fetchOnce(ctx, symbol, u)
		if err == nil {
			if len(h.Repaired) > 0 {
				y.Log.Warn("provider OHLC range repaired (G01)", "symbol", symbol, "dates", h.Repaired)
			}
			return h.Between(start, end), nil
		}
		lastErr = err
		if !retry {
			return History{}, err
		}
		y.Log.Warn("yahoo request failed, retrying", "symbol", symbol, "attempt", attempt, "error", err)
	}
	return History{}, lastErr
}

func (y *Yahoo) timeoutError(ctx context.Context, symbol string, last error) error {
	if errors.Is(ctx.Err(), context.Canceled) {
		return ctx.Err()
	}
	return apperr.Unavailable("%s: 시세 조회 시간이 초과되었습니다.", symbol).Wrap(last)
}

// fetchOnce는 한 번 요청한다. retry는 같은 요청을 다시 시도할 가치가 있는지(네트워크 오류, 5xx)다.
func (y *Yahoo) fetchOnce(ctx context.Context, symbol, u string) (History, bool, error) {
	if err := y.Limiter.Wait(ctx); err != nil {
		return History{}, false, y.timeoutError(ctx, symbol, err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return History{}, false, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (compatible; Backtest/1.7.10)")
	req.Header.Set("Accept", "application/json")
	resp, err := y.HTTP.Do(req)
	if err != nil {
		if ctx.Err() != nil {
			return History{}, false, y.timeoutError(ctx, symbol, err)
		}
		return History{}, true, apperr.Unavailable("%s: 시세 제공업체에 연결할 수 없습니다.", symbol).Wrap(err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(io.LimitReader(resp.Body, maxChartBody+1))
	if err != nil {
		return History{}, true, apperr.Unavailable("%s: 시세 응답을 읽을 수 없습니다.", symbol).Wrap(err)
	}
	if len(body) > maxChartBody {
		return History{}, false, apperr.Unavailable("%s: 시세 응답이 너무 큽니다.", symbol)
	}
	switch {
	case resp.StatusCode == http.StatusNotFound:
		return History{}, false, notFound(symbol)
	case resp.StatusCode == http.StatusTooManyRequests:
		return History{}, false, apperr.RateLimited("시세 제공업체의 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.")
	case resp.StatusCode >= 500:
		return History{}, true, apperr.Unavailable("%s: 시세 제공업체의 응답을 사용할 수 없습니다.", symbol).
			Wrap(fmt.Errorf("yahoo status %d", resp.StatusCode))
	case resp.StatusCode != http.StatusOK:
		return History{}, false, apperr.Unavailable("%s: 시세 제공업체의 응답을 사용할 수 없습니다.", symbol).
			Wrap(fmt.Errorf("yahoo status %d", resp.StatusCode))
	}
	h, err := ParseChart(symbol, body)
	return h, false, err
}
