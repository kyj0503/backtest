# 커밋 메시지 컨벤션 가이드

백테스팅 시스템 모노리포지토리를 위한 통일된 커밋 메시지 규칙입니다.

## 기본 형식

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type (필수)
- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **refactor**: 코드 리팩터링 (기능 변경 없음)
- **style**: 코드 스타일 변경 (포맷팅, 세미콜론 등)
- **test**: 테스트 코드 추가 또는 수정
- **docs**: 문서 변경
- **perf**: 성능 개선
- **ci**: CI/CD 설정 변경
- **chore**: 빌드 도구, 패키지 관리자 등의 변경
- **revert**: 이전 커밋 되돌리기

### Scope (권장)
모노리포지토리 특성상 변경된 영역을 명시:

규칙: Type/Scope는 영어로 작성합니다. 설명(Description)과 본문(Body), 푸터는 한글을 기본으로 합니다.

#### 주요 영역
- **backend**: 백엔드 관련 변경사항
- **frontend**: 프론트엔드 관련 변경사항
- **infra**: 인프라, Docker, CI/CD 관련
- **docs**: 문서 전용 (README, 가이드 등)
- **config**: 설정 파일 변경

#### 세부 영역 (선택적)
- **backend/api**: API 엔드포인트
- **backend/service**: 비즈니스 로직 서비스
- **backend/domain**: 도메인 모델
- **backend/test**: 백엔드 테스트
- **frontend/components**: React 컴포넌트
- **frontend/hooks**: 커스텀 훅
- **frontend/utils**: 유틸리티 함수
- **frontend/test**: 프론트엔드 테스트

### Description (필수)
- 50자 이내로 간결하게 작성
- **한글로 작성** (팀 내 의사소통 효율성을 위해)
- 명령형 어조 사용 ("추가" not "추가했음" or "추가하기")
- 마침표 없음
- 간결하고 명확한 표현 사용

### Body (선택)
- 72자마다 줄바꿈
- "무엇을" 변경했는지보다 "왜" 변경했는지 설명
- 여러 줄 가능

### Footer (선택)
- Breaking changes: `BREAKING CHANGE:`
- 이슈 참조: `Closes #123`, `Fixes #456`
- 리뷰어: `Reviewed-by:`

## 예시

### 기본 예시
```bash
feat(backend): 포트폴리오 최적화 서비스 추가

feat(frontend): Recharts를 사용한 차트 컴포넌트 구현

fix(backend/api): 백테스트 엔드포인트 검증 오류 수정

refactor(frontend/hooks): 폼 상태 로직을 커스텀 훅으로 추출

test(backend): 전략 서비스 단위 테스트 추가

docs: API 문서 업데이트

ci: Jenkins 파이프라인에 프론트엔드 빌드 단계 추가
```

### 상세 예시
```bash
feat(backend/domain): 포트폴리오 관리를 위한 DDD 아키텍처 구현

- Portfolio 도메인에 값 객체와 엔티티 추가
- 복잡한 비즈니스 로직을 위한 PortfolioDomainService 구현
- 가중치 최적화 및 상관관계 분석 기능 추가

BREAKING CHANGE: 포트폴리오 API 구조 변경
Closes #123
```

### 멀티 영역 변경
```bash
feat: 실시간 뉴스 통합 기능 추가

- backend: 네이버 뉴스 API 서비스 구현
- frontend: 뉴스 모달 컴포넌트 추가
- docs: 뉴스 엔드포인트 API 가이드 업데이트

Closes #456
```

## 특별 규칙

### 1. 모노리포 브레이킹 체인지
여러 영역에 영향을 주는 변경사항:
```bash
feat!: Pydantic V2로 마이그레이션

BREAKING CHANGE: 모든 API 응답 모델 업데이트
- backend: 모든 Pydantic 모델을 V2 문법으로 업데이트
- frontend: API 타입 정의 업데이트
- docs: API 문서 예시 업데이트
```

### 2. Phase 기반 리팩터링
대규모 리팩터링 작업 시:
```bash
refactor(backend): Phase 4 아키텍처 재설계 완료

- 도메인 통합을 통한 Enhanced Services 구현
- 17개 도메인 이벤트를 포함한 Event-driven 아키텍처 추가
- 명령/조회 분리를 위한 CQRS 패턴 통합
- 기존 API와의 역호환성 유지

Phase 4/5 완료
```

### 3. 의존성 업데이트
```bash
chore(backend): FastAPI 0.104.1로 업데이트

chore(frontend): React Icons 의존성 추가

chore: Docker 베이스 이미지 업데이트
```

### 4. 긴급 수정 (Hotfix)
```bash
fix!: 인증 시스템 보안 취약점 수정

BREAKING CHANGE: JWT 토큰 형식 변경
영향: 인증이 필요한 모든 API 엔드포인트
```

## 자주 하는 실수

### 잘못된 예시
```bash
# Scope 없음, 설명 불충분
fix: 버그 수정

# Type 잘못됨
update: 새로운 기능 추가

# 설명이 너무 김 (50자 초과)
feat(backend): 현대 포트폴리오 이론을 사용하여 최적 가중치를 계산하는 새로운 포트폴리오 최적화 서비스 추가

# 과거형 사용
feat(frontend): 차트 컴포넌트를 추가했음

# 마침표 포함
feat(backend): 새로운 API 엔드포인트 추가.

# 영어 사용 (팀 내 표준과 불일치)
feat(backend): Add new API endpoint
```

### 올바른 예시
```bash
fix(backend/api): 포트폴리오 가중치 검증 오류 수정

feat(backend): 포트폴리오 최적화 서비스 추가

refactor(frontend): 차트 로직을 커스텀 훅으로 추출

docs: 배포 가이드 업데이트

test(frontend): 폼 검증 단위 테스트 추가
```

## 툴 및 자동화

### Git Hooks (권장)
```bash
# .gitmessage 템플릿 설정
git config commit.template .gitmessage

# Commitizen 사용 (선택)
npm install -g commitizen
npm install -g cz-conventional-changelog
```

### IDE 설정
- VSCode: Git Commit Message extension
- IntelliJ: Git Commit Template plugin

### 검증 스크립트
```bash
# 커밋 메시지 검증 (commit-msg hook)
#!/bin/bash
commit_regex='^(feat|fix|refactor|style|test|docs|perf|ci|chore|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!"
    echo "Use: <type>(<scope>): <description>"
    exit 1
fi
```

## 마이그레이션 가이드

기존 커밋들을 새로운 컨벤션으로 수정하려면:

1. **Interactive Rebase 사용**
```bash
git rebase -i HEAD~10  # 최근 10개 커밋 수정
```

2. **커밋 메시지 일괄 수정**
```bash
# 특정 패턴의 커밋들 일괄 수정
git filter-branch --msg-filter 'sed "s/^fix:/fix(backend):/"'
```

3. **새 브랜치에서 정리**
```bash
git checkout -b feature/clean-commit-history
# 커밋 정리 후
git push origin feature/clean-commit-history
```

### 기존 커밋 메시지 변환 예시
```bash
# 기존 (영어 혼재)
feat: Add portfolio optimization service
fix: TypeScript build error

# 새 컨벤션 (한글 설명)
feat(backend): 포트폴리오 최적화 서비스 추가
fix(frontend): TypeScript 빌드 오류 수정
```
