// Package news는 종목 뉴스(네이버 검색 OpenAPI)와 stock_news 3시간 캐시다.
package news

import (
	"context"
	"database/sql"
	_ "embed"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/kyj0503/backtest/backtest_be_go/internal/apperr"
)

//go:embed ticker_names.json
var tickerNamesJSON []byte

// TickerNames는 티커 → 한국어 회사명이다(Python app/constants/ticker_mapping.py). 뉴스 검색어와
// 지표 라벨 허용 목록에 쓴다.
var TickerNames = func() map[string]string {
	m := map[string]string{}
	if err := json.Unmarshal(tickerNamesJSON, &m); err != nil {
		panic(err)
	}
	return m
}()

// Query는 검색어다: "애플 주식", 한국 종목은 "삼성전자 주가".
func Query(symbol string) string {
	name, ok := TickerNames[symbol]
	if !ok {
		name = strings.TrimSuffix(symbol, ".KS")
	}
	if strings.HasSuffix(symbol, ".KS") {
		return name + " 주가"
	}
	return name + " 주식"
}

// Clean은 HTML 태그를 지우고 엔티티를 푼다(Python news_service.remove_html_tags와 같다).
//
//   - '<' 다음이 영문자, '/', '!', '?'이면 태그 시작으로 보고 '>'까지 지운다. 닫는 '>'가 없는 미종료
//     태그(`<img src=x onerror=alert(1)`)는 끝까지 버린다. 정규식 `<.*?>`는 이런 입력을 통과시켰다.
//   - 그 밖의 '<'(예: "10 < 20")는 글자로 남긴다.
//   - 엔티티는 두 번 푼다(Python HTMLParser의 convert_charrefs + html.unescape): "&amp;amp;" → "&".
//
// 결과는 프론트가 JSX 텍스트로만 렌더링한다(AGENTS 규칙 12).
func Clean(text string) string {
	var b strings.Builder
	for i := 0; i < len(text); {
		if text[i] == '<' && i+1 < len(text) && isTagStart(text[i+1]) {
			end := strings.IndexByte(text[i:], '>')
			if end < 0 {
				break
			}
			i += end + 1
			continue
		}
		b.WriteByte(text[i])
		i++
	}
	return html.UnescapeString(html.UnescapeString(b.String()))
}

func isTagStart(c byte) bool {
	return c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c == '/' || c == '!' || c == '?'
}

var excluded = regexp.MustCompile(`(?i)\[역사속 오늘|\[오늘의 역사|\[이날의 역사|\[역사 속 오늘|\[오늘 이런 일이|\[Today in History|` +
	`미리보는.*신문|내일 신문|석간.*신문|조간.*신문|부고.*별세|별세.*부고|오늘의 날씨|주요뉴스|뉴스픽|방송프로그램|` +
	`TV.*편성|라디오.*편성|오늘.*방송|오늘의.*운세|오늘의.*별자리|오늘의.*혈액형|스포츠.*결과|경기.*결과|` +
	`오늘의.*메뉴|오늘의.*퀴즈|이벤트.*당첨|공지사항|보도자료|광고.*안내`)

// Relevant는 종목과 무관한 정기 기사(오늘의 역사, 날씨, 운세 등)를 거른다.
func Relevant(title, description string) bool {
	return !excluded.MatchString(title + " " + description)
}

// Item은 응답의 뉴스 한 건이다(Python news_service와 같은 필드).
type Item struct {
	Title       string `json:"title"`
	Link        string `json:"link"`
	Description string `json:"description"`
	PubDate     string `json:"pubDate"`
}

type Service struct {
	ClientID, ClientSecret string
	DB                     *sql.DB // nil이면 캐시 없이 동작
	HTTP                   *http.Client
	Endpoint               string
	Log                    *slog.Logger
	MaxAge                 time.Duration
}

func NewService(id, secret string, db *sql.DB, log *slog.Logger) *Service {
	return &Service{ClientID: id, ClientSecret: secret, DB: db, Log: log, MaxAge: 3 * time.Hour,
		HTTP: &http.Client{Timeout: 10 * time.Second}, Endpoint: "https://openapi.naver.com/v1/search/news.json"}
}

