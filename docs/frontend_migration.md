shadcn 스타일의 컴포넌트로 “UI/UX의 대부분(버튼, 입력, 모달, 토스트, 네비게이션 등)”을 충분히 만들 수 있지만, 차트·데이터그리드·지도·고급 시각화나 비즈니스 로직까지 전부 대체하긴 어렵고 보완 라이브러리가 필요합니다.
shadcn/ui로 가능한 것

기본 컴포넌트: 버튼, 입력, 셀렉트, 토글, 라디오, 체크박스, 배지, 탭, 아코디언, 모달, 드롭다운, 팝오버, 툴팁 등 UI 구성요소 전체.
레이아웃/토큰: Tailwind + 토큰(색상/간격)을 이용한 테마, 다크모드, 반응형 레이아웃 구성.
접근성: 내부적으로 Radix 프리미티브를 쓰면 ARIA/키보드 동작이 우수.
일관된 스타일 규칙: cva/cn 패턴으로 변형(variant) 관리, 일관된 디자인 시스템 구축 가능.
빠른 프로토타이핑: 제공되는 컴포넌트(혹은 생성 스캐폴드)를 그대로 사용하면 개발 속도 증대.
제한 사항 / 보완해야 할 부분

차트·데이터 시각화: 복잡한 차트·시계열·캔들차트는 recharts, chart.js, apexcharts, echarts 등 별도 라이브러리 필요.
데이터 그리드 / 테이블: 대용량 그리드(가상 스크롤, 정렬, 필터링)는 tanstack-table 등 전문 라이브러리 필요.
폼 검증·스키마: react-hook-form + zod 같은 조합이 권장(단순 폼은 shadcn 컴포넌트로 충분).
상태관리·라우팅·인증 로직: shadcn은 UI 라이브러리이므로 zustand/redux/react-query 등 사용.
애니메이션·모션: 정교한 애니메이션은 framer-motion 필요.
완전한 패키지화 아님: shadcn은 보통 “템플릿/생성물”로 소스 파일(프로젝트 내)에 복사해 쓰는 패턴이라, 업데이트/업그레이드 관리는 수동.
타입·의존성 관리: lucide-react, @radix-ui/*, class-variance-authority 등 의존성·타입이 필요하며 CI에서 타입 문제(특히 TS 설정)가 발생할 수 있음.
도입 시 고려 포인트(실무)

종류: shadcn 컴포넌트는 대부분 Radix + Tailwind + cva 조합 → @radix-ui/*, class-variance-authority, lucide-react 등 설치 필요.
업데이트 전략: 로컬에 복사한 컴포넌트를 계속 수정하면 빠르지만, upstream 변경 추적이 어려움. 패키지 형태로 관리하면 업그레이드 용이.
타입 안정성: tsconfig.json에서 skipLibCheck 활성화(이미 활성화됨)를 유지하되, 프로젝트 타입 오류는 컴포넌트 Props를 명확히 선언해 해결.
CI/빌드: 빌드환경(도커)에서도 devDependencies가 필요할 수 있음 — Dockerfile에서 npm ci와 npm run build 단계의 의존성 설치를 검토.
권장 보완 라이브러리(예시)

Forms: react-hook-form, zod
Charts: recharts, apexcharts, echarts
Data Tables: @tanstack/react-table
Icons: lucide-react (shadcn 표준)
Accessibility primitives: @radix-ui/react-*
Motion: framer-motion
State & Data: zustand, react-query/tanstack-query
실행(도입/전환) 전략 제안

점진적 도입(권장):
src/components/ui에 이미 있는 shadcn 스타일 컴포넌트 검토(현재 repo에 존재함).
일관성 없는 컴포넌트(예: 버튼/입력)만 shadcn 스타일로 정리 → 테스트/빌드 확인.
차트·그리드·특수 컴포넌트는 전문 라이브러리로 남겨 통합 스타일만 적용.
문서화(frontend/docs/UI_OVERRIDES.md)로 어디를 오버라이드했는지 기록.
한번에 교체(큰 변경):
고려사항: 작업량 큼, 리스크 높음. 자동화 스크립트/검색+치환 필요.