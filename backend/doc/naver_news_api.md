# 네이버 뉴스 API 가이드

## 개요

네이버 검색 API를 활용하여 주식 투자와 관련된 뉴스를 검색하고 제공하는 서비스입니다. 종목별, 날짜별 뉴스 검색과 함께 불필요한 콘텐츠 필터링 및 네트워크 안정성을 보장합니다.

## 주요 특징

- **70+ 종목 지원**: 한국 40+개, 미국 30+개 주요 종목
- **스마트 검색**: 종목 코드를 회사명으로 자동 변환
- **날짜별 필터링**: 특정 날짜 범위의 뉴스만 조회
- **콘텐츠 정제**: 불필요한 역사/부고/날씨 뉴스 자동 제거
- **네트워크 안정성**: 3회 재시도 + 지수 백오프

## API 엔드포인트

### 1. 기본 뉴스 검색

```http
GET /api/v1/naver-news/search?query={검색어}&display={결과수}
```

**사용 예시:**
```bash
curl "http://localhost:8001/api/v1/naver-news/search?query=삼성전자&display=10"
```

### 2. 종목별 뉴스 검색

```http
GET /api/v1/naver-news/ticker/{ticker}?display={결과수}
```

**사용 예시:**
```bash
# 삼성전자 뉴스
curl "http://localhost:8001/api/v1/naver-news/ticker/005930.KS"

# 애플 뉴스
curl "http://localhost:8001/api/v1/naver-news/ticker/AAPL"
```

### 3. 날짜별 뉴스 검색

```http
GET /api/v1/naver-news/search-by-date?query={검색어}&start_date={시작일}&end_date={종료일}
```

**사용 예시:**
```bash
# 특정 날짜의 삼성전자 뉴스
curl "http://localhost:8001/api/v1/naver-news/search-by-date?query=삼성전자&start_date=2025-09-01"

# 날짜 범위 검색
curl "http://localhost:8001/api/v1/naver-news/search-by-date?query=테슬라&start_date=2025-08-30&end_date=2025-09-01"
```

### 4. 종목별 날짜 뉴스 검색

```http
GET /api/v1/naver-news/ticker/{ticker}/date?start_date={시작일}&end_date={종료일}
```

**사용 예시:**
```bash
# 삼성전자의 특정 날짜 뉴스
curl "http://localhost:8001/api/v1/naver-news/ticker/005930.KS/date?start_date=2025-09-01"
```

## 지원 종목 목록

### 한국 주요 종목 (40+개)

#### 삼성 계열
- `005930.KS`: 삼성전자
- `006400.KS`: 삼성SDI
- `207940.KS`: 삼성바이오로직스
- `028260.KS`: 삼성물산
- `009150.KS`: 삼성전기
- `018260.KS`: 삼성에스디에스
- `032830.KS`: 삼성생명

#### SK 계열
- `000660.KS`: SK하이닉스
- `096770.KS`: SK이노베이션
- `017670.KS`: SK텔레콤
- `034730.KS`: SK

#### LG 계열
- `051910.KS`: LG화학
- `373220.KS`: LG에너지솔루션
- `066570.KS`: LG전자
- `003550.KS`: LG

#### 금융
- `055550.KS`: 신한지주
- `105560.KS`: KB금융
- `086790.KS`: 하나금융지주
- `316140.KS`: 우리금융지주

#### 자동차
- `005380.KS`: 현대차
- `000270.KS`: 기아
- `012330.KS`: 현대모비스

#### IT/게임
- `035420.KS`: NAVER
- `035720.KS`: 카카오
- `323410.KS`: 카카오뱅크
- `036570.KS`: 엔씨소프트
- `251270.KS`: 넷마블

#### 기타 주요 종목
- `030200.KS`: KT
- `015760.KS`: 한국전력
- `068270.KS`: 셀트리온
- `003670.KS`: 포스코퓨처엠
- `009540.KS`: HD한국조선해양
- `033780.KS`: KT&G
- `090430.KS`: 아모레퍼시픽
- `180640.KS`: 한진칼
- `128940.KS`: 한미약품
- `047050.KS`: 포스코인터내셔널
- `010950.KS`: S-Oil

### 미국 주요 종목 (30+개)

#### 빅테크
- `AAPL`: 애플
- `MSFT`: 마이크로소프트
- `GOOGL`: 구글
- `AMZN`: 아마존
- `META`: 메타
- `NFLX`: 넷플릭스

#### 반도체
- `NVDA`: 엔비디아
- `AMD`: AMD
- `INTC`: 인텔

#### 전기차
- `TSLA`: 테슬라
- `RIVN`: 리비안
- `LCID`: 루시드

