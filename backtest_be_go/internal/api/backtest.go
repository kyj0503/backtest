package api

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"
	"unicode/utf8"

	"github.com/kyj0503/backtest/backtest_be_go/internal/admission"
	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
	"github.com/kyj0503/backtest/backtest_be_go/internal/engine"
	"github.com/kyj0503/backtest/backtest_be_go/internal/marketdata"
	"github.com/kyj0503/backtest/backtest_be_go/internal/monitoring"
	"github.com/kyj0503/backtest/backtest_be_go/internal/news"
)

// Service는 계산·참고 조회 엔드포인트의 의존성이다.
type Service struct {
	Cfg       config.Config
	Log       *slog.Logger
	App       *monitoring.App
	Source    *marketdata.Source
	News      *news.Service
	Turnstile *Turnstile
	Calc      *admission.Gate
	Reads     *admission.Gate
	// Today는 "미래 종료일" 검사의 기준 날짜다. 서비스 사용자가 한국에 있어, 한국 날짜가 UTC보다 하루
	// 앞서는 00~09시(KST)에 오늘 종료일이 거부되던 문제를 막으려고 Asia/Seoul 날짜를 쓴다.
	Today func() civil.Date
}

var seoul = func() *time.Location {
	l, err := time.LoadLocation("Asia/Seoul")
	if err != nil {
		return time.FixedZone("KST", 9*3600)
	}
	return l
}()

func SeoulToday() civil.Date { return civil.Of(time.Now().In(seoul)) }

func (s *Service) limits() engine.Limits {
	return engine.Limits{MinPeriodDays: s.Cfg.MinBacktestPeriodDays, MaxPeriodDays: s.Cfg.MaxBacktestDurationDays,
		MaxItems: s.Cfg.MaxPortfolioItems, MaxSymbolLen: s.Cfg.MaxSymbolLength, Today: s.Today()}
}

const maxBody = 64 << 10

// statusClientClosed는 nginx가 "클라이언트가 먼저 끊음"에 쓰는 비표준 코드다. 응답은 아무도 받지 않는다.
const statusClientClosed = 499

func (s *Service) backtest(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	if err := s.Turnstile.Verify(ctx, r); err != nil {
		s.writeErr(w, err)
		return
	}
	body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, maxBody))
	if err != nil {
		s.writeErr(w, &apperr.Error{Status: http.StatusRequestEntityTooLarge, Detail: "요청 본문이 너무 큽니다."})
		return
	}
	// encoding/json은 깨진 UTF-8을 U+FFFD로 바꿔 받아들인다. Python(Starlette)은 본문 해석 단계에서
	// 400으로 거부했다. 현금 항목 이름 등이 조용히 깨진 채 계산되지 않게 원본과 같이 거부한다.
	if !utf8.Valid(body) {
		s.writeErr(w, &apperr.Error{Status: http.StatusBadRequest, Detail: "There was an error parsing the body"})
		return
	}
	req, err := parseBacktest(body, s.limits())
	if err != nil {
		s.writeErr(w, err)
		return
	}
	release, err := s.Calc.Acquire(ctx, clientKey(r, s.Cfg.TrustedProxies), s.Cfg.BacktestQueueTimeout)
	if err != nil {
		if ctx.Err() != nil {
			w.WriteHeader(statusClientClosed)
			return
		}
		s.writeErr(w, err)
		return
	}
	defer release()

	for _, a := range req.Portfolio {
		if !a.Cash() {
			s.App.RecordTicker(a.Symbol)
		}
	}
	began := time.Now()
	jobCtx, cancel := context.WithTimeout(ctx, s.Cfg.BacktestTimeout)
	defer cancel()
	d, loaded, err := s.compute(jobCtx, req)
	elapsed := time.Since(began).Seconds()
	s.App.ObserveStage("simulation", elapsed)
	if err != nil {
		s.App.Executions.WithLabelValues(req.Strategy, "error").Inc()
		switch {
		case ctx.Err() != nil:
			w.WriteHeader(statusClientClosed)
		case errors.Is(err, context.DeadlineExceeded):
			s.writeErr(w, &apperr.Error{Status: http.StatusGatewayTimeout, Detail: "백테스트 실행 시간이 초과되었습니다."})
		default:
			s.writeErr(w, err)
		}
		return
	}
	s.App.Executions.WithLabelValues(req.Strategy, "success").Inc()
	s.App.Processing.WithLabelValues(req.Strategy).Observe(elapsed)
	release() // 부가 데이터는 계산 슬롯을 쥐지 않는다
	s.supplemental(ctx, req, d, loaded)
	writeJSON(w, http.StatusOK, engine.Response{Status: "success", Data: d})
}

