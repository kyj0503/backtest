package api

import (
	"bytes"
	"encoding/json"
	"log/slog"
	"net/http"
)

// writeJSON은 FastAPI JSONResponse와 같은 형태로 쓴다: UTF-8 그대로(ensure_ascii=False),
// HTML 이스케이프 없음. 인코딩 실패(NaN 등)는 500으로 바꾼다. 응답을 버퍼에 먼저 만들어
// 상태 코드를 쓴 뒤에 실패하는 일이 없게 한다.
func writeJSON(w http.ResponseWriter, status int, v any) {
	var body []byte
	var err error
	if a, ok := v.(jsonAppender); ok {
		// 계산 응답은 전용 인코더로 바로 쓴다(engine/jsonenc.go). 출력은 아래 표준 경로와 같다.
		body, err = a.AppendJSON(make([]byte, 0, 64<<10))
		body = append(body, '\n')
	} else {
		var buf bytes.Buffer
		enc := json.NewEncoder(&buf)
		enc.SetEscapeHTML(false)
		err = enc.Encode(v)
		body = buf.Bytes()
	}
	if err != nil {
		slog.Error("response encoding failed", "error", err)
		body = []byte(`{"detail":"내부 서버 오류가 발생했습니다."}` + "\n")
		status = http.StatusInternalServerError
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write(body)
}

type jsonAppender interface {
	AppendJSON([]byte) ([]byte, error)
}

// errorBody는 FastAPI HTTPException과 같은 {"detail": ...} 형태다. detail은 문자열이거나
// 검증 오류 목록(422)일 수 있다.
type errorBody struct {
	Detail any `json:"detail"`
}

func writeError(w http.ResponseWriter, status int, detail any) {
	writeJSON(w, status, errorBody{Detail: detail})
}
