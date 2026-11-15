package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// BenchmarkScenarios는 3자 벤치마크(.comparison/bench-3way)와 같은 시세·요청으로 HTTP 핸들러 전체
// (디코딩 → 시세 로드 → 계산 → JSON)를 잰다. 입력 디렉터리는 저장소에 없으므로 BENCH_INPUTS가 있을 때만 돈다:
//
//	BENCH_INPUTS=/inputs go test -run x -bench Scenarios -benchmem ./internal/api
func BenchmarkScenarios(b *testing.B) {
	root := os.Getenv("BENCH_INPUTS")
	if root == "" {
		b.Skip("BENCH_INPUTS not set")
	}
	raw, err := os.ReadFile(filepath.Join(root, "prices.json"))
	if err != nil {
		b.Fatal(err)
	}
	var h marketdata.Histories
	if err := json.Unmarshal(raw, &h); err != nil {
		b.Fatal(err)
	}
	cfg := testConfig(b)
	_, handler := newTestService(b, marketdata.NewFixtureFetcher(h), cfg)
	for _, name := range []string{"usd_single", "usd_five_8years", "dca_monthly_1", "rebalance_monthly_1", "sma_default", "macd_default"} {
		in, err := os.ReadFile(filepath.Join(root, "normal", name, "input.json"))
		if err != nil {
			b.Fatal(err)
		}
		var c struct {
			Body json.RawMessage `json:"body"`
		}
		if err := json.Unmarshal(in, &c); err != nil {
			b.Fatal(err)
		}
		body := string(c.Body)
		b.Run(name, func(b *testing.B) {
			for b.Loop() {
				rec := httptest.NewRecorder()
				req := httptest.NewRequest(http.MethodPost, "/api/v1/backtest", strings.NewReader(body))
				handler.ServeHTTP(rec, req)
				if rec.Code != 200 {
					b.Fatalf("%d %s", rec.Code, rec.Body.String()[:200])
				}
			}
		})
	}
}
