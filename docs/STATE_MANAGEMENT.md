# 상태 관리 가이드

목적: 백테스팅 프론트엔드에서 일관되고 예측 가능한 상태 관리를 유지하기 위한 실제 구현과 계획을 정리합니다. 코드 예제는 포함하지 않습니다.

## 현재 방식
- 로컬 우선: 전역 상태는 최소화하고 컴포넌트·훅 단위 로컬 상태를 우선 사용
- 단방향 데이터 흐름: 부모→자식 Props 전달, 이벤트 상향 전파
- 타입 안전성: TypeScript 기반으로 상태/액션/반환 타입을 명시

## 커스텀 훅 구조 (`src/hooks/*`)
- useBacktestForm: 백테스트 폼 통합 상태와 액션을 관리(전략 변경 시 기본 파라미터 자동 적용 포함)
- usePortfolio: 자산 추가/삭제/수정, 가중/금액 합계, 유효성 검증 등 포트폴리오 조작
- useFormValidation: 날짜·포트폴리오·금액 검증과 오류 상태
- useStrategyParams: 전략별 파라미터 구성/라벨/검증 보조
- useExchangeRate: 기간별 환율 데이터 페칭/상태
- useVolatilityNews: 변동성 이벤트·종목 선택·뉴스 모달 상태
- useTooltip/useDropdown/useModal: 공통 UI 상태 관리

## 데이터 연동
- API 서비스: `src/services/api.ts`, `src/services/auth.ts`, `src/services/community.ts` 등에서 호출 규칙 일원화
- 베이스 URL: 개발은 Vite 프록시, 프로덕션은 환경변수(`VITE_API_BASE_URL`) 우선

## 테스트 관점
- Vitest + Testing Library로 폼/훅/서비스를 단위 검증
- 차트는 환경 제약(JSDOM) 상 기본 렌더 중심 스모크 테스트

## 향후 계획
- 상태 정규화 강화: 중복 제거와 파생 상태 최소화
- 폼 유효성 보강: 전략·기간·포트폴리오 제약 조건 명시화
- 캐싱/동기화: 빈번한 데이터(전략 목록, 환율·심볼 정보) 캐싱 정책 추가
