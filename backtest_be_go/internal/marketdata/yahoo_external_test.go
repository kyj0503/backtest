//go:build external

// 실제 Yahoo를 호출한다. CI에서는 돌리지 않는다:
//
//	docker run --rm backtest-be-go:test go test -tags external -run External -v ./internal/marketdata
package marketdata

import (
	"context"
	"testing"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

func TestExternalYahooFetch(t *testing.T) {
	y := NewYahoo(15*time.Second, quietLog)
	start, end := civil.MustParse("2024-01-02"), civil.MustParse("2024-03-28")
	for _, tc := range []struct {
		symbol, currency string
		minBars          int
	}{
		{"AAPL", "USD", 55},
		{"005930.KS", "KRW", 50},
		{"KRW=X", "KRW", 55},
		{"EURUSD=X", "USD", 55},
		{"BTC-USD", "USD", 85},
	} {
		h, err := y.Fetch(context.Background(), tc.symbol, start, end)
		if err != nil {
			t.Errorf("%s: %v", tc.symbol, err)
			continue
		}
		if h.Currency != tc.currency || len(h.Bars) < tc.minBars || h.Bars[0].Date < start || h.Bars[len(h.Bars)-1].Date > end {
			t.Errorf("%s: currency %s, %d bars %s..%s", tc.symbol, h.Currency, len(h.Bars), h.Bars[0].Date, h.Bars[len(h.Bars)-1].Date)
		}
		t.Logf("%s %s %d bars %s..%s first close %.4f listed %v", tc.symbol, h.Currency, len(h.Bars),
			h.Bars[0].Date, h.Bars[len(h.Bars)-1].Date, h.Bars[0].Close, h.FirstTradeDate)
	}
	if _, err := y.Fetch(context.Background(), "ZZZZNOTREAL", start, end); !isStatus(err, 404) {
		t.Errorf("unknown symbol: %v", err)
	}
}

func isStatus(err error, code int) bool { return status(err) == code }
