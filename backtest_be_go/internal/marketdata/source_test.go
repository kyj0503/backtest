package marketdata

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

type countingFetcher struct {
	data  Histories
	calls atomic.Int32
	delay time.Duration
	err   error
}

func (f *countingFetcher) Fetch(ctx context.Context, symbol string, start, end civil.Date) (History, error) {
	f.calls.Add(1)
	if f.delay > 0 {
		time.Sleep(f.delay)
	}
	if f.err != nil {
		return History{}, f.err
	}
	return NewFixtureFetcher(f.data).Fetch(ctx, symbol, start, end)
}

type memStore struct {
	mu      sync.Mutex
	saved   map[string]History
	saveErr error
	reads   int
	// round은 저장 시 DB 반올림을 흉내 낸다.
	round func(float64) float64
}

func (s *memStore) Cached(_ context.Context, symbol string, start, end civil.Date) (*History, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.reads++
	h, ok := s.saved[symbol]
	if !ok {
		return nil, nil
	}
	h = h.Between(start, end)
	return &h, nil
}

func (s *memStore) Save(_ context.Context, h History, _, _ civil.Date) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.saveErr != nil {
		return s.saveErr
	}
	if s.saved == nil {
		s.saved = map[string]History{}
	}
	c := h
	c.Bars = append([]Bar(nil), h.Bars...)
	if s.round != nil {
		for i := range c.Bars {
			c.Bars[i].Close = s.round(c.Bars[i].Close)
		}
	}
	s.saved[h.Symbol] = c
	return nil
}

func series(symbol, currency string, from string, n int, price float64) History {
	h := History{Symbol: symbol, Currency: currency}
	d := civil.MustParse(from)
	for i := range n {
		h.Bars = append(h.Bars, Bar{Date: d.AddDays(i), Open: price, High: price, Low: price, Close: price})
	}
	return h
}

var (
	d0 = civil.MustParse("2023-01-01")
	d9 = civil.MustParse("2023-01-10")
)

func TestConcurrentRequestsShareOneFetch(t *testing.T) {
	f := &countingFetcher{data: Histories{"AAPL": series("AAPL", "USD", "2023-01-01", 10, 100)}, delay: 20 * time.Millisecond}
	s := NewSource(f, nil, quietLog)
	var wg sync.WaitGroup
	for range 8 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, err := s.History(context.Background(), "AAPL", d0, d9); err != nil {
				t.Error(err)
			}
		}()
	}
	wg.Wait()
	if _, err := s.History(context.Background(), "AAPL", d0, d9); err != nil {
		t.Fatal(err)
	}
	if n := f.calls.Load(); n != 1 {
		t.Fatalf("fetched %d times", n)
	}
}

func TestSavedValuesAreReadBack(t *testing.T) {
	f := &countingFetcher{data: Histories{"AAPL": series("AAPL", "USD", "2023-01-01", 10, 100.123456789)}}
	store := &memStore{round: func(v float64) float64 { return float64(int(v*100)) / 100 }}
	s := NewSource(f, store, quietLog)
	h, err := s.History(context.Background(), "AAPL", d0, d9)
	if err != nil {
		t.Fatal(err)
	}
	if h.Bars[0].Close != 100.12 {
		t.Fatalf("first request must see the stored (rounded) value, got %v", h.Bars[0].Close)
	}
	// 새 Source(메모리 캐시 없음)도 DB에서 같은 값을 본다.
	s2 := NewSource(&countingFetcher{err: errors.New("must not fetch")}, store, quietLog)
	h2, err := s2.History(context.Background(), "AAPL", d0, d9)
	if err != nil || h2.Bars[0].Close != 100.12 {
		t.Fatalf("cache hit: %v %v", h2.Bars, err)
	}
}

func TestSaveFailureStillReturnsProviderData(t *testing.T) {
	f := &countingFetcher{data: Histories{"AAPL": series("AAPL", "USD", "2023-01-01", 10, 100)}}
	s := NewSource(f, &memStore{saveErr: errors.New("db down")}, quietLog)
	if h, err := s.History(context.Background(), "AAPL", d0, d9); err != nil || len(h.Bars) != 10 {
		t.Fatalf("%v %v", h, err)
	}
}

func TestInvalidProviderBarsAreRejected(t *testing.T) {
	bad := series("AAPL", "USD", "2023-01-01", 10, 100)
	bad.Bars[3].Low = 200 // 저가 > 고가
	s := NewSource(&countingFetcher{data: Histories{"AAPL": bad}}, nil, quietLog)
	if _, err := s.History(context.Background(), "AAPL", d0, d9); apperr.Status(err) != 503 {
		t.Fatalf("got %v", err)
	}
}

func TestLoadSkipsMissingSymbolsAndAddsFX(t *testing.T) {
	f := &countingFetcher{data: Histories{
		"AAPL":      series("AAPL", "USD", "2023-01-01", 10, 100),
		"005930.KS": series("005930.KS", "KRW", "2023-01-01", 10, 60000),
		"KRW=X":     series("KRW=X", "KRW", "2022-10-01", 110, 1300),
	}}
	s := NewSource(f, nil, quietLog)
	got, err := s.Load(context.Background(), []string{"AAPL", "ZZZZ", "005930.KS"}, d0, d9)
	if err != nil {
		t.Fatal(err)
	}
	if len(got.Missing) != 1 || got.Missing[0] != "ZZZZ" {
		t.Fatalf("missing %v", got.Missing)
	}
	fx, ok := got.Histories["KRW=X"]
	if !ok || fx.Bars[0].Date != d0.AddDays(-FXLookbackDays) {
		t.Fatalf("FX must start %d days early: %+v", FXLookbackDays, fx.Bars[:1])
	}
}

func TestLoadFailsOnUnsupportedCurrencyOrProviderError(t *testing.T) {
	f := &countingFetcher{data: Histories{"XYZ.T": series("XYZ.T", "ZAR", "2023-01-01", 10, 1)}}
	if _, err := NewSource(f, nil, quietLog).Load(context.Background(), []string{"XYZ.T"}, d0, d9); apperr.Status(err) != 422 {
		t.Fatalf("unsupported currency: %v", err)
	}
	f2 := &countingFetcher{err: apperr.RateLimited("slow down")}
	if _, err := NewSource(f2, nil, quietLog).Load(context.Background(), []string{"AAPL"}, d0, d9); apperr.Status(err) != 429 {
		t.Fatalf("rate limit: %v", err)
	}
}

func TestMemCacheDropsOtherRangesOfTheSameSymbol(t *testing.T) {
	c := memCache{ttl: time.Minute, cap: 2}
	c.put("AAPL", "a1", History{Symbol: "AAPL"})
	c.put("MSFT", "m1", History{Symbol: "MSFT"})
	c.put("AAPL", "a2", History{Symbol: "AAPL"})
	if _, ok := c.get("a1"); ok {
		t.Fatal("old AAPL range kept")
	}
	if _, ok := c.get("m1"); !ok {
		t.Fatal("other symbol evicted")
	}
	c.put("NVDA", "n1", History{})
	if len(c.entries) != 2 {
		t.Fatalf("cap exceeded: %d", len(c.entries))
	}
	now := time.Now()
	c.now = func() time.Time { return now.Add(2 * time.Minute) }
	if _, ok := c.get("n1"); ok {
		t.Fatal("expired entry returned")
	}
}
