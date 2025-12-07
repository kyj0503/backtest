# 트레이딩 전략 백테스팅 플랫폼

**개인 맞춤형 트레이딩 전략 백테스팅 플랫폼입니다.**

이 프로젝트는 주식, 암호화폐 등 다양한 자산에 대한 투자 전략을 과거 데이터로 검증하고, 포트폴리오의 성과를 분석하여 데이터 기반의 합리적인 의사결정을 돕기 위해 개발되었습니다.

## 주요 기능

-   **단일 종목 백테스트**: 특정 종목에 대해 하나의 투자 전략(예: SMA, RSI)을 적용하여 성과를 분석합니다.
-   **포트폴리오 백테스트**: 여러 자산을 조합한 포트폴리오의 과거 성과를 시뮬레이션합니다.
-   **자산 분배 전략**: 정적 가중치, 동적 가중치 등 다양한 자산 분배 전략을 테스트합니다.
-   **정기 투자 (DCA) 시뮬레이션**: 적립식 투자(Cost Averaging) 전략의 성과를 분석합니다.
-   **리밸런싱 전략**: 주기적인 자산 비중 조절(리밸런싱) 효과를 검증합니다.
-   **상세 분석 리포트**: 수익률, 변동성, 샤프 지수 등 다양한 통계 지표와 시각화 차트를 제공합니다.

## 기술 스택

| 구분       | 기술                                                              |
| :--------- | :---------------------------------------------------------------- |
| **백엔드**   | Python, FastAPI, backtesting.py, SQLAlchemy, pandas, numpy        |
| **프론트엔드** | TypeScript, React, Vite, Zustand, Recharts, shadcn/ui, Tailwind CSS |
| **데이터베이스** | MySQL (개발/프로덕션), SQLite (테스트)                     |
| **인프라/배포** | Docker, Docker Compose, Nginx                                     |
| **테스트**     | Pytest (백엔드), Vitest, React Testing Library, Playwright (프론트엔드) |

## 프로젝트 구조

```
.
├── backtest_be_fast/  # 백엔드 (FastAPI)
├── backtest_fe/       # 프론트엔드 (React + Vite)
├── database/          # DB 스키마 및 초기화 스크립트
├── compose.dev.yaml   # 개발용 Docker Compose 설정
└── README.md          # 프로젝트 안내 문서
```

---

## 개발 환경 시작하기 (Docker)

프로젝트의 모든 서비스는 Docker Compose를 통해 한 번에 실행할 수 있습니다. (Docker 설치 필수)

```bash
# 1. 개발용 컨테이너 빌드 및 백그라운드 실행
docker compose -f compose.dev.yaml up -d --build

# 2. 서비스 접속
#    - 프론트엔드: http://localhost:5173
#    - 백엔드 API 문서 (Swagger UI): http://localhost:8000/api/v1/docs

# 3. 로그 확인 (필요 시)
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# 4. 서비스 중지
docker compose -f compose.dev.yaml down
```

## 테스트 실행하기

### 백엔드 테스트

```bash
# 컨테이너 내에서 모든 테스트 실행
docker compose -f compose.dev.yaml exec backtest-be-fast pytest

# 단위 테스트
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit
```

### 프론트엔드 테스트

```bash
# 컨테이너 내에서 모든 테스트 실행
docker compose -f compose.dev.yaml exec backtest-fe npm test

# 대화형 UI 모드로 테스트 실행
docker compose -f compose.dev.yaml exec backtest-fe npm run test:ui
```

## 커밋 메시지 컨벤션

1. 기본 포맷 (Format)

```
태그(스코프): 제목 (50자 내외)

- 본문 (선택 사항, 자세한 설명이 필요할 때만 작성)
```

2. 스코프 (Scope) - 위치 구분

```
be | Backend 관련 코드
fe | Frontend 관련 코드
common | 양쪽 모두 영향이 있거나, 프로젝트 전체 설정 (README, .gitignore)
infra | 배포, Docker, CI/CD 등
```

3. 태그 (Type) - 작업 성격

```
feat | 새로운 기능 추가 | API 개발, 버튼 추가
fix | 버그 수정 | 로직 오류 수정, 오타 수정
docs | 문서 수정 | README, Swagger, 주석 수정
style | 코드 포맷팅 (로직 변경 X) | 세미콜론 누락, 줄바꿈, 들여쓰기 정렬
refactor | 코드 리팩토링 | 기능 변경 없이 코드 구조 개선
test | 테스트 코드 | 테스트 코드 추가/수정 (프로덕션 코드 변경 X)
chore | 기타 잡무 | 빌드 설정, 패키지 매니저 설정, 라이브러리 추가
```

## 문서

프로젝트의 아키텍처, 설계 결정, 테스트 전략 등에 대한 상세 문서는 각 서비스의 `docs` 디렉토리에서 확인할 수 있습니다.

-   [백엔드 문서 바로가기](./backtest_be_fast/docs/README.md)
-   [프론트엔드 문서 바로가기](./backtest_fe/docs/README.md)
