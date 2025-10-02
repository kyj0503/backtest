# 테스트 가이드

이 문서는 단위 테스트, 통합 테스트, 커버리지 수집 및 CI에서의 테스트 실행 방법을 설명합니다.

## 테스트 종류
- 단위(Unit) 테스트: 서비스, 유틸리티, 리포지토리 레이어의 개별 단위 로직을 검증합니다.
- 통합(Integration) 테스트: 데이터베이스, 메시지 큐, 외부 API 연동 등 실제 컴포넌트 통합 동작을 검증합니다.
- 엔드투엔드(E2E) 테스트: 전체 스택을 기동해 시나리오 기반 테스트를 수행할 때 사용합니다 (대개 별도 환경에서 실행).

## 로컬에서 테스트 실행
프로젝트 루트에서 Gradle을 통해 테스트를 실행합니다.

```bash
cd backtest_be_spring
./gradlew test
```

통합 테스트가 별도의 리소스(예: MySQL, Redis)를 필요로 할 경우, Docker Compose로 의존 서비스를 먼저 기동하세요.

```bash
# 루트 프로젝트에서 전체 스택 기동
docker compose -f compose/compose.dev.yaml up -d --build

# 백엔드 서비스의 테스트 실행
cd backtest_be_spring
./gradlew test
```

## 테스트 분류 및 실행 옵션
- 특정 테스트만 실행: `--tests` 옵션을 사용합니다.

```bash
./gradlew test --tests "com.example.service.*ServiceTest"
```

- 통합 테스트를 별도 태그로 관리하는 경우 `@Tag("integration")`을 활용하고 Gradle에 프로퍼티로 제어하세요.

```bash
./gradlew test --tests "*" -DincludeTags=integration
```

## 테스트 커버리지
- 프로젝트에 JaCoCo 또는 다른 커버리지 도구가 설정되어 있다면 Gradle task로 리포트 생성이 가능합니다.

예시 (JaCoCo):

```bash
./gradlew jacocoTestReport
```

생성된 리포트는 `build/reports/jacoco/test/html/index.html` 등에서 확인할 수 있습니다.

## CI(예: GitHub Actions)에서의 테스트 권장 구성
- 워크플로우 단계 예시:
	1. 체크아웃
	2. JDK 설치 (Java 17)
	3. 캐시 의존성 (Gradle caches)
	4. 의존 서비스 필요 시 Docker Compose로 띄움
	5. `./gradlew test` 실행
	6. 커버리지 리포트 업로드(옵션)

팁: 통합 테스트는 CI에서 네트워크/DB 리소스 때문에 느려질 수 있으므로, 유닛 테스트는 빠르게, 통합 테스트는 별도의 워크플로우로 분리하는 것을 권장합니다.

## 테스트 작성 규칙(권장)
- 각 테스트는 독립적이어야 하며, 서로의 상태에 의존하면 안됩니다.
- 데이터베이스를 사용하는 테스트는 트랜잭션 롤백 또는 테스트 전후 클린업을 수행하세요.
- 객체 생성은 테스트 데이터 빌더(Builder) 또는 테스트 픽스처/팩토리를 사용해 중복을 줄이세요.

## 로깅/디버깅 테스트 실패
- 테스트 실패 시 `--stacktrace`, `--info` 또는 `--debug` 옵션을 사용해 원인 파악에 필요한 추가 로그를 확인하세요.

```bash
./gradlew test --stacktrace --info
```

## 추가 리소스
- 프로젝트의 `src/test/java` 폴더 구조를 참고해 기존 테스트 패턴을 따르세요.
- 팀 내 테스트 스타일 가이드나 추가 규칙이 있다면 해당 문서를 우선 적용하세요.

문서가 더 필요하면 어떤 테스트 프레임워크(JUnit 버전, Mocking 라이브러리 등)를 중점으로 문서화할지 알려주세요.
