// Package monitoring은 Prometheus 지표를 정의한다.
//
// HTTP 지표의 이름·라벨·버킷은 Python의 prometheus_fastapi_instrumentator 기본값과 같다.
// 기존 Grafana 대시보드와 경보 규칙을 그대로 쓰기 위해서다.
package monitoring

import (
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/collectors"
)

// Registry는 이 프로세스의 지표 레지스트리다. 전역 DefaultRegisterer를 쓰지 않아 테스트가 서로 간섭하지 않는다.
type Registry struct {
	*prometheus.Registry
	http httpMetrics
}

type httpMetrics struct {
	requests     *prometheus.CounterVec
	requestSize  *prometheus.SummaryVec
	responseSize *prometheus.SummaryVec
	latency      *prometheus.HistogramVec
	latencyHighR prometheus.Histogram
}

func NewRegistry() *Registry {
	reg := prometheus.NewRegistry()
	reg.MustRegister(
		collectors.NewGoCollector(),
		collectors.NewProcessCollector(collectors.ProcessCollectorOpts{}),
	)
	m := httpMetrics{
		requests: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of requests by method, status and handler.",
		}, []string{"method", "status", "handler"}),
		requestSize: prometheus.NewSummaryVec(prometheus.SummaryOpts{
			Name: "http_request_size_bytes",
			Help: "Content length of incoming requests by handler. Only value of header is respected. Otherwise ignored.",
		}, []string{"handler"}),
		responseSize: prometheus.NewSummaryVec(prometheus.SummaryOpts{
			Name: "http_response_size_bytes",
			Help: "Content length of outgoing responses by handler. Only value of header is respected. Otherwise ignored.",
		}, []string{"handler"}),
		latency: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Latency with only few buckets by handler. Made to be only used if aggregation by handler is important.",
			Buckets: []float64{0.1, 0.5, 1},
		}, []string{"method", "handler"}),
		latencyHighR: prometheus.NewHistogram(prometheus.HistogramOpts{
			Name: "http_request_duration_highr_seconds",
			Help: "Latency with many buckets but no API specific labels. Made for more accurate percentile calculations.",
			Buckets: []float64{0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5,
				4, 4.5, 5, 7.5, 10, 30, 60},
		}),
	}
	reg.MustRegister(m.requests, m.requestSize, m.responseSize, m.latency, m.latencyHighR)
	return &Registry{Registry: reg, http: m}
}

// statusRecorder는 응답 상태와 크기를 기록한다.
type statusRecorder struct {
	http.ResponseWriter
	status    int
	bytes     int
	unmatched bool
}

// MarkUnmatched는 라우터의 NotFound/MethodNotAllowed 핸들러가 부른다. chi는 하위 라우터 안의
// 미등록 경로에 "/api/v1/*" 같은 패턴을 남기므로, 패턴만으로는 미등록 경로를 가려낼 수 없다.
func MarkUnmatched(w http.ResponseWriter) {
	for {
		switch x := w.(type) {
		case *statusRecorder:
			x.unmatched = true
			return
		case interface{ Unwrap() http.ResponseWriter }:
			w = x.Unwrap()
		default:
			return
		}
	}
}

func (w *statusRecorder) WriteHeader(code int) {
	if w.status == 0 {
		w.status = code
	}
	w.ResponseWriter.WriteHeader(code)
}

func (w *statusRecorder) Write(b []byte) (int, error) {
	if w.status == 0 {
		w.status = http.StatusOK
	}
	n, err := w.ResponseWriter.Write(b)
	w.bytes += n
	return n, err
}

func (w *statusRecorder) Unwrap() http.ResponseWriter { return w.ResponseWriter }

// InstrumentHTTP는 chi 라우터에 거는 미들웨어다. handler 라벨은 경로 템플릿이고,
// 등록되지 않은 경로는 라벨 폭발을 막기 위해 "none"으로 묶는다(instrumentator 기본 동작).
// status 라벨은 "2xx"처럼 묶는다.
func (r *Registry) InstrumentHTTP(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w}
		next.ServeHTTP(rec, req)

		handler := "none"
		if rc := chi.RouteContext(req.Context()); rc != nil && !rec.unmatched {
			if pattern := rc.RoutePattern(); pattern != "" {
				handler = pattern
			}
		}
		if handler == "/metrics" {
			return // instrumentator는 /metrics 자체를 세지 않는다
		}
		status := rec.status
		if status == 0 {
			status = http.StatusOK
		}
		elapsed := time.Since(start).Seconds()
		m := r.http
		m.requests.WithLabelValues(req.Method, strconv.Itoa(status/100)+"xx", handler).Inc()
		m.requestSize.WithLabelValues(handler).Observe(float64(max(req.ContentLength, 0)))
		m.responseSize.WithLabelValues(handler).Observe(float64(rec.bytes))
		m.latency.WithLabelValues(req.Method, handler).Observe(elapsed)
		m.latencyHighR.Observe(elapsed)
	})
}
