# Spring Boot 커뮤니티 백엔드 (backtest_be_spring)

이 서비스는 커뮤니티, 채팅, 인증 관련 기능을 제공하는 Spring Boot 기반 백엔드 애플리케이션입니다.

주요 책임:
- 사용자 인증 및 회원 관리
- 커뮤니티 게시판(게시글/댓글/검색)
- 실시간 채팅(웹소켓/STOMP)
- 권한 및 보안 (Spring Security)

## 요구 사항
- Java 17 이상
- Gradle Wrapper (프로젝트에 포함됨)
- Docker 및 Docker Compose (Docker 배포/개발 선택시)

## 빠른 시작 (로컬)
루트에서 프로젝트로 이동 후 Gradle Wrapper로 실행합니다.

```bash
cd backtest_be_spring
./gradlew bootRun
```

애플리케이션이 시작되면 기본 포트로 노출됩니다 (기본: 8080). 설정은 `src/main/resources/application.yml`과 환경 변수로 오버라이드할 수 있습니다.

## 프로덕션 빌드
JAR 파일을 빌드한 뒤 실행합니다.

```bash
./gradlew bootJar
java -jar build/libs/*.jar
```

## Docker / Docker Compose (개발 환경)
루트의 Compose 구성에서 `backtest_be_spring` 서비스가 정의되어 있습니다. 전체 스택을 띄우려면 프로젝트 루트에서 다음을 실행하세요:

```bash
docker compose -f compose/compose.dev.yaml up -d --build
```

컨테이너 로그 확인:

```bash
docker compose -f compose/compose.dev.yaml logs -f backtest_be_spring
```

## 설정 (환경 변수)
- `SPRING_PROFILES_ACTIVE` - 활성 프로파일 (예: `dev`, `prod`)
- 데이터베이스 연결: `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD`
- JWT/보안 관련: `JWT_SECRET`, `JWT_EXPIRATION_MS` 등 (환경에 따라 다름)

권장 방법: 민감한 값은 시스템 환경 변수 또는 Secrets 관리 도구(예: Docker secrets, Kubernetes secrets)에 보관하세요.

## API 문서
애플리케이션 실행 후 Swagger UI를 통해 API 문서를 확인할 수 있습니다:

```
http://localhost:8080/swagger-ui.html
```

## 테스트
단위/통합 테스트는 Gradle로 실행합니다.

```bash
./gradlew test
```

테스트 및 CI 관련 자세한 내용은 `docs/Test.md`를 참고하세요.

## 로그 및 헬스 체크
- 기본 헬스 체크 엔드포인트: `/actuator/health` (Actuator가 활성화된 경우)
- 메트릭 및 상태 정보는 Actuator 설정에 따라 노출됩니다.

## 기여 및 코드 스타일
- 코드 포맷: `./gradlew spotlessApply` (프로젝트에 Spotless 설정이 있을 경우)
- 커밋 메시지: 간결한 설명과 변경 의도를 포함하세요

더 자세한 개발 지침은 `docs/Development.md`와 `docs/Test.md`를 확인하세요.