func (s *Service) compute(ctx context.Context, req engine.Request) (*engine.Data, marketdata.Histories, error) {
	var symbols []string
	for _, a := range req.Portfolio {
		if !a.Cash() {
			symbols = append(symbols, a.Symbol)
		}
	}
	loaded, err := s.Source.Load(ctx, symbols, req.StartDate, req.EndDate)
	if err != nil {
		return nil, nil, err
	}
	d, err := engine.Run(ctx, req, loaded.Histories, s.limits())
	return d, loaded.Histories, err
}

// read는 참고 조회 GET이다. 계산과 별도의 슬롯(동시 4건)을 쓴다.
func (s *Service) read(section string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		q, err := parseReadQuery(section, r.URL.RawQuery, s.limits())
		if err != nil {
			s.writeErr(w, err)
			return
		}
		ctx := r.Context()
		release, err := s.Reads.Acquire(ctx, clientKey(r, s.Cfg.TrustedProxies), s.Cfg.MarketDataQueueTimeout)
		if err != nil {
			if ctx.Err() != nil {
				w.WriteHeader(statusClientClosed)
				return
			}
			s.writeErr(w, err)
			return
		}
		defer release()
		jobCtx, cancel := context.WithTimeout(ctx, s.Cfg.MarketDataTimeout)
		defer cancel()
		res := s.reference(jobCtx, section, q)
		if ctx.Err() != nil {
			w.WriteHeader(statusClientClosed)
			return
		}
		if errors.Is(jobCtx.Err(), context.DeadlineExceeded) {
			s.writeErr(w, &apperr.Error{Status: http.StatusGatewayTimeout, Detail: "참고 데이터 조회 시간이 초과되었습니다."})
			return
		}
		var data engine.Ordered[any]
		for _, k := range sectionFields[section] {
			data.Set(k, res.Fields[k])
		}
		if section == "benchmarks" {
			data.Set("sp500_total_return_pct", res.SP500TotalReturn)
		}
		var st engine.Ordered[string]
		for _, k := range sectionStatuses[section] {
			st.Set(k, res.Status[k])
		}
		data.Set("supplemental_status", st)
		var resp engine.Ordered[any]
		resp.Set("status", "success")
		resp.Set("data", data)
		writeJSON(w, http.StatusOK, resp)
	}
}

// writeErr는 오류를 FastAPI와 같은 본문으로 쓴다. 분류되지 않은 오류는 내부 정보 없이 오류 ID만 준다.
func (s *Service) writeErr(w http.ResponseWriter, err error) {
	var ve validationErrors
	if errors.As(err, &ve) {
		writeError(w, http.StatusUnprocessableEntity, []fieldError(ve))
		return
	}
	var ae *apperr.Error
	if errors.As(err, &ae) {
		switch ae.Status {
		case http.StatusTooManyRequests:
			w.Header().Set("Retry-After", "10")
		case http.StatusServiceUnavailable:
			w.Header().Set("Retry-After", "30")
		}
		if ae.Err != nil {
			s.Log.Warn("request failed", "status", ae.Status, "detail", ae.Detail, "cause", ae.Err)
		}
		writeError(w, ae.Status, ae.Detail)
		return
	}
	id := newErrorID()
	s.Log.Error("unhandled error", "error_id", id, "error", err)
	writeError(w, http.StatusInternalServerError, fmt.Sprintf("포트폴리오 처리 중 오류가 발생했습니다. (오류 ID: %s)", id))
}

func newErrorID() string {
	var b [16]byte
	_, _ = rand.Read(b[:])
	b[6] = b[6]&0x0f | 0x40
	b[8] = b[8]&0x3f | 0x80
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}

// marshal은 HTML 이스케이프 없이 JSON으로 만든다.
func marshal(v any) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	return bytes.TrimRight(buf.Bytes(), "\n"), nil
}