// Latest는 최신 뉴스 limit건이다. DB 캐시(3시간) → 네이버 API 순서다. API 키가 없으면 빈 목록이다.
func (s *Service) Latest(ctx context.Context, symbol string, limit int) ([]Item, error) {
	if items, err := s.cached(ctx, symbol, limit); err != nil {
		s.Log.Warn("news cache read failed", "symbol", symbol, "error", err)
	} else if len(items) > 0 {
		return items, nil
	}
	if s.ClientID == "" || s.ClientSecret == "" {
		return []Item{}, nil
	}
	items, err := s.search(ctx, symbol, limit)
	if err != nil {
		return nil, err
	}
	s.save(ctx, symbol, items)
	return items, nil
}

func (s *Service) cached(ctx context.Context, symbol string, limit int) ([]Item, error) {
	if s.DB == nil {
		return nil, nil
	}
	rows, err := s.DB.QueryContext(ctx, `
		SELECT title, link, description, news_date FROM stock_news
		WHERE ticker = ? AND created_at >= UTC_TIMESTAMP() - INTERVAL ? SECOND
		ORDER BY news_date DESC, created_at DESC LIMIT ?`, symbol, int(s.MaxAge.Seconds()), limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Item
	for rows.Next() {
		var title string
		var link, desc sql.NullString
		var date string
		if err := rows.Scan(&title, &link, &desc, &date); err != nil {
			return nil, err
		}
		pub := date
		if d, err := time.Parse("2006-01-02", date); err == nil {
			// Python 캐시와 같은 표기(시각 정보는 저장하지 않는다)
			pub = d.Format("Mon, 02 Jan 2006 15:04:05") + " +0900"
		}
		out = append(out, Item{Title: title, Link: link.String, Description: desc.String, PubDate: pub})
	}
	return out, rows.Err()
}

func (s *Service) search(ctx context.Context, symbol string, limit int) ([]Item, error) {
	q := url.Values{"query": {Query(symbol)}, "display": {strconv.Itoa(limit)}, "sort": {"date"}}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, s.Endpoint+"?"+q.Encode(), nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Naver-Client-Id", s.ClientID)
	req.Header.Set("X-Naver-Client-Secret", s.ClientSecret)
	resp, err := s.HTTP.Do(req)
	if err != nil {
		return nil, apperr.Unavailable("뉴스 조회 실패").Wrap(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, apperr.Unavailable("뉴스 조회 실패").Wrap(fmt.Errorf("naver status %d", resp.StatusCode))
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if err != nil {
		return nil, apperr.Unavailable("뉴스 조회 실패").Wrap(err)
	}
	var result struct {
		Items []struct {
			Title       string `json:"title"`
			Link        string `json:"link"`
			Description string `json:"description"`
			PubDate     string `json:"pubDate"`
		} `json:"items"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, apperr.Unavailable("뉴스 응답 형식 오류").Wrap(err)
	}
	items := []Item{}
	for _, it := range result.Items {
		title, desc := Clean(it.Title), Clean(it.Description)
		if !Relevant(title, desc) {
			continue
		}
		items = append(items, Item{Title: title, Link: it.Link, Description: desc, PubDate: it.PubDate})
		if len(items) == limit {
			break
		}
	}
	return items, nil
}

// save는 캐시에 넣는다. 실패해도 결과에는 영향이 없다. 같은 (티커, 날짜, 링크)는 갱신한다.
func (s *Service) save(ctx context.Context, symbol string, items []Item) {
	if s.DB == nil {
		return
	}
	for _, it := range items {
		day := time.Now().UTC().Format("2006-01-02")
		if t, err := time.Parse(time.RFC1123Z, it.PubDate); err == nil {
			day = t.Format("2006-01-02") // 기사 현지(발행 시각대) 날짜
		}
		_, err := s.DB.ExecContext(ctx, `
			INSERT INTO stock_news (ticker, news_date, title, link, description, source)
			VALUES (?, ?, ?, ?, ?, 'naver') AS new
			ON DUPLICATE KEY UPDATE title = new.title, description = new.description, created_at = UTC_TIMESTAMP()`,
			symbol, day, truncate(it.Title, 500), truncate(it.Link, 1000), it.Description)
		if err != nil {
			s.Log.Warn("news cache write failed", "symbol", symbol, "error", err)
			return
		}
	}
}

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}
