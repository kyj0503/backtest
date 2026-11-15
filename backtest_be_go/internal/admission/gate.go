// Package admission은 실행 슬롯(동시 실행 상한)과 클라이언트별 상한이다.
//
// Python은 uvicorn 워커 여러 개가 파일 잠금 슬롯을 공유했지만, Go 서버는 컨테이너당 프로세스 하나라
// 메모리 세마포어로 충분하다. 슬롯은 작업이 실제로 끝날 때(release 호출) 반환한다. 시간 초과로 응답을
// 먼저 돌려줘도 계산이 취소 신호를 보고 멈출 때까지 슬롯을 쥐고 있어 상한이 무력화되지 않는다.
package admission

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
)

type Gate struct {
	slots     chan struct{}
	mu        sync.Mutex
	clients   map[string]int
	perClient int
	total     int
	jobName   string
}

// New: total은 동시 실행 상한, perClient는 같은 클라이언트의 동시 요청(대기 포함) 상한(0 이하면 끔).
func New(total, perClient int, jobName string) *Gate {
	return &Gate{slots: make(chan struct{}, total), clients: map[string]int{}, perClient: perClient,
		total: total, jobName: jobName}
}

// Acquire는 슬롯을 얻는다. 반환된 release를 반드시 한 번 호출해야 한다.
//
//	429: 같은 클라이언트가 이미 perClient건 (대기열에 넣지 않고 즉시 거절, Retry-After 10)
//	503: 전체 대기열이 가득 찼거나 queue 시간 안에 슬롯을 얻지 못함
//	ctx 오류: 기다리는 동안 클라이언트가 끊음
func (g *Gate) Acquire(ctx context.Context, key string, queue time.Duration) (release func(), err error) {
	g.mu.Lock()
	inFlight := 0
	for _, n := range g.clients {
		inFlight += n
	}
	if inFlight >= g.total+64 {
		g.mu.Unlock()
		return nil, apperr.Unavailable("대기열이 가득 찼습니다.")
	}
	if g.perClient > 0 && g.clients[key] >= g.perClient {
		g.mu.Unlock()
		return nil, apperr.RateLimited("같은 클라이언트에서 이미 %d건의 %s가 실행 중입니다. 이전 요청이 끝난 뒤 다시 시도해주세요.",
			g.perClient, g.jobName)
	}
	g.clients[key]++
	g.mu.Unlock()

	leave := func() {
		g.mu.Lock()
		if g.clients[key]--; g.clients[key] <= 0 {
			delete(g.clients, key)
		}
		g.mu.Unlock()
	}
	timer := time.NewTimer(queue)
	defer timer.Stop()
	select {
	case g.slots <- struct{}{}:
	case <-timer.C:
		leave()
		return nil, apperr.Unavailable("실행 슬롯 대기 시간이 초과되었습니다.")
	case <-ctx.Done():
		leave()
		return nil, ctx.Err()
	}
	var once sync.Once
	return func() {
		once.Do(func() {
			<-g.slots
			leave()
		})
	}, nil
}

// Running은 슬롯을 쥔 작업 수, Waiting은 슬롯을 기다리는 요청 수다(/metrics 게이지).
func (g *Gate) Running() int { return len(g.slots) }

func (g *Gate) Waiting() int {
	g.mu.Lock()
	defer g.mu.Unlock()
	n := 0
	for _, c := range g.clients {
		n += c
	}
	return max(n-len(g.slots), 0)
}

func (g *Gate) String() string { return fmt.Sprintf("%s gate %d/%d", g.jobName, g.Running(), g.total) }
