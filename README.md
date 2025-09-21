# 백테스트 플랫폼

## 🚀 개요

전문적인 백테스팅 및 포트폴리오 분석을 위한 통합 플랫폼입니다. React 프론트엔드와 FastAPI/Spring Boot 백엔드로 구성된 모던 웹 애플리케이션입니다.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/your-repo)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](compose/)

## 🏗️ 시스템 구조

```
backtest/
├── backtest_fe/           # React + TypeScript 프론트엔드
├── backtest_be_fast/      # FastAPI 백테스트 엔진
├── backtest_be_spring/    # Spring Boot 사용자 관리
├── database/              # MySQL 스키마 및 초기 데이터
└── compose/               # Docker Compose 설정
```

## 🛠️ 기술 스택

### 프론트엔드 (`backtest_fe/`)
- **React 18.2+** - 최신 React 기능
- **TypeScript 5.0+** - 타입 안전성
- **Vite 4.4+** - 빠른 빌드 도구
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **shadcn/ui** - 모던 UI 컴포넌트
- **Vitest** - 빠른 테스트 환경

### 백엔드 - 백테스트 엔진 (`backtest_be_fast/`)
- **FastAPI** - Python 비동기 웹 프레임워크
- **Pydantic** - 데이터 검증 및 직렬화
- **NumPy/Pandas** - 수치 계산 및 데이터 분석
- **yfinance** - 금융 데이터 수집
- **SQLAlchemy** - ORM

### 백엔드 - 사용자 관리 (`backtest_be_spring/`)
- **Spring Boot 3.x** - Java 엔터프라이즈 프레임워크
- **Spring Data JPA** - 데이터 영속성
- **Spring Security** - 인증 및 권한 관리
- **MySQL 8.0+** - 관계형 데이터베이스

## ⚡ 빠른 시작

### 1. 환경 설정

```bash
# 저장소 복제
git clone <repository-url>
cd backtest

# 환경 변수 파일 생성
cp backtest_fe/.env.example backtest_fe/.env
cp backtest_be_fast/.env.example backtest_be_fast/.env
cp backtest_be_spring/.env.example backtest_be_spring/.env
```

### 2. Docker Compose로 전체 스택 실행

```bash
# 개발 환경 실행
docker compose -f compose/compose.dev.yaml up -d --build

# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```

### 3. 개별 서비스 실행

#### 프론트엔드
```bash
cd backtest_fe
npm ci
npm run dev
# http://localhost:5173
```

#### FastAPI 백엔드
```bash
cd backtest_be_fast
pip install -r requirements.txt
python run_server.py
# http://localhost:8000
```

#### Spring Boot 백엔드
```bash
cd backtest_be_spring
./gradlew bootRun
# http://localhost:8080
```

## 🌐 서비스 엔드포인트

| 서비스 | 개발 URL | 설명 |
|---------|----------|------|
| 프론트엔드 | http://localhost:5173 | React 웹 애플리케이션 |
| FastAPI | http://localhost:8000 | 백테스트 API 서버 |
| Spring Boot | http://localhost:8080 | 사용자 관리 API |
| MySQL | localhost:3307 | 데이터베이스 |
| Swagger UI | http://localhost:8080/swagger-ui.html | API 문서 |

## 📊 주요 기능

### ✅ 백테스트 기능
- **다양한 전략**: Buy & Hold, SMA Cross, RSI 등
- **성과 분석**: 수익률, 샤프 비율, 드로우다운
- **시각화**: 수익률 차트, 포트폴리오 변화

### ✅ 포트폴리오 관리
- **자산 배분**: 가중치 기반 포트폴리오 구성
- **리밸런싱**: 주기적 재조정
- **리스크 분석**: VaR, 베타 계산

### ✅ 사용자 시스템
- **인증/권한**: JWT 기반 인증
- **프로필 관리**: 개인 설정 저장
- **히스토리**: 백테스트 결과 보관

## 🗄️ 데이터베이스

### 스키마 구조
```
database/
├── 01_schema.sql      # 메인 스키마 정의
└── 02_yfinance.sql    # 금융 데이터 초기값
```

### 주요 테이블
- `users` - 사용자 정보
- `backtest_results` - 백테스트 결과
- `portfolios` - 포트폴리오 설정
- `market_data` - 시장 데이터 캐시

## 🔧 개발 환경

### 요구 사항
- **Node.js 18+**
- **Python 3.11+**
- **Java 17+**
- **Docker & Docker Compose**
- **MySQL 8.0+**

### IDE 설정
- **VS Code**: 권장 확장 프로그램 설치
- **IntelliJ IDEA**: Spring Boot 개발
- **Cursor**: AI 지원 코드 에디터

### 코드 품질
```bash
# 프론트엔드
npm run lint          # ESLint 검사
npm run type-check    # TypeScript 검사
npm run test:run      # 테스트 실행

# FastAPI
black app/            # 코드 포맷팅
isort app/            # import 정렬
pytest               # 테스트 실행

# Spring Boot
./gradlew check      # 정적 분석
./gradlew test       # 테스트 실행
```

## 📚 문서

| 문서 | 설명 |
|------|------|
| [프론트엔드 가이드](backtest_fe/README.md) | React 애플리케이션 개발 |
| [FastAPI 가이드](backtest_be_fast/README.md) | 백테스트 API 개발 |
| [Spring Boot 가이드](backtest_be_spring/README.md) | 사용자 API 개발 |
| [아키텍처 문서](backtest_fe/docs/Architecture.md) | 시스템 설계 문서 |
| [배포 가이드](backtest_fe/docs/Deployment.md) | 운영 환경 배포 |

## 🚀 배포

### 프로덕션 배포

```bash
# 프로덕션 환경 실행
docker compose -f compose/compose.prod.yaml up --build -d

# 헬스 체크
curl http://localhost:8000/health
curl http://localhost:8080/actuator/health
```

### CI/CD

GitHub Actions를 통한 자동 배포:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          docker compose -f compose/compose.prod.yaml up -d --build
```

## 🤝 기여하기

### 개발 워크플로우

1. **Fork** 저장소
2. **Feature 브랜치** 생성: `git checkout -b feature/new-feature`
3. **커밋**: `git commit -m 'Add new feature'`
4. **푸시**: `git push origin feature/new-feature`
5. **Pull Request** 생성

### 커밋 컨벤션

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 업데이트
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드 관련 업데이트
```

## 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 🔗 관련 링크

- [프로덕션 사이트](https://backtest.example.com)
- [API 문서](https://api.backtest.example.com/docs)
- [이슈 트래커](https://github.com/your-repo/issues)
- [위키](https://github.com/your-repo/wiki)

## 💬 지원

문제가 있거나 질문이 있으시면:

- **이슈**: [GitHub Issues](https://github.com/your-repo/issues)
- **이메일**: support@backtest.example.com
- **슬랙**: [개발자 채널](https://workspace.slack.com)

---

⭐ **이 프로젝트가 도움이 되었다면 스타를 눌러주세요!**