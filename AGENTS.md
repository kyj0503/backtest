# 저장소 가이드라인

## 프로젝트 구조 및 모듈 구성

### 핵심 디렉터리
- `backtest_be_fast/`: FastAPI 마이크로서비스; 도메인 로직은 `app/` 하위에 위치
- `backtest_be_spring/`: Spring Boot API; 주 코드는 `src/main/java`에 위치
- `backtest_fe/`: Vite + React 클라이언트; 기능 모듈은 `src/features`에, 공유 UI와 유틸리티는 `src/shared`에 위치
- `database/`: SQL 스냅샷 (`01_schema.sql`, `02_yfinance.sql`) - 스키마 업데이트에 사용
- `compose/`: 개발 및 프로덕션 환경을 위한 중앙 집중식 Docker Compose 파일

### 프론트엔드 아키텍처 (`backtest_fe/`)
```
src/
├── shared/           # 공통 인프라스트럭처
│   ├── types/        # 전역 타입 정의
│   ├── config/       # 환경 설정
│   ├── hooks/        # 재사용 가능한 커스텀 훅
│   ├── utils/        # 유틸리티 함수
│   └── components/   # 공용 UI 컴포넌트
├── features/         # 기능별 모듈
│   ├── backtest/     # 백테스트 관련 기능
│   ├── portfolio/    # 포트폴리오 관리
│   └── auth/         # 인증 관련
├── pages/            # 페이지 컴포넌트
└── test/             # 테스트 유틸리티
```

## 빌드 및 개발 명령어

### 전체 스택 실행
```bash
# 개발 환경 시작
docker compose -f compose/compose.dev.yaml up -d --build

# 서비스 중지
docker compose down
```

### 개별 서비스

#### FastAPI 백엔드
```bash
cd backtest_be_fast
pip install -r requirements.txt
python run_server.py
# 또는 uvicorn app.main:app --reload
```

#### 프론트엔드
```bash
cd backtest_fe
npm ci                # 의존성 설치
npm run dev          # Vite 개발 서버
npm run build        # 최적화된 프로덕션 빌드
npm run lint         # ESLint 검사
npm run test:run     # 테스트 실행 (단일 실행)
npm run test         # 테스트 실행 (워치 모드)
npm run type-check   # TypeScript 타입 검사
```

#### Spring Boot 백엔드
```bash
cd backtest_be_spring
./gradlew bootRun    # 로컬 API 서버 실행
./gradlew build      # 프로덕션 아티팩트 빌드
./gradlew test       # 테스트 실행
```

**개발 도구 설정**: Spring Boot Devtools가 활성화되어 있습니다. IntelliJ에서 `Build project automatically`와 `compiler.automake.allow.when.app.running`을 활성화하면 저장 시 자동 재시작됩니다.

### API 문서
- Spring Boot: 실행 후 `http://localhost:8080/swagger-ui.html`에서 Swagger UI 접근 가능
- OpenAPI 엔드포인트: `/v3/api-docs/**` (기본적으로 공개 접근 가능)

## 코딩 스타일 및 네이밍 규칙

### Python (FastAPI)
- **PEP 8** 준수: `black` (라인 길이 88), `isort` 사용
- **네이밍**: snake_case 모듈, PascalCase 클래스
- **타입 힌트**: 필수 사용
- **인터페이스**: 타입이 지정된 인터페이스 선호

### TypeScript/React (Frontend)
- **ESLint** 기본 설정, 2-space 들여쓰기
- **네이밍**: PascalCase 컴포넌트, camelCase 훅/서비스
- **함수형 컴포넌트**: 화살표 함수 사용
- **커스텀 훅**: `use`로 시작하는 네이밍

### Java (Spring Boot)
- **Java 17** 기능 제한적 사용
- **패키지 구조**: 계층화 유지 (`controller`, `service`, `config`)
- **네이밍**: camelCase 변수/메서드, PascalCase 클래스

## 테스트 가이드라인

### 현재 상태
- **프론트엔드**: Vitest + Testing Library로 포괄적인 테스트 환경 구축
  - 단위 테스트: 유틸리티, 훅, 서비스
  - 컴포넌트 테스트: UI 컴포넌트
  - 통합 테스트: 전체 플로우
