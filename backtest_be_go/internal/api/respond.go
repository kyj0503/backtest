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
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		slog.Error("response encoding failed", "error", err)
		buf.Reset()
		buf.WriteString(`{"detail":"내부 서버 오류가 발생했습니다."}` + "\n")
		status = http.StatusInternalServerError
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write(buf.Bytes())
}

// errorBody는 FastAPI HTTPException과 같은 {"detail": ...} 형태다. detail은 문자열이거나
// 검증 오류 목록(422)일 수 있다.
type errorBody struct {
	Detail any `json:"detail"`
}

func writeError(w http.ResponseWriter, status int, detail any) {
	writeJSON(w, status, errorBody{Detail: detail})
}
