package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"slices"
	"strings"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
	"github.com/kyj0503/backtest/backtest_be_go/internal/config"
)

// Turnstile은 Cloudflare Turnstile 서버 검증이다(Python app/api/v1/turnstile.py).
//
//	403: 토큰 없음·여러 개·2048자 초과, 또는 검증 실패(success/hostname/action 불일치)
//	503: 설정 불완전, Siteverify에 닿지 못함 또는 응답이 이상함
type Turnstile struct {
	cfg       config.Turnstile
	client    *http.Client
	verifyURL string
}

const siteverifyURL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

func NewTurnstile(cfg config.Turnstile) *Turnstile {
	return &Turnstile{cfg: cfg, client: &http.Client{Timeout: cfg.Timeout}, verifyURL: siteverifyURL}
}

var (
	errHumanRequired    = &apperr.Error{Status: http.StatusForbidden, Detail: "사람 인증이 필요하거나 만료되었습니다."}
	errHumanUnavailable = apperr.Unavailable("사람 인증을 확인할 수 없습니다.")
)

func (t *Turnstile) Verify(ctx context.Context, r *http.Request) error {
	if t == nil || !t.cfg.Enabled {
		return nil
	}
	if strings.TrimSpace(t.cfg.SecretKey) == "" || len(t.cfg.AllowedHostnames) == 0 || t.cfg.ExpectedAction == "" {
		return errHumanUnavailable
	}
	values := r.Header.Values("X-Turnstile-Token")
	if len(values) != 1 || strings.TrimSpace(values[0]) == "" || len(values[0]) > 2048 {
		return errHumanRequired
	}
	ctx, cancel := context.WithTimeout(ctx, t.cfg.Timeout+time.Second)
	defer cancel()
	form := url.Values{"secret": {t.cfg.SecretKey}, "response": {values[0]}}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, t.verifyURL, strings.NewReader(form.Encode()))
	if err != nil {
		return errHumanUnavailable.Wrap(err)
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := t.client.Do(req)
	if err != nil {
		return errHumanUnavailable.Wrap(err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(io.LimitReader(resp.Body, 16385))
	if err != nil || resp.StatusCode != http.StatusOK || len(body) > 16384 {
		return errHumanUnavailable
	}
	var result struct {
		Success  bool   `json:"success"`
		Hostname string `json:"hostname"`
		Action   string `json:"action"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return errHumanUnavailable.Wrap(err)
	}
	if !result.Success || result.Action != t.cfg.ExpectedAction || !slices.Contains(t.cfg.AllowedHostnames, result.Hostname) {
		return errHumanRequired
	}
	return nil
}
