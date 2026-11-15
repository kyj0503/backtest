// Package api는 HTTP 라우팅과 핸들러를 담는다.
package api

import (
	_ "embed"
	"fmt"
	"log/slog"
	"net/http"
	"runtime/debug"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
	"github.com/kyj0503/backtest/backtest_be_go/internal/health"
	"github.com/kyj0503/backtest/backtest_be_go/internal/monitoring"
)

//go:embed openapi.json
var openAPIDocument []byte

// Deps는 라우터가 쓰는 의존성이다. 테스트는 가짜 Probe를 넣는다.
type Deps struct {
	Config  config.Config
	Log     *slog.Logger
	Metrics *monitoring.Registry
	Ready   health.Probe
	Now     func() time.Time
}

func NewRouter(d Deps) http.Handler {
	if d.Now == nil {
		d.Now = time.Now
	}
	r := chi.NewRouter()
	r.Use(recoverer(d.Log))
	r.Use(d.Metrics.InstrumentHTTP)

	r.NotFound(func(w http.ResponseWriter, _ *http.Request) {
		monitoring.MarkUnmatched(w)
		writeError(w, http.StatusNotFound, "Not Found")
	})
	r.MethodNotAllowed(func(w http.ResponseWriter, _ *http.Request) {
		monitoring.MarkUnmatched(w)
		writeError(w, http.StatusMethodNotAllowed, "Method Not Allowed")
	})

	r.Get("/", func(w http.ResponseWriter, req *http.Request) {
		http.Redirect(w, req, config.APIPrefix+"/docs", http.StatusTemporaryRedirect)
	})
	r.Get("/health", d.health)
	r.Get("/health/ready", d.readiness)
	r.Method(http.MethodGet, "/metrics",
		promhttp.HandlerFor(d.Metrics, promhttp.HandlerOpts{Registry: d.Metrics}))

	r.Route(config.APIPrefix, func(api chi.Router) {
		api.Get("/openapi.json", func(w http.ResponseWriter, _ *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write(openAPIDocument)
		})
		api.Get("/docs", docsPage(swaggerHTML))
		api.Get("/redoc", docsPage(redocHTML))
	})
	return r
}

// timestamp는 Python datetime.now().isoformat()과 같은 모양(시간대 없는 로컬 시각, 마이크로초)이다.
func timestamp(t time.Time) string { return t.Format("2006-01-02T15:04:05.000000") }

type healthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version"`
}

type readinessResponse struct {
	Status    string            `json:"status"`
	Timestamp string            `json:"timestamp"`
	Version   string            `json:"version"`
	Checks    map[string]string `json:"checks"`
}

// health는 liveness다. DB나 외부 API를 보지 않는다. 재시작으로 고쳐지지 않는 의존성 장애를
// 여기 넣으면 DB가 내려갔을 때 멀쩡한 앱까지 재시작 대상이 된다.
func (d Deps) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, healthResponse{Status: "healthy", Timestamp: timestamp(d.Now()), Version: config.Version})
}

func (d Deps) readiness(w http.ResponseWriter, req *http.Request) {
	ok, reason := d.Ready.Check(req.Context())
	body := readinessResponse{
		Status: "ready", Timestamp: timestamp(d.Now()), Version: config.Version,
		Checks: map[string]string{"database": reason},
	}
	status := http.StatusOK
	if !ok {
		body.Status, status = "not_ready", http.StatusServiceUnavailable
	}
	writeJSON(w, status, body)
}

// recoverer는 패닉을 500으로 바꾼다. 응답 본문에는 내부 정보를 싣지 않는다.
// http.ErrAbortHandler는 net/http가 연결을 끊는 신호라 다시 던진다.
func recoverer(log *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			defer func() {
				if v := recover(); v != nil {
					if v == http.ErrAbortHandler {
						panic(v)
					}
					log.Error("unhandled panic", "panic", fmt.Sprint(v), "path", req.URL.Path, "stack", string(debug.Stack()))
					writeError(w, http.StatusInternalServerError, "내부 서버 오류가 발생했습니다.")
				}
			}()
			next.ServeHTTP(w, req)
		})
	}
}

func docsPage(html string) http.HandlerFunc {
	page := fmt.Sprintf(html, config.APIPrefix+"/openapi.json")
	return func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = w.Write([]byte(page))
	}
}

// FastAPI 기본 문서 페이지와 같은 구성이다(Swagger UI / ReDoc을 CDN에서 읽는다). 버전은 고정한다.
const swaggerHTML = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>라고할때살걸 - Swagger UI</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({url: %q, dom_id: "#swagger-ui", deepLinking: true, showExtensions: true, showCommonExtensions: true});
</script>
</body>
</html>
`

const redocHTML = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>라고할때살걸 - ReDoc</title>
<style>body { margin: 0; padding: 0; }</style>
</head>
<body>
<redoc spec-url=%q></redoc>
<script src="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js"></script>
</body>
</html>
`
