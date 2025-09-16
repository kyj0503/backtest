# 개발 가이드

이 문서는 백테스팅 시스템의 백엔드와 프론트엔드 개발에 필요한 모든 정보를 제공합니다.

## 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [백엔드 개발](#백엔드-개발)
3. [프론트엔드 개발](#프론트엔드-개발)
4. [아키텍처 개요](#아키텍처-개요)

## 개발 환경 설정

### 필수 요구사항
- Docker Desktop
- Git
- 선택사항: Node.js 20+, Python 3.11+ (로컬 개발용)

### 개발 환경 실행
```bash
# 개발 환경 시작
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 백그라운드 실행
docker compose -f compose.yml -f compose/compose.dev.yml up -d

# 특정 서비스만 재시작
docker compose -f compose.yml -f compose/compose.dev.yml restart backend

# 시스템 종료
docker compose -f compose.yml -f compose/compose.dev.yml down
```

### 환경변수 설정
프로젝트 루트에 `.env` 파일을 생성하여 필요한 환경변수를 설정하세요:

```bash
# 데이터베이스
DATABASE_URL=mysql+pymysql://root:password@mysql:3306/stock_data_cache

# CORS 설정 (개발용)
BACKEND_CORS_ORIGINS=["http://localhost:5174","http://localhost:3000"]

# 네이버 뉴스 API (선택)
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

## 백엔드 개발

### 기술 스택
- **FastAPI**: 고성능 API 프레임워크
- **Pydantic v2**: 데이터 검증 및 직렬화
- **SQLAlchemy**: ORM 및 데이터베이스 연동
- **MySQL**: 주가 데이터 캐시
- **backtesting.py**: 백테스트 엔진
- **uv**: Python 패키지 관리 (pip 대체)

### 디렉터리 구조
```
backend/
├── app/
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── core/                # 설정 및 예외 처리
│   ├── api/v1/              # API 라우터 및 엔드포인트
│   ├── models/              # Pydantic 모델 (요청/응답)
│   ├── services/            # 비즈니스 로직
│   ├── repositories/        # 데이터 액세스 계층
│   ├── domains/             # DDD 도메인 모델 (점진 도입)
│   ├── events/              # 이벤트 시스템
│   └── utils/               # 유틸리티 함수
├── tests/                   # 테스트 코드
└── requirements.txt         # 의존성 목록
```

### 로컬 개발 실행
```bash
# 컨테이너 내부에서 개발 서버 실행
docker compose exec backend python run_server.py

# 또는 로컬에서 직접 실행 (의존성 설치 필요)
cd backend
uv pip install --system -r requirements.txt
python run_server.py
```

#### 주요 API 엔드포인트

#### 백테스트 API
- `POST /api/v1/backtest/run` - 단일 종목 백테스트 실행
- `POST /api/v1/backtest/chart-data` - 백테스트 + 차트 데이터
- `POST /api/v1/backtest/portfolio` - 포트폴리오 백테스트

#### 인증 및 커뮤니티 API
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `GET /api/v1/community/posts` - 게시글 목록
- `POST /api/v1/community/posts` - 게시글 작성

#### 기타 API
- `GET /api/v1/strategies/` - 전략 목록
- `GET /api/v1/naver-news/search` - 뉴스 검색
- `WS /api/v1/chat/ws/{room}` - 실시간 채팅

### 데이터베이스 스키마
시스템은 두 개의 분리된 데이터베이스를 사용합니다:

1. **Community DB** (`database/schema.sql`)
   - 사용자 인증 및 세션 관리
   - 커뮤니티 게시글/댓글/좋아요
   - 백테스트 히스토리

2. **Stock Data Cache DB** (`database/yfinance.sql`)
   - 주식 기본 정보 및 일별 가격
   - 배당금 및 주식 분할 데이터
   - 환율 정보

### 에러 처리 및 로깅
- 전역 예외 핸들러로 일관된 에러 응답
- 사용자 친화적 메시지와 디버그용 에러 ID 제공
- 구조화된 로깅으로 추적 가능한 로그 기록

## 프론트엔드 개발

### 기술 스택
- **React 18**: 함수형 컴포넌트 및 훅 기반
- **TypeScript**: 정적 타입 검사
- **Vite**: 빠른 개발 서버 및 빌드
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **shadcn/ui**: 재사용 가능한 UI 컴포넌트 라이브러리
- **Recharts**: 데이터 시각화
- **React Router v6**: 라우팅

### 디렉터리 구조
```
frontend/src/
├── pages/                   # 페이지 컴포넌트
├── components/              # 재사용 가능한 UI 컴포넌트
│   ├── ui/                  # shadcn/ui 컴포넌트
│   ├── common/              # 공통 컴포넌트
│   ├── results/             # 백테스트 결과 컴포넌트
│   └── volatility/          # 변동성/뉴스 컴포넌트
├── hooks/                   # 커스텀 훅
├── contexts/                # React 컨텍스트
├── services/                # API 클라이언트
├── types/                   # TypeScript 타입 정의
├── utils/                   # 유틸리티 함수
├── lib/                     # shadcn/ui 유틸리티
└── constants/               # 상수 정의
```

### 로컬 개발 실행
```bash
# 컨테이너 내부에서 개발 서버 실행
docker compose exec frontend npm run dev

# 또는 로컬에서 직접 실행
cd frontend
npm ci
npm run dev
```

### 주요 페이지 및 기능

#### 홈페이지 (`/`)
- 프로젝트 소개 및 주요 기능 안내
- 빠른 시작 가이드

#### 백테스트 페이지 (`/backtest`)
- 통합 백테스트 폼
  - 포트폴리오 구성 (종목/현금, 투자방식, 금액)
  - 날짜 범위 및 전략 선택
  - 수수료 및 리밸런싱 설정
- 결과 표시
  - 성과 지표 요약
  - OHLC 및 수익률 차트
  - 거래 내역 및 보조 지표
  - 단일/포트폴리오 결과 화면은 `SectionCard` 기반 2열 그리드로 동일한 구성(요약 → 차트 → 뉴스/환율)을 유지하며, 벤치마크와 거래 신호는 데이터가 있을 때만 추가 카드로 노출됩니다.

#### 커뮤니티 페이지 (`/community`)
- 게시글 목록 및 상세 보기
- 댓글 시스템 및 좋아요 기능
- 로그인 사용자만 작성 가능

### 상태 관리
- 로컬 상태 우선: 컴포넌트 및 훅 단위로 관리
- 커스텀 훅으로 로직 분리 및 재사용
- Context API는 최소한으로 사용

### UI 컴포넌트 (shadcn/ui)

프로젝트는 일관성 있는 디자인과 접근성을 위해 shadcn/ui를 사용합니다.

#### 설치된 컴포넌트
- **Button**: 기본 버튼 컴포넌트
- **Input**: 입력 필드
- **Card**: 카드 레이아웃 (Header, Content, Title, Description)
- **Badge**: 상태 표시 뱃지
- **Select**: 드롭다운 선택
- **Dialog**: 모달 창 (Modal 대체)
- **Tooltip**: 툴팁 (FinancialTermTooltip 등에 사용)
- **Popover**: 팝오버

#### 사용 예시
```typescript
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export function ExampleComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>백테스트 설정</CardTitle>
        <CardDescription>투자 전략을 설정하세요</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input placeholder="종목 심볼 입력" />
        <Button onClick={handleSubmit}>백테스트 실행</Button>
      </CardContent>
    </Card>
  )
}
```

#### 새 컴포넌트 추가
```bash
# 도커 컨테이너 내에서 shadcn/ui 컴포넌트 추가
docker compose exec frontend npx shadcn-ui@latest add [컴포넌트명]

