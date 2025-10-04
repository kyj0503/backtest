# Spring Boot 커뮤니티 백엔드 (backtest_be_spring)

커뮤니티, 채팅, 인증 기능을 제공하는 Spring Boot 백엔드다.

주요 책임
- 사용자 인증 및 회원 관리
- 커뮤니티 게시판(게시글/댓글/검색)
- 실시간 채팅(웹소켓/STOMP)
- 권한 및 보안(Spring Security)

## 요구 사항
- Java 17 이상
- Gradle Wrapper (프로젝트에 포함됨)
- Docker 및 Docker Compose (Docker 배포/개발 선택시)

## 빠른 시작

### Docker Compose 개발 환경

**Hot Reload 지원**: 소스 코드 변경 시 자동으로 재빌드되고 서버가 재시작됩니다.

프로젝트 루트에서 전체 스택을 실행합니다:
```bash
docker compose -f compose.dev.yaml up -d --build
```

- Spring Boot: http://localhost:8080
- FastAPI: http://localhost:8000
- Frontend: http://localhost:5173
- MySQL: localhost:3307
- Redis: localhost:6380

**소스 코드 수정**: `backtest_be_spring/src` 디렉토리의 파일을 수정하면 Gradle이 자동으로 변경을 감지하고 애플리케이션을 재시작합니다.

**로그 확인**:
```bash
docker logs -f backtest-be-spring-dev
```

**서비스 재시작** (필요 시):
```bash
docker compose -f compose.dev.yaml restart backtest-be-spring
```

**서비스 중지**:
```bash
docker compose -f compose.dev.yaml down
```

## 프로덕션 빌드
JAR 파일을 빌드한 뒤 실행한다.

```bash
./gradlew bootJar
java -jar build/libs/*.jar
```

## Docker / Docker Compose (개발 환경)
전체 스택을 동시에 실행할 수 있다.

프로젝트 루트에서 실행한다.
```bash
docker compose -f compose.dev.yaml up -d --build
```

## 설정 (환경 변수)
- `SPRING_PROFILES_ACTIVE` - 활성 프로파일 (예: `dev`, `prod`)
- 데이터베이스 연결: `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD`
- JWT/보안 관련: `JWT_SECRET`, `JWT_EXPIRATION_MS` 등 (환경에 따라 다름)

민감한 값은 환경 변수 또는 시크릿 매니저를 사용한다.

## API 문서
애플리케이션 실행 후 API 문서(Swagger UI)를 확인한다: `http://localhost:8080/swagger-ui.html`

## 테스트
단위/통합 테스트는 Gradle로 실행한다.

```bash
./gradlew test
```

자세한 내용은 `docs/Development.md`, `docs/Test.md`를 참고한다.

## 로그 및 헬스 체크
- 기본 헬스 체크 엔드포인트: `/actuator/health` (Actuator가 활성화된 경우)
- 메트릭 및 상태 정보는 Actuator 설정에 따라 노출됩니다.

## 기여 및 코드 스타일
- 코드 포맷: `./gradlew spotlessApply`(Spotless 설정이 있는 경우)
- 커밋 메시지: 간결하게 작성한다

자세한 개발/테스트 지침은 `docs/Development.md`, `docs/Test.md`를 참고한다.