- **FastAPI**: 자동화된 단위 테스트 스위트 현재 미유지; 필요 시 수동 QA 및 통합 스모크 체크 수행
- **Spring Boot**: Gradle 테스트 설정 유지; Java 테스트 재도입 시 `./gradlew test` 실행

### 테스트 실행
```bash
# 프론트엔드 테스트
npm run test:run     # 모든 테스트 단일 실행
npm run test         # 워치 모드
npm run test:coverage # 커버리지 리포트

# Spring Boot 테스트
./gradlew test       # Java 테스트 (재도입 시)
```

## 커밋 및 Pull Request 가이드라인

### 커밋 메시지
- **간결하고 명령형** 제목 작성 (예: `HMR 비활성화`, `compose 수정`)
- 필요 시 본문에 이중 언어 컨텍스트 포함 가능
- **컨벤션**:
  ```
  feat: 새로운 기능 추가
  fix: 버그 수정  
  docs: 문서 업데이트
  style: 코드 스타일 변경
  refactor: 코드 리팩토링
  test: 테스트 추가/수정
  chore: 빌드 관련 업데이트
  ```

### Pull Request
- **이슈 연결**: 관련 이슈 링크
- **위험도/롤백** 요약 포함
- **영향받는 서비스** 명시
- **UI 스크린샷** 또는 커버리지 차이 첨부 (해당하는 경우)
- **검증**: 린트 검사 및 대상 `docker compose` 스모크 실행 후 리뷰 요청

## 설정 및 운영 노트

### 환경 변수 관리
- **프론트엔드/FastAPI**: 각각의 디렉터리에 `.env` 파일 생성 필요
- **Spring Boot**: `application.properties` + 선택적 `.env` 파일 (`.env.example`에서 복사)로 로컬에서 민감한 값 오버라이드
- **주의사항**: 시크릿 정보는 절대 커밋하지 말 것

### 환경 변수 위치
- **Spring Boot**: 프로젝트 루트에서 `.env` 파일 읽음 (`./gradlew bootRun` 실행 디렉터리와 동일)
- **Docker Compose**: 루트 `.env` 파일을 프로덕션 오버라이드용으로 사용

### 데이터베이스
- **스키마 정의**: `database/01_schema.sql`이 표준 MySQL 스키마 정의
- **JPA 매핑과 동기화** 필요 (예: `users.investment_type`은 CHECK 제약 조건이 있는 `VARCHAR(20)` 사용)
- **환경 키 문서화**: 새로운 환경 키 도입 시 관련 README에 문서화

### 포트 구성
- **MySQL**: 호스트의 `3307` 포트에 매핑 (설치된 MySQL(3306)과 충돌 방지)
- **포트 커스터마이징**: 필요 시 `MYSQL_HOST_PORT` 변수로 다른 포트 지정 가능

## 개발 환경별 URL

| 서비스 | 개발 URL | 설명 |
|---------|----------|------|
| 프론트엔드 | http://localhost:5173 | Vite 개발 서버 |
| FastAPI | http://localhost:8000 | 백테스트 API |
| Spring Boot | http://localhost:8080 | 사용자 관리 API |
| MySQL | localhost:3307 | 데이터베이스 |
| Swagger UI | http://localhost:8080/swagger-ui.html | API 문서 |

## 품질 관리

### 코드 품질 도구
```bash
# 프론트엔드
npm run lint         # ESLint 검사
npm run lint:fix     # ESLint 자동 수정
npm run type-check   # TypeScript 타입 검사

# FastAPI
black app/           # 코드 포맷팅
isort app/           # import 정렬

# Spring Boot
./gradlew check      # 정적 분석
```

### 프리커밋 검증
1. 해당 서비스의 린트 검사 통과
2. 타입 검사 통과 (TypeScript)
3. 테스트 실행 (해당하는 경우)
4. Docker Compose 스모크 테스트

이 가이드라인을 따라 일관성 있고 품질 높은 코드베이스를 유지할 수 있습니다.