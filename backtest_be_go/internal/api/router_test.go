package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"reflect"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
	"github.com/kyj0503/backtest/backtest_be_go/internal/monitoring"
)

type fakeProbe struct {
	ok     bool
	reason string
}

func (f fakeProbe) Check(context.Context) (bool, string) { return f.ok, f.reason }

var fixedNow = func() time.Time { return time.Date(2026, 11, 15, 10, 30, 0, 123456000, time.UTC) }

func newTestRouter(probe fakeProbe) http.Handler {
	return NewRouter(Deps{
		Config:  config.Config{},
		Log:     slog.New(slog.NewTextHandler(io.Discard, nil)),
		Metrics: monitoring.NewRegistry(),
		Ready:   probe,
		Now:     fixedNow,
	})
}

func do(t *testing.T, h http.Handler, method, path string) *httptest.ResponseRecorder {
	t.Helper()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(method, path, nil))
	return rec
}

func decode(t *testing.T, rec *httptest.ResponseRecorder) map[string]any {
	t.Helper()
	var body map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid JSON %q: %v", rec.Body.String(), err)
	}
	return body
}

func TestHealthIsLivenessOnly(t *testing.T) {
	// readiness가 실패해도 liveness는 200이어야 한다.
	rec := do(t, newTestRouter(fakeProbe{false, "unavailable"}), http.MethodGet, "/health")
	if rec.Code != http.StatusOK {
		t.Fatalf("status %d", rec.Code)
	}
	want := map[string]any{"status": "healthy", "timestamp": "2026-11-15T10:30:00.123456", "version": config.Version}
	if got := decode(t, rec); !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
	if ct := rec.Header().Get("Content-Type"); ct != "application/json" {
		t.Fatalf("content type %q", ct)
	}
}

func TestReadiness(t *testing.T) {
	cases := []struct {
		probe  fakeProbe
		status int
		state  string
	}{
		{fakeProbe{true, "ok"}, 200, "ready"},
		{fakeProbe{false, "timeout"}, 503, "not_ready"},
		{fakeProbe{false, "unavailable"}, 503, "not_ready"},
	}
	for _, tc := range cases {
		rec := do(t, newTestRouter(tc.probe), http.MethodGet, "/health/ready")
		if rec.Code != tc.status {
			t.Errorf("%s: status %d want %d", tc.probe.reason, rec.Code, tc.status)
		}
		body := decode(t, rec)
		if body["status"] != tc.state || !reflect.DeepEqual(body["checks"], map[string]any{"database": tc.probe.reason}) {
			t.Errorf("%s: body %v", tc.probe.reason, body)
		}
	}
}

func TestFastAPIStyleErrorsForUnknownRoutes(t *testing.T) {
	h := newTestRouter(fakeProbe{true, "ok"})
	if rec := do(t, h, http.MethodGet, "/api/v1/nope"); rec.Code != 404 || decode(t, rec)["detail"] != "Not Found" {
		t.Fatalf("404: %d %s", rec.Code, rec.Body)
	}
	if rec := do(t, h, http.MethodPost, "/health"); rec.Code != 405 || decode(t, rec)["detail"] != "Method Not Allowed" {
		t.Fatalf("405: %d %s", rec.Code, rec.Body)
	}
}

func TestRootRedirectsToDocs(t *testing.T) {
	rec := do(t, newTestRouter(fakeProbe{true, "ok"}), http.MethodGet, "/")
	if rec.Code != http.StatusTemporaryRedirect || rec.Header().Get("Location") != "/api/v1/docs" {
		t.Fatalf("got %d %q", rec.Code, rec.Header().Get("Location"))
	}
}

func TestDocsPagesPointAtOpenAPI(t *testing.T) {
	h := newTestRouter(fakeProbe{true, "ok"})
	for _, path := range []string{"/api/v1/docs", "/api/v1/redoc"} {
		rec := do(t, h, http.MethodGet, path)
		if rec.Code != 200 || !strings.Contains(rec.Body.String(), `"/api/v1/openapi.json"`) {
			t.Errorf("%s: %d", path, rec.Code)
		}
	}
}

func TestPanicBecomesGeneric500(t *testing.T) {
	h := recoverer(slog.New(slog.NewTextHandler(io.Discard, nil)))(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
		panic("secret internal state")
	}))
	rec := do(t, h, http.MethodGet, "/")
	if rec.Code != 500 || strings.Contains(rec.Body.String(), "secret") {
		t.Fatalf("got %d %s", rec.Code, rec.Body)
	}
}

