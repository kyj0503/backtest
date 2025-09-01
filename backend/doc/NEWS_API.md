# 뉴스 API 사용 가이드

## 개요

주식의 급등/급락 시점과 관련된 뉴스를 조회하는 API입니다. 여러 뉴스 소스를 통합하여 관련성 높은 뉴스를 제공합니다.

## API 엔드포인트

### 1. 특정 날짜 뉴스 조회

```
GET /api/v1/news/news/{ticker}/{date}?threshold=5.0
```

**매개변수:**
- `ticker` (path): 주식 티커 (예: AAPL, GOOGL)
- `date` (path): 조회할 날짜 (YYYY-MM-DD 형식)
- `threshold` (query, 선택사항): 급등/급락 기준 퍼센트 (기본값: 5.0)

**응답 예시:**
```json
{
  "status": "success",
  "message": "AAPL의 2024-01-15 뉴스 3건을 조회했습니다.",
  "data": {
    "ticker": "AAPL",
    "date": "2024-01-15",
    "price_change_percent": 7.2,
    "is_significant_move": true,
    "threshold": 5.0,
    "news_count": 3,
    "news": [
      {
        "title": "Apple Reports Record Q4 Earnings",
        "description": "Apple Inc. reported better-than-expected earnings...",
        "url": "https://example.com/news/1",
        "source": "Financial Times",
        "published_at": "2024-01-15T10:30:00Z",
        "api_source": "news_api"
      }
    ],
    "available_apis": ["news_api", "alpha_vantage"]
  }
}
```

### 2. 뉴스 API 테스트

```
GET /api/v1/news/news/test
```

API 연결 상태와 설정을 확인할 수 있습니다.

**응답 예시:**
```json
{
  "status": "success",
  "available_apis": ["news_api", "finnhub"],
  "news_api_key_set": true,
  "alpha_vantage_key_set": false,
  "finnhub_key_set": true,
  "test_result": {
    "ticker": "AAPL",
    "news_count": 5
  }
}
```

## 환경변수 설정

뉴스 API를 사용하려면 다음 환경변수를 설정해야 합니다:

```bash
# .env 파일
NEWS_API_KEY=your_news_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FINNHUB_API_KEY=your_finnhub_key_here
```

### API 키 발급 방법

1. **News API** (추천)
   - 웹사이트: https://newsapi.org/
   - 무료 플랜: 1,000 requests/month
   - 비용: 무료 ~ $449/month

2. **Alpha Vantage**
   - 웹사이트: https://www.alphavantage.co/
   - 무료 플랜: 25 requests/day
   - 비용: 무료 ~ $49.99/month

3. **Finnhub**
   - 웹사이트: https://finnhub.io/
   - 무료 플랜: 60 requests/minute
   - 비용: 무료 ~ $99/month

## 지원하는 뉴스 소스

### News API
- 범용 뉴스 검색
- 키워드 기반 필터링
- 날짜 범위 지정 가능
- 다양한 언어 지원

### Alpha Vantage News & Sentiment
- 주식 전문 뉴스
- 감정 분석 점수 제공
- 티커별 뉴스 분류
- 제한적이지만 정확한 데이터

### Finnhub Stock News
- 실시간 주식 뉴스
- 기업별 뉴스 분류
- 높은 업데이트 빈도
- 간결한 요약 제공

## 사용 예시

### Python 클라이언트

```python
import requests

# 기본 뉴스 조회
response = requests.get(
    "http://localhost:8001/api/v1/news/news/AAPL/2024-01-15",
    params={"threshold": 3.0}
)

if response.status_code == 200:
    data = response.json()
    news_items = data["data"]["news"]
    for news in news_items:
        print(f"제목: {news['title']}")
        print(f"출처: {news['source']}")
        print(f"URL: {news['url']}")
        print("---")
```

### JavaScript/Frontend

```javascript
const fetchNews = async (ticker, date, threshold = 5.0) => {
  try {
    const response = await fetch(
      `/api/v1/news/news/${ticker}/${date}?threshold=${threshold}`
    );
    
    if (!response.ok) {
      throw new Error('뉴스 조회 실패');
    }
    
    const data = await response.json();
    return data.data.news;
  } catch (error) {
    console.error('뉴스 조회 오류:', error);
    return [];
  }
};

// 사용 예시
fetchNews('AAPL', '2024-01-15', 5.0)
  .then(news => {
    news.forEach(item => {
      console.log(`${item.title} - ${item.source}`);
    });
  });
```

## 에러 처리

### 일반적인 에러 코드

- `422`: 잘못된 날짜 형식
- `500`: 내부 서버 오류 (API 연결 실패 등)

### 에러 응답 예시

```json
{
  "detail": "올바른 날짜 형식(YYYY-MM-DD)을 입력해주세요."
}
```

## 성능 고려사항

1. **API 제한**: 각 뉴스 API는 요청 제한이 있으므로 과도한 호출 주의
2. **응답 시간**: 외부 API 호출로 인해 응답 시간이 다소 소요될 수 있음
3. **폴백 메커니즘**: 하나의 API가 실패해도 다른 API로 자동 전환
4. **중복 제거**: 동일한 뉴스는 자동으로 중복 제거됨

## 향후 개발 계획

1. **MySQL 캐싱**: 조회된 뉴스를 DB에 저장하여 중복 API 호출 방지
2. **감정 분석**: 뉴스 내용의 긍정/부정 감정 분석
3. **실시간 알림**: 급등/급락 시 실시간 뉴스 알림
4. **다국어 지원**: 한국어 뉴스 소스 추가

## 문제해결

### 뉴스가 조회되지 않는 경우

1. API 키 설정 확인
2. 인터넷 연결 상태 확인
3. API 할당량 초과 여부 확인
4. 티커 심볼 정확성 확인

### 로그 확인

```bash
# Docker 환경에서 로그 확인
docker-compose logs backend | grep news

# 로컬 환경에서 로그 확인
tail -f backend.log | grep news
```
