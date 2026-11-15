package health

import (
	"context"
	"database/sql"
	"errors"
	"io"
	"log/slog"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

var quiet = slog.New(slog.NewTextHandler(io.Discard, nil))

func TestOpenFailureIsUnavailable(t *testing.T) {
	p := NewDBProbe(func() (*sql.DB, error) { return nil, errors.New("dial tcp 10.0.0.5: refused") },
		time.Second, quiet)
	if ok, reason := p.Check(context.Background()); ok || reason != ReasonUnavailable {
		t.Fatalf("got %v %q", ok, reason)
	}
}

func TestSlowProbeTimesOutAndIsShared(t *testing.T) {
	var opens atomic.Int32
	release := make(chan struct{})
	p := NewDBProbe(func() (*sql.DB, error) {
		opens.Add(1)
		<-release
		return nil, errors.New("late")
	}, 50*time.Millisecond, quiet)

	var wg sync.WaitGroup
	for range 5 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if ok, reason := p.Check(context.Background()); ok || reason != ReasonTimeout {
				t.Errorf("got %v %q", ok, reason)
			}
		}()
	}
	wg.Wait()
	close(release)
	if n := opens.Load(); n != 1 {
		t.Fatalf("concurrent checks opened %d probes, want 1 (single-flight)", n)
	}
}

func TestCallerCancellationIsReportedAsTimeout(t *testing.T) {
	block := make(chan struct{})
	defer close(block)
	p := NewDBProbe(func() (*sql.DB, error) { <-block; return nil, nil }, time.Minute, quiet)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if ok, reason := p.Check(ctx); ok || reason != ReasonTimeout {
		t.Fatalf("got %v %q", ok, reason)
	}
}