# 예: Table 컴포넌트 추가
docker compose exec frontend npx shadcn-ui@latest add table
```

### API 연동
```typescript
// API 클라이언트 예시
import { BacktestApiService } from '@/services/api';

const apiService = new BacktestApiService();

// 백테스트 실행
const result = await apiService.runBacktest(request);

// 포트폴리오 백테스트
const portfolioResult = await apiService.runPortfolioBacktest(request);
```

## 아키텍처 개요

### 시스템 구조
```
Frontend (React)  ←→  Backend (FastAPI)  ←→  Database (MySQL)
       ↓                     ↓                    ↓
   Vite + Tailwind     backtesting.py        yfinance API
```

### Domain-Driven Design (DDD)
현재 부분적으로 적용 중이며, 점진적으로 확장하고 있습니다:

- **서비스 계층**: 현재 주요 비즈니스 로직 담당
- **도메인 계층**: 값 객체와 엔티티 점진 도입
- **이벤트 시스템**: 선택적 기능에서 사용
- **CQRS 패턴**: 명령/쿼리 분리 구조 마련

### 데이터 흐름
1. 프론트엔드에서 API 요청
2. FastAPI가 요청 검증 및 라우팅
3. 서비스 계층에서 비즈니스 로직 처리
4. 리포지토리를 통한 데이터 액세스
5. 결과를 JSON으로 직렬화하여 응답

### 데이터 소스 전략
- **DB 캐시 우선**: MySQL에 저장된 데이터 우선 사용
- **외부 API 보강**: 누락된 데이터는 yfinance에서 조회
- **자동 캐싱**: 조회된 데이터는 자동으로 DB에 저장

### 현금 자산 처리
- 무위험 자산으로 간주 (0% 수익률, 무변동성)
- 포트폴리오에서 리스크 완충 역할
- 리밸런싱 시 현금 비중 유지

### 테스트 전략
- **단위 테스트**: 개별 함수/클래스 검증
- **통합 테스트**: 서비스 간 연동 검증
- **E2E 테스트**: 전체 시스템 시나리오 검증
- **모킹**: 외부 의존성 최소화

자세한 테스트 가이드는 [TESTING_GUIDE.md](TESTING_GUIDE.md)를 참고하세요.
