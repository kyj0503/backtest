package news

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

// Python news_service의 텍스트 정리·관련성 결과(testdata/rust/supplemental.json news_text)와 같아야 한다.
func TestCleanAndRelevantMatchPython(t *testing.T) {
	raw, err := os.ReadFile("../../testdata/rust/supplemental.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		NewsText []struct {
			Input    string `json:"input"`
			Clean    string `json:"clean"`
			Relevant bool   `json:"relevant"`
		} `json:"news_text"`
	}
	if err := json.Unmarshal(raw, &fixture); err != nil {
		t.Fatal(err)
	}
	for _, c := range fixture.NewsText {
		got := Clean(c.Input)
		if got != c.Clean {
			t.Errorf("Clean(%q) = %q, want %q", c.Input, got, c.Clean)
		}
		if Relevant(got, "") != c.Relevant {
			t.Errorf("Relevant(%q) = %v", got, !c.Relevant)
		}
	}
}

func TestQuery(t *testing.T) {
	for in, want := range map[string]string{"AAPL": "애플 주식", "005930.KS": "삼성전자 주가", "123456.KS": "123456 주가", "QQQ": "QQQ 주식"} {
		if got := Query(in); got != want {
			t.Errorf("%s: %s", in, got)
		}
	}
}

func TestSearchFiltersAndLimits(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Naver-Client-Id") != "id" || r.URL.Query().Get("query") != "애플 주식" {
			t.Errorf("bad request %v %v", r.Header, r.URL)
		}
		_, _ = w.Write([]byte(`{"items":[
			{"title":"<b>애플</b> 실적","link":"https://n/1","description":"좋음 &amp; 기대","pubDate":"Mon, 02 Jan 2023 09:00:00 +0900"},
			{"title":"[역사속 오늘] 애플","link":"https://n/2","description":"","pubDate":"Mon, 02 Jan 2023 08:00:00 +0900"},
			{"title":"애플 주가","link":"https://n/3","description":"","pubDate":"Mon, 02 Jan 2023 07:00:00 +0900"}]}`))
	}))
	defer srv.Close()
	s := NewService("id", "secret", nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	s.Endpoint = srv.URL
	items, err := s.Latest(context.Background(), "AAPL", 1)
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 1 || items[0].Title != "애플 실적" || items[0].Description != "좋음 & 기대" {
		t.Fatalf("%+v", items)
	}
	none, err := NewService("", "", nil, s.Log).Latest(context.Background(), "AAPL", 5)
	if err != nil || len(none) != 0 || none == nil {
		t.Fatalf("missing keys must give an empty list: %v %v", none, err)
	}
}