func TestMetricsUseInstrumentatorNames(t *testing.T) {
	h := newTestRouter(fakeProbe{true, "ok"})
	do(t, h, http.MethodGet, "/health")
	do(t, h, http.MethodGet, "/api/v1/nope")
	body := do(t, h, http.MethodGet, "/metrics").Body.String()
	for _, want := range []string{
		`http_requests_total{handler="/health",method="GET",status="2xx"} 1`,
		`http_requests_total{handler="none",method="GET",status="4xx"} 1`,
		`http_request_duration_seconds_bucket{handler="/health",method="GET",le="0.1"}`,
		`http_request_duration_highr_seconds_count`,
		`http_response_size_bytes_count{handler="/health"} 1`,
	} {
		if !strings.Contains(body, want) {
			t.Errorf("metrics missing %q", want)
		}
	}
	if strings.Contains(body, `handler="/metrics"`) {
		t.Error("/metrics must not count itself")
	}
}

// documentation 필드를 지운 OpenAPI paths/components가 Python 시절 계약 스냅샷과 같아야 한다.
// test_api_contract.py와 같은 규칙이다(4개 GET 읽기 경로와 Turnstile 헤더/403은 추가분으로 허용).
func TestOpenAPIMatchesPythonContract(t *testing.T) {
	rec := do(t, newTestRouter(fakeProbe{true, "ok"}), http.MethodGet, "/api/v1/openapi.json")
	if rec.Code != 200 {
		t.Fatalf("status %d", rec.Code)
	}
	actual := decode(t, rec)
	raw, err := os.ReadFile("../../testdata/python/contract/api-contract.json")
	if err != nil {
		t.Fatal(err)
	}
	var expected map[string]any
	if err := json.Unmarshal(raw, &expected); err != nil {
		t.Fatal(err)
	}

	paths := actual["paths"].(map[string]any)
	for _, name := range []string{"prices", "exchange-rates", "benchmarks", "news"} {
		p := "/api/v1/" + name
		item, ok := paths[p].(map[string]any)
		if !ok || item["get"] == nil {
			t.Fatalf("missing GET %s", p)
		}
		delete(paths, p)
	}
	post := paths["/api/v1/backtest"].(map[string]any)["post"].(map[string]any)
	params := post["parameters"].([]any)
	if len(params) != 1 {
		t.Fatalf("parameters %v", params)
	}
	header := params[0].(map[string]any)
	if header["name"] != "X-Turnstile-Token" || header["in"] != "header" || header["required"] != false {
		t.Fatalf("turnstile header %v", header)
	}
	delete(post, "parameters")
	responses := post["responses"].(map[string]any)
	if forbidden, ok := responses["403"].(map[string]any); !ok || len(forbidden) != 1 || forbidden["description"] == nil {
		t.Fatalf("403 response %v", responses["403"])
	}
	delete(responses, "403")

	for _, section := range []string{"paths", "components"} {
		if diff := firstDiff(section, stripDocs(actual[section]), expected[section]); diff != "" {
			t.Errorf("differs from api-contract.json: %s", diff)
		}
	}
}

// firstDiff는 두 JSON 값의 첫 차이를 경로와 함께 돌려준다. 같으면 "".
func firstDiff(path string, got, want any) string {
	switch w := want.(type) {
	case map[string]any:
		g, ok := got.(map[string]any)
		if !ok {
			return path + ": not an object"
		}
		for k := range w {
			if _, ok := g[k]; !ok {
				return path + "." + k + ": missing"
			}
		}
		for k := range g {
			if _, ok := w[k]; !ok {
				return path + "." + k + ": unexpected"
			}
			if d := firstDiff(path+"."+k, g[k], w[k]); d != "" {
				return d
			}
		}
		return ""
	case []any:
		g, ok := got.([]any)
		if !ok || len(g) != len(w) {
			return path + ": array length differs"
		}
		for i := range w {
			if d := firstDiff(path+"["+strconv.Itoa(i)+"]", g[i], w[i]); d != "" {
				return d
			}
		}
		return ""
	}
	if !reflect.DeepEqual(got, want) {
		return path + ": got " + fmt.Sprint(got) + ", want " + fmt.Sprint(want)
	}
	return ""
}

var documentationKeys = map[string]bool{
	"description": true, "summary": true, "example": true, "examples": true,
	"title": true, "tags": true, "externalDocs": true,
}

func stripDocs(v any) any {
	switch x := v.(type) {
	case map[string]any:
		out := map[string]any{}
		for k, child := range x {
			if !documentationKeys[k] {
				out[k] = stripDocs(child)
			}
		}
		return out
	case []any:
		out := make([]any, len(x))
		for i, child := range x {
			out[i] = stripDocs(child)
		}
		return out
	}
	return v
}
