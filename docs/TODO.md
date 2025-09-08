## Project TODO / Roadmap

간결하고 실행 가능한 작업 목록입니다. 상세 설계/정책은 `docs/` 내 개별 문서를 참고하세요.

### High (다음 스프린트)
- [ ] 백테스트 결과 지표 확장: 월/연도별 성과, 베타, 연속 손실/이익 기간, CAGR 보정
- [ ] Open trades 처리: `finalize_trades=True` 적용 검토 또는 자체 마감 로직 도입(현재 경고 다수)
- [ ] MySQL Repository 구현: `MySQLBacktestRepository` CRUD 구현 및 설정 스위치 지원
- [ ] API 검증/에러코드 일관화: 422 기준 정비, ValidationError 메시지 표준화
- [ ] 프론트 테스트 경고 제거: `React.act` 사용으로 마이그레이션, `act(...)` 누락 케이스 래핑

### Medium (제품 개선)
- [ ] 사용자/포트폴리오 저장: 사용자 관리 + 포트폴리오 저장/조회 API/UX
- [ ] 전략 파라미터 프리셋/검증 UI: 전략별 권장값/범위 시각화
- [ ] 성능/리소스 가드: 대용량 구간 타임아웃/메모리 보호 옵션 제공
- [ ] 의존성 보안 점검: 프론트 npm audit 취약점 우선순위 기반 처리

### Low (확장/실험)
- [ ] 뉴스/변동성 고도화: 키워드 필터, 간단 감성/상관 분석
- [ ] 자동완성/심볼 검색 개선: 캐시 + 최근 사용 심볼 제공
- [ ] 백테스트 시나리오 템플릿: 샘플 시나리오 저장/불러오기

### Quality / Tech Debt
- [ ] Pydantic V2 마이그레이션 마무리: ConfigDict, `json_schema_extra` 사용으로 경고 제거
- [ ] 백엔드 변환/폴백 안전성 테스트: 폴백 결과/결과 변환(safe_float/int) 단위 테스트 추가
- [ ] Docker 베이스 이미지 고정: 백엔드 `python:3.11-slim@<digest>`로 핀(프론트는 고정됨)

### CI/CD & Infra
- [ ] Jenkins 결과 게시 개선: GitHub Checks/Artifacts 링크화 검토
- [ ] 캐시 최적화: 프론트 테스트 컨테이너 npm 캐시 재사용률 점검 및 개선
- [ ] 배포 구성 단순화: 필요 시 `:latest` 푸시 완전 제거(캐시 목적 외 사용 지양)

### Docs
- [ ] 문서 교차 링크 정리: GUIDE ↔ TEST_ARCHITECTURE ↔ RUNBOOK 상호 연결 강화
- [ ] Compose 명령/경로 검수: `compose.yml` / `compose/compose.dev.yml` 사용 일원화 유지

---

## Done (최근)
- [x] 현금 자산 처리: `asset_type='cash'` 지원(0% 수익률, 무변동성)
- [x] 프론트 대규모 리팩터링: 폼/결과/뉴스 컴포넌트 분리, 상태 로직 훅화
- [x] 오프라인 모킹 테스트 체계: 외부 의존성 제거, CI 안정화
- [x] Jenkins 파이프라인 안정화: GHCR 로그인/푸시 재시도, 빌드 병렬화, POSIX 호환 수정
- [x] Compose 재구성/문서 일원화: `compose.yml`, `compose/compose.dev.yml` 반영

