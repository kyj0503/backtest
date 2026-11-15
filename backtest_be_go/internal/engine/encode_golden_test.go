//go:build encodegolden

// 응답 직렬화를 바꿀 때 출력이 바이트 단위로 같은지 확인하는 일회성 도구다.
//
//	ENCODE_GOLDEN_DIR=/out ENCODE_GOLDEN_MODE=write go test -tags encodegolden -run EncodeGolden ./internal/engine
//	ENCODE_GOLDEN_DIR=/out ENCODE_GOLDEN_MODE=check go test -tags encodegolden -run EncodeGolden ./internal/engine
package engine

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

func TestEncodeGolden(t *testing.T) {
	dir, mode := os.Getenv("ENCODE_GOLDEN_DIR"), os.Getenv("ENCODE_GOLDEN_MODE")
	if dir == "" {
		t.Skip("ENCODE_GOLDEN_DIR not set")
	}
	var data marketdata.Histories
	readJSON(t, "../../testdata/rust/histories.json", &data)
	var cases []parityCase
	readJSON(t, "../../testdata/rust/parity.json", &cases)
	for _, c := range cases {
		d, err := Run(context.Background(), decodeRequest(t, c.Request), data, testLimits)
		if err != nil {
			t.Fatal(err)
		}
		// 실행 시각 필드는 매번 다르다.
		for _, k := range d.StrategyDetails.Keys() {
			v, _ := d.StrategyDetails.Get(k)
			if st, ok := v.(StrategyStats); ok {
				st.ExecutionTimeSeconds, st.Timestamp = 0, ""
				d.StrategyDetails.Set(k, st)
			}
		}
		d.Supplemental = map[string]json.RawMessage{"ticker_info": json.RawMessage(`{"A":{"x":"<&>"}}`), "supplemental_status": json.RawMessage(`{"news":"skipped"}`)}
		var buf bytes.Buffer
		enc := json.NewEncoder(&buf)
		enc.SetEscapeHTML(false)
		if err := enc.Encode(Response{Status: "success", Data: d}); err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(dir, c.Name+".json")
		if mode == "write" {
			if err := os.WriteFile(path, buf.Bytes(), 0o644); err != nil {
				t.Fatal(err)
			}
			continue
		}
		want, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(buf.Bytes(), want) {
			i := 0
			for i < len(want) && i < buf.Len() && want[i] == buf.Bytes()[i] {
				i++
			}
			lo := max(i-80, 0)
			t.Errorf("%s differs at byte %d:\n got  %s\n want %s", c.Name, i,
				buf.Bytes()[lo:min(i+80, buf.Len())], want[lo:min(i+80, len(want))])
		}
	}
}
