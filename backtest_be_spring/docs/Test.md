# 테스트 가이드

단위/통합 테스트, 커버리지, CI 실행 방법을 정리한다.

## 테스트 종류
- 단위(Unit) 테스트: 서비스, 유틸리티, 리포지토리 레이어의 개별 로직을 검증한다.
- 통합(Integration) 테스트: 데이터베이스, 메시지 큐, 외부 API 연동 등 실제 컴포넌트 통합 동작을 검증한다.
- 엔드투엔드(E2E) 테스트: 전체 스택을 기동해 시나리오 기반 테스트를 수행한다(대개 별도 환경에서 실행).

## 로컬 실행
프로젝트 루트에서 Gradle로 테스트를 실행한다.

```bash
cd backtest_be_spring
./gradlew test
```

통합 테스트에 MySQL/Redis가 필요하면 Compose로 의존 서비스를 먼저 기동한다.

```bash
# 루트 프로젝트에서 전체 스택 기동
docker compose -f compose/compose.dev.yaml up -d --build

# 백엔드 서비스의 테스트 실행
cd backtest_be_spring
./gradlew test
```

## 테스트 분류/옵션
- 특정 테스트만 실행: `--tests` 옵션을 사용한다.

```bash
./gradlew test --tests "com.example.service.*ServiceTest"
```

- 통합 테스트를 태그로 관리하는 경우 `@Tag("integration")`을 사용하고 Gradle 프로퍼티로 제어한다.

```bash
./gradlew test --tests "*" -DincludeTags=integration
```

## 테스트 커버리지
- JaCoCo 등 커버리지 도구가 설정되어 있다면 Gradle task로 리포트를 생성한다.

예시 (JaCoCo):

```bash
./gradlew jacocoTestReport
```

생성된 리포트는 `build/reports/jacoco/test/html/index.html` 등에서 확인할 수 있습니다.

## CI 권장 구성
- 예시 단계: 체크아웃 → JDK 17 → Gradle 캐시 →(옵션) 의존 서비스 기동 → `./gradlew test` →(옵션) 커버리지 업로드
- 통합 테스트는 별도 워크플로로 분리하는 것을 권장한다.

## 테스트 작성 규칙(권장)
- 테스트는 독립적으로 작성한다.
- DB를 사용하는 테스트는 트랜잭션 롤백 또는 전후 클린업을 수행한다.
- 테스트 데이터 빌더/픽스처로 중복을 줄인다.

## 로깅/디버깅
- 실패 시 `--stacktrace`, `--info`, `--debug`로 추가 로그를 확인한다.

```bash
./gradlew test --stacktrace --info
```

## 추가 리소스
- `src/test/java` 폴더 구조의 기존 패턴을 따른다.
- 팀 내 테스트 스타일 가이드가 있다면 우선 적용한다.
