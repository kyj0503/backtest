//go:build diff

// rust-migration 구현과의 차등 비교(보조 검증). 합격 기준은 아니다(기준은 불변식 테스트).
// scripts/diff-rust-reference.sh가 rust 서버 응답을 모은 뒤 이 테스트를 돌린다:
//
//	DIFF_RUST_OUT=/w/rust-out.json go test -tags diff -run RustDiff -v ./internal/engine
package engine

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"sort"
	"strings"
	"testing"

	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
)

// 실행 시각처럼 결정적이지 않은 필드는 비교하지 않는다.
var nondeterministic = map[string]bool{"execution_time_seconds": true, "timestamp": true}

func TestRustDiff(t *testing.T) {
	path := os.Getenv("DIFF_RUST_OUT")
	if path == "" {
		t.Skip("DIFF_RUST_OUT not set")
	}
	var rust map[string]struct {
		Status int            `json:"status"`
		Body   map[string]any `json:"body"`
	}
	readJSON(t, path, &rust)
	var all marketdata.Histories
	readJSON(t, "../../testdata/rust/histories.json", &all)
	var cases []parityCase
	readJSON(t, "../../testdata/rust/parity.json", &cases)

	worst := map[string]float64{}
	for _, c := range cases {
		req := decodeRequest(t, c.Request)
		// rust 고정 시세 경로와 같게 자른다: 종목은 [시작, 끝], 환율은 [시작-60일, 끝].
		data := marketdata.Histories{}
		for sym, h := range all {
			if marketdata.IsFX(sym) {
				data[sym] = h.Between(req.StartDate.AddDays(-marketdata.FXLookbackDays), req.EndDate)
			} else {
				data[sym] = h.Between(req.StartDate, req.EndDate)
			}
		}
		d, err := Run(context.Background(), req, data, testLimits)
		if err != nil {
			t.Errorf("%s: go error %v", c.Name, err)
			continue
		}
		raw, _ := json.Marshal(Response{Status: "success", Data: d})
		var got map[string]any
		_ = json.Unmarshal(raw, &got)
		// 부가 데이터(include_*)는 API 계층이 붙인다. 엔진 비교에서는 뺀다.
		want := rust[c.Name].Body
		if data, ok := want["data"].(map[string]any); ok {
			for _, k := range SupplementalKeys {
				delete(data, k)
			}
		}
		var diffs []string
		compare("", got, want, &diffs, worst)
		for _, d := range diffs {
			t.Errorf("%s: %s", c.Name, d)
		}
	}
	keys := make([]string, 0, len(worst))
	for k := range worst {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		t.Logf("max relative difference %-40s %.3g", k, worst[k])
	}
}

func compare(path string, got, want any, diffs *[]string, worst map[string]float64) {
	if len(*diffs) > 20 {
		return
	}
	switch w := want.(type) {
	case map[string]any:
		g, ok := got.(map[string]any)
		if !ok {
			*diffs = append(*diffs, path+": go is not an object")
			return
		}
		for k := range w {
			if nondeterministic[k] {
				continue
			}
			if _, ok := g[k]; !ok {
				*diffs = append(*diffs, path+"."+k+": missing in go")
				continue
			}
			compare(path+"."+k, g[k], w[k], diffs, worst)
		}
		for k := range g {
			if _, ok := w[k]; !ok && !nondeterministic[k] {
				*diffs = append(*diffs, path+"."+k+": only in go")
			}
		}
	case []any:
		g, ok := got.([]any)
		if !ok || len(g) != len(w) {
			*diffs = append(*diffs, fmt.Sprintf("%s: array length go=%v rust=%d", path, lenOf(got), len(w)))
			return
		}
		for i := range w {
			compare(fmt.Sprintf("%s[%d]", path, i), g[i], w[i], diffs, worst)
		}
	case float64:
		g, ok := got.(float64)
		if !ok {
			*diffs = append(*diffs, fmt.Sprintf("%s: go=%v rust=%v", path, got, w))
			return
		}
		rel := math.Abs(g-w) / math.Max(1, math.Abs(w))
		field := path[strings.LastIndex(path, ".")+1:]
		if i := strings.Index(field, "["); i >= 0 {
			field = field[:i]
		}
		worst[field] = math.Max(worst[field], rel)
		if rel > 1e-9 {
			*diffs = append(*diffs, fmt.Sprintf("%s: go=%.15g rust=%.15g", path, g, w))
		}
	default:
		if fmt.Sprint(got) != fmt.Sprint(want) {
			*diffs = append(*diffs, fmt.Sprintf("%s: go=%v rust=%v", path, got, want))
		}
	}
}

func lenOf(v any) any {
	if a, ok := v.([]any); ok {
		return len(a)
	}
	return v
}
