// Package apperr는 HTTP 상태 코드로 바로 옮겨지는 애플리케이션 오류다.
//
// Python의 예외 → 상태 코드 매핑(app/api/v1/decorators.py)과 같은 분류를 쓴다:
//
//	Validation    422  요청 값이 잘못됨
//	NotFound      404  시세·데이터가 없음
//	RateLimited   429  외부 제공업체가 요청을 제한함 (Retry-After: 10)
//	Unavailable   503  외부 제공업체·DB를 지금 쓸 수 없음 (Retry-After: 30)
//
// Detail은 응답 본문 {"detail": ...}에 그대로 실리므로 내부 정보(호스트, SQL, 스택)를 넣지 않는다.
// 원인은 Err에 담아 로그로만 남긴다.
package apperr

import (
	"errors"
	"fmt"
	"net/http"
)

type Error struct {
	Status int
	Detail string
	Err    error
}

func (e *Error) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("%d %s: %v", e.Status, e.Detail, e.Err)
	}
	return fmt.Sprintf("%d %s", e.Status, e.Detail)
}

func (e *Error) Unwrap() error { return e.Err }

func newf(status int, format string, args ...any) *Error {
	return &Error{Status: status, Detail: fmt.Sprintf(format, args...)}
}

func Validation(format string, args ...any) *Error {
	return newf(http.StatusUnprocessableEntity, format, args...)
}
func NotFound(format string, args ...any) *Error { return newf(http.StatusNotFound, format, args...) }
func RateLimited(format string, args ...any) *Error {
	return newf(http.StatusTooManyRequests, format, args...)
}
func Unavailable(format string, args ...any) *Error {
	return newf(http.StatusServiceUnavailable, format, args...)
}

// Wrap은 원인 오류를 붙인다(로그용). 응답 본문에는 Detail만 나간다.
func (e *Error) Wrap(err error) *Error {
	c := *e
	c.Err = err
	return &c
}

// Status는 err 체인에서 *Error를 찾아 상태 코드를 돌려준다. 없으면 0.
func Status(err error) int {
	var e *Error
	if errors.As(err, &e) {
		return e.Status
	}
	return 0
}

func IsNotFound(err error) bool { return Status(err) == http.StatusNotFound }