#### 소프트웨어
- `CRM`: 세일즈포스
- `ORCL`: 오라클
- `ADBE`: 어도비
- `OKTA`: 옥타
- `DDOG`: 데이터독
- `SNOW`: 스노우플레이크
- `PLTR`: 팔란티어

#### 핀테크
- `PYPL`: 페이팔
- `SQ`: 스퀘어
- `COIN`: 코인베이스

#### 소셜/엔터
- `SNAP`: 스냅챗
- `SPOT`: 스포티파이
- `PINS`: 핀터레스트
- `RBLX`: 로블록스

#### 기타
- `UBER`: 우버
- `ZOOM`: 줌
- `SHOP`: 쇼피파이
- `ROKU`: 로쿠
- `DOCU`: 도큐사인
- `U`: 유니티

## 응답 형식

모든 API는 동일한 구조의 JSON 응답을 반환합니다:

```json
{
  "status": "success",
  "message": "설명 메시지",
  "data": {
    "query": "실제 검색어",
    "ticker": "종목코드 (해당시)",
    "start_date": "시작일 (날짜 검색시)",
    "end_date": "종료일 (날짜 검색시)",
    "total_count": 10,
    "news_list": [
      {
        "title": "뉴스 제목 (HTML 태그 제거됨)",
        "link": "뉴스 링크",
        "description": "뉴스 내용 요약 (HTML 태그 제거됨)",
        "pubDate": "Mon, 01 Sep 2025 21:01:00 +0900"
      }
    ]
  }
}
```

## 필터링 규칙

다음과 같은 불필요한 콘텐츠는 자동으로 필터링됩니다:

### 제외되는 뉴스 패턴
- `[역사속 오늘]`, `[오늘의 역사]` 등 역사 관련 기사
- `부고`, `별세` 관련 기사
- `오늘의 날씨`, `오늘의 운세` 등 일상 정보
- `주요뉴스`, `뉴스픽` 등 종합 뉴스
- `방송프로그램`, `TV 편성` 등 방송 관련
- `스포츠 결과`, `경기 결과` 등 스포츠 뉴스
- `공지사항`, `보도자료`, `광고 안내` 등 홍보성 콘텐츠

## 환경 설정

### 환경 변수

```bash
# backend/.env
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
```

### 네이버 검색 API 신청

1. [네이버 개발자 센터](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. 검색 API 서비스 선택
4. Client ID와 Client Secret 발급

## 에러 처리

### 일반적인 에러 상황

1. **API 키 미설정**
   ```json
   {
     "detail": "네이버 API 키가 설정되지 않았습니다."
   }
   ```

2. **네트워크 연결 오류**
   ```json
   {
     "detail": "네트워크 연결 실패 (최대 재시도 초과): ..."
   }
   ```

3. **잘못된 날짜 형식**
   ```json
   {
     "detail": "날짜는 YYYY-MM-DD 형식으로 입력해주세요."
   }
   ```

### 네트워크 안정성

- **최대 재시도**: 3회
- **지수 백오프**: 1초 → 2초 → 4초
- **타임아웃**: 10초
- **지원 오류**: URLError, socket.gaierror, socket.timeout

## 개발 가이드

### 새 종목 추가

새로운 종목을 지원하려면 `backend/app/api/v1/endpoints/naver_news.py`의 `ticker_mapping` 딕셔너리에 추가하세요:

```python
ticker_mapping = {
    # 기존 종목들...
    "NEW_TICKER": "새로운_회사명",
}
```

### 필터링 규칙 수정

불필요한 뉴스 패턴을 추가하려면 `is_relevant_news` 메소드의 `exclude_patterns` 리스트를 수정하세요:

```python
exclude_patterns = [
    # 기존 패턴들...
    r'새로운_필터_패턴',
]
```

### 테스트

```bash
# API 연결 테스트
curl "http://localhost:8001/api/v1/naver-news/test"

# 특정 종목 테스트
curl "http://localhost:8001/api/v1/naver-news/ticker/005930.KS"
```

## 주의사항

1. **API 사용량**: 네이버 검색 API는 일일 호출 제한이 있습니다
2. **검색 품질**: 회사명 기반 검색으로 더 정확한 결과를 제공합니다
3. **날짜 제한**: 너무 오래된 날짜의 뉴스는 검색되지 않을 수 있습니다
4. **실시간성**: 뉴스 데이터는 네이버 검색 결과에 따라 지연될 수 있습니다

## 업데이트 내역

- **v1.0** (2025-09-01): 네이버 뉴스 검색 API 최초 구현
  - 기본 뉴스 검색
  - 종목별 뉴스 검색
  - 날짜별 필터링
  - 콘텐츠 정제 및 네트워크 안정성 확보
