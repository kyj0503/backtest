package marketdata

import (
	"context"
	"log/slog"
	"sort"
	"sync"
	"time"

	"golang.org/x/sync/errgroup"
	"golang.org/x/sync/singleflight"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Source는 시세 조회 진입점이다: 프로세스 메모리(5분) → MySQL 스냅샷(1시간) → 제공업체 순서로 본다.
type Source struct {
	Fetcher Fetcher
	Store   Store // nil이면 DB 캐시 없이 동작한다
	Log     *slog.Logger
	// FetchBudget은 한 종목 조회(캐시 저장 포함)의 상한이다. 조회는 첫 요청자의 context와 분리돼
	// 진행되므로(같은 종목을 기다리는 다른 요청이 있을 수 있다) 이 상한이 필요하다.
	FetchBudget time.Duration

	mem   memCache
	group singleflight.Group
}

func NewSource(f Fetcher, store Store, log *slog.Logger) *Source {
	return &Source{Fetcher: f, Store: store, Log: log, FetchBudget: 60 * time.Second,
		mem: memCache{ttl: 5 * time.Minute, cap: 128}}
}

// History는 [start, end]의 시세다. 데이터가 없으면 404 오류다.
func (s *Source) History(ctx context.Context, symbol string, start, end civil.Date) (History, error) {
	key := symbol + "|" + start.String() + "|" + end.String()
	if h, ok := s.mem.get(key); ok {
		return h, nil
	}
	ch := s.group.DoChan(key, func() (any, error) {
		fetchCtx, cancel := context.WithTimeout(context.WithoutCancel(ctx), s.FetchBudget)
		defer cancel()
		return s.load(fetchCtx, symbol, start, end)
	})
	select {
	case <-ctx.Done():
		return History{}, ctx.Err()
	case r := <-ch:
		if r.Err != nil {
			return History{}, r.Err
		}
		h := r.Val.(History)
		s.mem.put(symbol, key, h)
		return h, nil
	}
}

func (s *Source) load(ctx context.Context, symbol string, start, end civil.Date) (History, error) {
	if s.Store != nil {
		cached, err := s.Store.Cached(ctx, symbol, start, end)
		if err != nil {
			s.Log.Warn("price cache read failed", "symbol", symbol, "error", err)
		} else if cached != nil {
			return *cached, nil
		}
	}
	h, err := s.Fetcher.Fetch(ctx, symbol, start, end)
	if err != nil {
		return History{}, err
	}
	for _, b := range h.Bars {
		if !b.ValidFor(symbol) {
			return History{}, apperr.Unavailable("%s: 시세의 OHLC 값이 유효하지 않습니다.", symbol)
		}
	}
	h = h.Between(start, end)
	if len(h.Bars) == 0 {
		return History{}, notFound(symbol)
	}
	if s.Store == nil {
		return h, nil
	}
	if err := s.Store.Save(ctx, h, start, end); err != nil {
		// 캐시 저장 실패는 결과를 막지 않는다. 제공업체 값을 그대로 쓴다.
		s.Log.Warn("price cache write failed", "symbol", symbol, "error", err)
		return h, nil
	}
	// 저장된 값(DECIMAL 반올림 후)을 다시 읽어 첫 요청과 캐시 적중 요청이 같은 숫자를 보게 한다.
	if cached, err := s.Store.Cached(ctx, symbol, start, end); err == nil && cached != nil {
		return *cached, nil
	} else if err != nil {
		s.Log.Warn("price cache read-back failed", "symbol", symbol, "error", err)
	}
	return h, nil
}

// Loaded는 포트폴리오 시세 묶음이다. Missing은 제공업체에 데이터가 없는(404) 종목으로,
// 호출자가 경고와 함께 계산에서 뺀다(Python drop_unloaded_symbols와 같다).
type Loaded struct {
	Histories Histories
	Missing   []string
}

// Load는 종목들의 시세(최대 4개 동시)와 필요한 환율을 가져온다. 404가 아닌 오류는 전체 실패다.
// 환율은 시작일보다 FXLookbackDays 앞에서부터 가져와 시작일이 환율 휴장일이어도 직전 값이 있게 한다.
func (s *Source) Load(ctx context.Context, symbols []string, start, end civil.Date) (Loaded, error) {
	out := Loaded{Histories: Histories{}}
	var mu sync.Mutex
	g, gctx := errgroup.WithContext(ctx)
	g.SetLimit(4)
	for _, symbol := range symbols {
		g.Go(func() error {
			h, err := s.History(gctx, symbol, start, end)
			mu.Lock()
			defer mu.Unlock()
			switch {
			case apperr.IsNotFound(err):
				out.Missing = append(out.Missing, symbol)
				return nil
			case err != nil:
				return err
			}
			out.Histories[symbol] = h
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return Loaded{}, err
	}
	sort.Strings(out.Missing)

	currencies := map[string]bool{}
	for _, h := range out.Histories {
		if h.Currency != "USD" {
			currencies[h.Currency] = true
		}
	}
	for currency := range currencies {
		ticker, ok := FXTicker(currency)
		if !ok {
			return Loaded{}, apperr.Validation("지원하지 않거나 확인할 수 없는 통화: %s", currency)
		}
		h, err := s.History(ctx, ticker, start.AddDays(-FXLookbackDays), end)
		if err != nil {
			if apperr.IsNotFound(err) {
				return Loaded{}, apperr.Validation("%s: 환율 데이터를 가져올 수 없습니다.", currency).Wrap(err)
			}
			return Loaded{}, err
		}
		out.Histories[ticker] = h
	}
	return out, nil
}

// memCache는 짧은 프로세스 내 캐시다. 같은 종목의 다른 구간 항목은 새 항목을 넣을 때 지운다.
// 서로 다른 시점의 수정 주가 기준이 한 요청 안에서 섞이지 않게 하기 위해서다.
type memCache struct {
	mu      sync.Mutex
	ttl     time.Duration
	cap     int
	entries map[string]memEntry
	now     func() time.Time
}

type memEntry struct {
	symbol string
	at     time.Time
	h      History
}

func (c *memCache) clock() time.Time {
	if c.now != nil {
		return c.now()
	}
	return time.Now()
}

func (c *memCache) get(key string) (History, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.entries[key]
	if !ok || c.clock().Sub(e.at) >= c.ttl {
		return History{}, false
	}
	return e.h, true
}

func (c *memCache) put(symbol, key string, h History) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.entries == nil {
		c.entries = map[string]memEntry{}
	}
	now := c.clock()
	for k, e := range c.entries {
		if e.symbol == symbol || now.Sub(e.at) >= c.ttl {
			delete(c.entries, k)
		}
	}
	if len(c.entries) >= c.cap {
		var oldest string
		var at time.Time
		for k, e := range c.entries {
			if oldest == "" || e.at.Before(at) {
				oldest, at = k, e.at
			}
		}
		delete(c.entries, oldest)
	}
	c.entries[key] = memEntry{symbol: symbol, at: now, h: h}
}
