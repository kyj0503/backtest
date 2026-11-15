package marketdata

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync/atomic"
	"testing"
	"time"

	"golang.org/x/time/rate"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

var quietLog = slog.New(slog.NewTextHandler(io.Discard, nil))

func testYahoo(t *testing.T, handler http.HandlerFunc) (*Yahoo, *atomic.Int32) {
	t.Helper()
	var calls atomic.Int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		handler(w, r)
	}))
	t.Cleanup(srv.Close)
	y := NewYahoo(5*time.Second, quietLog)
	y.BaseURL = srv.URL + "/v8/finance/chart/"
	y.Limiter = rate.NewLimiter(rate.Inf, 1)
	y.Backoff = func(int) time.Duration { return time.Millisecond }
	return y, &calls
}

func TestYahooRequestAndRangeTrim(t *testing.T) {
	body := newChart("UTC", days("2023-01-01", 10)).bytes(t)
	y, _ := testYahoo(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v8/finance/chart/TEST" {
			t.Errorf("path %s", r.URL.Path)
		}
		q := r.URL.Query()
		start := civil.MustParse("2023-01-03").AddDays(-1).Time().Unix()
		end := civil.MustParse("2023-01-05").AddDays(2).Time().Unix()
		if q.Get("period1") != strconv.FormatInt(start, 10) || q.Get("period2") != strconv.FormatInt(end, 10) ||
			q.Get("interval") != "1d" || q.Get("includeAdjustedClose") != "true" {
			t.Errorf("query %v", q)
		}
		if r.Header.Get("User-Agent") == "" {
			t.Error("missing user agent")
		}
		_, _ = w.Write(body)
	})
	h, err := y.Fetch(context.Background(), "TEST", civil.MustParse("2023-01-03"), civil.MustParse("2023-01-05"))
	if err != nil {
		t.Fatal(err)
	}
	if len(h.Bars) != 3 || h.Bars[0].Date.String() != "2023-01-03" || h.Bars[2].Date.String() != "2023-01-05" {
		t.Fatalf("not trimmed to the requested dates: %+v", h.Bars)
	}
}

func TestYahooStatusMapping(t *testing.T) {
	cases := []struct {
		status    int
		wantCode  int
		wantCalls int32
	}{
		{404, 404, 1},
		{429, 429, 1},
		{401, 503, 1},
		{502, 503, 3}, // 5xx는 재시도한다
	}
	for _, tc := range cases {
		y, calls := testYahoo(t, func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(tc.status) })
		_, err := y.Fetch(context.Background(), "TEST", civil.MustParse("2023-01-03"), civil.MustParse("2023-01-05"))
		if status(err) != tc.wantCode || calls.Load() != tc.wantCalls {
			t.Errorf("HTTP %d: got %v after %d calls", tc.status, err, calls.Load())
		}
	}
}

func TestYahooRetriesThenSucceeds(t *testing.T) {
	body := newChart("UTC", days("2023-01-01", 10)).bytes(t)
	var n atomic.Int32
	y, calls := testYahoo(t, func(w http.ResponseWriter, _ *http.Request) {
		if n.Add(1) < 3 {
			w.WriteHeader(http.StatusServiceUnavailable)
			return
		}
		_, _ = w.Write(body)
	})
	if _, err := y.Fetch(context.Background(), "TEST", civil.MustParse("2023-01-03"), civil.MustParse("2023-01-05")); err != nil {
		t.Fatal(err)
	}
	if calls.Load() != 3 {
		t.Fatalf("calls %d", calls.Load())
	}
}

func TestYahooHonoursCancellation(t *testing.T) {
	y, _ := testYahoo(t, func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() })
	ctx, cancel := context.WithCancel(context.Background())
	go func() { time.Sleep(20 * time.Millisecond); cancel() }()
	_, err := y.Fetch(ctx, "TEST", civil.MustParse("2023-01-03"), civil.MustParse("2023-01-05"))
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("got %v", err)
	}
}

func TestYahooBudgetIsUnavailable(t *testing.T) {
	y, _ := testYahoo(t, func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() })
	y.Budget = 30 * time.Millisecond
	_, err := y.Fetch(context.Background(), "TEST", civil.MustParse("2023-01-03"), civil.MustParse("2023-01-05"))
	if status(err) != 503 {
		t.Fatalf("got %v", err)
	}
}
