// Package health는 /health/ready가 쓰는 DB readiness 프로브를 제공한다.
//
// liveness(/health)는 프로세스 생존만 보고, readiness는 "지금 요청을 처리할 수 있는가"를 본다.
// 백테스트는 시세 캐시를 MySQL에서 읽으므로 DB 연결이 조건이다. Yahoo/Naver 같은 외부 API는
// 넣지 않는다. 외부 장애가 배포 실패로 번지면 안 된다.
//
// 운영 연결 풀을 쓰지 않는다. 풀이 요청으로 가득 차면 "바쁨"과 "DB에 닿을 수 없음"이 구분되지
// 않기 때문이다. 매 프로브는 짧은 드라이버 타임아웃을 건 새 연결로 접속·인증까지 확인한다.
package health

import (
	"context"
	"database/sql"
	"errors"
	"log/slog"
	"time"

	"golang.org/x/sync/singleflight"
)

const (
	ReasonOK          = "ok"
	ReasonTimeout     = "timeout"
	ReasonUnavailable = "unavailable"
)

// Probe는 readiness 검사 결과(준비 여부, 사유)를 돌려준다.
type Probe interface {
	Check(ctx context.Context) (ready bool, reason string)
}

// DBProbe는 MySQL `SELECT 1` 프로브다. 동시에 여러 번 호출돼도 실제 접속은 한 번만 진행한다
// (single-flight). DB가 멈춘 상태에서 readiness를 반복 호출해도 멈춘 연결은 최대 1개다.
type DBProbe struct {
	open    func() (*sql.DB, error)
	timeout time.Duration
	group   singleflight.Group
	log     *slog.Logger
}

// NewDBProbe의 open은 프로브 전용 *sql.DB를 만든다. 드라이버 타임아웃은 timeout과 같게 걸어 둔다.
func NewDBProbe(open func() (*sql.DB, error), timeout time.Duration, log *slog.Logger) *DBProbe {
	return &DBProbe{open: open, timeout: timeout, log: log}
}

func (p *DBProbe) Check(ctx context.Context) (bool, string) {
	ctx, cancel := context.WithTimeout(ctx, p.timeout)
	defer cancel()
	// 공유 프로브는 호출자 context와 분리한다. 한 호출자가 먼저 빠져도 다른 호출자는 같은 결과를 기다린다.
	result := p.group.DoChan("db", func() (any, error) { return nil, p.run() })
	select {
	case <-ctx.Done():
		p.log.Warn("readiness: DB probe did not finish in time", "timeout", p.timeout)
		return false, ReasonTimeout
	case r := <-result:
		if r.Err != nil {
			// 드라이버 오류에는 호스트·사용자명이 들어 있을 수 있어 응답이 아니라 로그로만 남긴다.
			p.log.Warn("readiness: DB probe failed", "error", r.Err)
			if errors.Is(r.Err, context.DeadlineExceeded) {
				return false, ReasonTimeout
			}
			return false, ReasonUnavailable
		}
		return true, ReasonOK
	}
}

func (p *DBProbe) run() error {
	db, err := p.open()
	if err != nil {
		return err
	}
	if db == nil {
		return errors.New("probe opener returned no database handle")
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(0)
	// 드라이버 타임아웃과 별개로 프로브 전체에도 상한을 둔다(여유 1초).
	ctx, cancel := context.WithTimeout(context.Background(), p.timeout+time.Second)
	defer cancel()
	var one int
	return db.QueryRowContext(ctx, "SELECT 1").Scan(&one)
}
