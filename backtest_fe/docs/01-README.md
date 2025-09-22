### 핵심 원칙

## 빠른 시작

```bash
# 의존성 설치
npm ci

# 환경 설정
cp .env.example .env

# 개발 서버 실행
npm run dev

# 브라우저에서 확인
# http://localhost:5173
```

## 주요 스크립트

```bash
# 개발
npm run dev          # 개발 서버 실행
npm run build        # 프로덕션 빌드
npm run preview      # 빌드 결과 미리보기

# 테스트
npm run test         # 테스트 실행 (watch 모드)
npm run test:run     # 단일 실행
npm run test:coverage # 커버리지 리포트

# 코드 품질
npm run lint         # ESLint 검사
npm run lint:fix     # ESLint 자동 수정
npm run type-check   # TypeScript 타입 검사
```

## 환경 변수

### 개발 환경
```bash
VITE_API_URL=http://localhost:8080/api
VITE_ENVIRONMENT=development
VITE_DEBUG=true
```

### 프로덕션 환경
```bash
VITE_API_URL=https://api.backtest.com/api
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```