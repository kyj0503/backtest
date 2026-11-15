package marketdata

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// FixtureFetcher는 testdata/rust/histories.json 형식의 고정 시세를 외부 조회 대신 돌려준다.
// E2E와 로컬 재현 전용이며 config가 DEBUG=true일 때만 허용한다.
type FixtureFetcher struct {
	data Histories
}

func LoadFixtures(path string) (*FixtureFetcher, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read fixture file: %w", err)
	}
	var data Histories
	if err := json.Unmarshal(raw, &data); err != nil {
		return nil, fmt.Errorf("parse fixture file %s: %w", path, err)
	}
	for symbol, h := range data {
		for _, b := range h.Bars {
			if !b.ValidFor(symbol) {
				return nil, fmt.Errorf("fixture %s has an invalid bar on %s", symbol, b.Date)
			}
		}
	}
	return &FixtureFetcher{data: data}, nil
}

func NewFixtureFetcher(data Histories) *FixtureFetcher { return &FixtureFetcher{data: data} }

func (f *FixtureFetcher) Fetch(_ context.Context, symbol string, start, end civil.Date) (History, error) {
	h, ok := f.data[symbol]
	if !ok {
		return History{}, notFound(symbol)
	}
	return h.Between(start, end), nil
}
