# 백테스팅 시스템

FastAPI + React 기반의 투자 전략 백테스팅 시스템입니다.

문제 발생 시: 트러블슈팅은 [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)를 참고하세요.

## 프로젝트 소개

투자 전략의 과거 성과를 분석하는 웹 기반 백테스팅 도구입니다. 다양한 기술적 지표로 전략을 시뮬레이션하고 리스크와 수익성을 분석합니다.

### 주요 특징
- 포트폴리오 및 단일 종목 백테스트 지원
- 현금 자산을 포함한 리스크 관리
- 실시간 주식 데이터 연동 (yfinance API)
- 종목별 뉴스 검색 기능 (네이버 검색 API)
- 시각적 차트 및 성과 분석

## 빠른 시작

### 개발 환경 실행
```bash
# 개발 환경 시작
docker compose -f compose.yml -f compose/compose.dev.yml up --build -d

# 백그라운드 실행
docker compose -f compose.yml -f compose/compose.dev.yml up -d

# 시스템 종료
docker compose -f compose.yml -f compose/compose.dev.yml down

# 프론트엔드 npm 패키지 추가/수정 후에는 반드시 아래 명령어로 강제 재빌드 (캐시 무시, 백그라운드 실행 아님)
docker compose -f compose.yml -f compose/compose.dev.yml build --no-cache
```

### 접속 정보
- **프론트엔드**: http://localhost:5174
- **백엔드 API**: http://localhost:8001
- **API 문서**: http://localhost:8001/api/v1/docs

### 테스트 실행
```bash
# 단위 테스트 (빠름)
./scripts/test-runner.sh unit

# 통합 테스트 (DB 포함)
./scripts/test-runner.sh integration

# 전체 테스트
./scripts/test-runner.sh all
```

### Radix UI 등 커스텀 Select/Dropdown 테스트 가이드

Radix UI 등 커스텀 셀렉트(Select/Dropdown) 컴포넌트는 실제 `<select>` 엘리먼트를 사용하지 않으므로, Testing Library의 `user.selectOptions` 대신 드롭다운 트리거를 클릭하고 옵션을 클릭하는 방식으로 테스트해야 합니다.

#### 예시 (user-event 기반)

```tsx
// 드롭다운 트리거(보통 combobox role)를 클릭
await user.click(screen.getByRole('combobox'));
// 원하는 옵션이 나타날 때까지 대기 후 클릭
const option = await screen.findByText('옵션명', {}, { timeout: 1000 });
await user.click(option);
// 이후 onChange 등 콜백 호출 여부 검증
expect(handleChange).toHaveBeenCalledWith('optionValue');
```

> ⚠️ 기존의 `user.selectOptions` 방식은 Radix UI 등 커스텀 셀렉트에는 동작하지 않습니다. 반드시 위와 같이 사용자 인터랙션을 모방해야 합니다.

## 기술 스택

### 프론트엔드
- **React 18** + TypeScript
- **Vite** - 고속 빌드 도구
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **Recharts** - 데이터 시각화

### 백엔드
- **FastAPI** + Python
- **Pydantic V2** - 데이터 검증
- **MySQL** - 주가 데이터 캐시
- **backtesting.py** - 백테스트 엔진

### 인프라
- **Docker** + Docker Compose
- **Jenkins** - CI/CD 파이프라인
- **nginx** - 프로덕션 웹 서버

## 문서

자세한 개발 가이드와 문서는 [`docs/`](docs/) 폴더를 참고하세요:

- [개발 가이드](docs/DEVELOPMENT_GUIDE.md) - 백엔드/프론트엔드 개발 방법
- [테스트 가이드](docs/TESTING_GUIDE.md) - 테스트 실행 및 전략
- [API 가이드](docs/API_GUIDE.md) - API 사용법 및 스키마
- [운영 가이드](docs/OPERATIONS_GUIDE.md) - 배포 및 운영 방법
- [아키텍처 가이드](docs/ARCHITECTURE_GUIDE.md) - 시스템 구조 및 설계
- [기여 가이드](docs/CONTRIBUTING.md) - 기여 방법 및 커밋 규칙

## 라이선스

이 프로젝트는 GNU AFFERO GENERAL PUBLIC LICENSE 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 확인하세요.
