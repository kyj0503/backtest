# 02. 개발 가이드 — Spring Boot

- JDK 17+

빠른 시작
```bash
cd backtest_be_spring
./gradlew bootRun
```

빌드/테스트
```bash
./gradlew test
./gradlew bootJar
# 개발 가이드 — Spring Boot

이 문서는 로컬 개발 환경 설정, 주요 디렉토리 구조, 설정 파일, 테스트 및 디버깅 방법을 정리합니다.

## 요구 사항
- Java 17 이상
- Gradle Wrapper (프로젝트에 포함)
- (선택) Docker 및 Docker Compose — 전체 스택 연동 시 사용

## 주요 디렉토리
- `src/main/java` - 애플리케이션 소스 코드
- `src/main/resources` - 설정(application.yml), 정적 리소스
- `src/test/java` - 단위/통합 테스트
- `build.gradle`, `settings.gradle` - 빌드 스크립트

## 빠른 시작 (로컬)
프로젝트 루트에서 서비스 디렉터리로 이동한 뒤 Gradle Wrapper로 애플리케이션을 실행합니다.

```bash
cd backtest_be_spring
./gradlew bootRun
```

실행 시 기본 포트(8080)로 서비스가 올라옵니다. 환경 프로파일을 지정하려면 아래처럼 실행하세요.

```bash
SPRING_PROFILES_ACTIVE=dev ./gradlew bootRun
```

## 빌드 (프로덕션용)
JAR 파일을 생성하고 실행합니다.

```bash
./gradlew bootJar
java -jar build/libs/*.jar
```

## 테스트
단위 및 통합 테스트는 Gradle로 실행합니다.

```bash
./gradlew test
```

테스트 리포트는 `build/reports/tests/test/index.html`에서 확인하세요.

## 환경 및 설정 관리
- 기본 설정은 `src/main/resources/application.yml`에 있습니다. 환경별 설정 파일(`application-dev.yml`, `application-prod.yml`)을 사용해 프로파일을 분리하세요.
- 민감한 값(비밀번호, 시크릿)은 환경 변수 또는 시크릿 매니저를 사용하세요.

예시 (application.yml 일부):

```yaml
spring:
	datasource:
		url: jdbc:mysql://localhost:3306/backtest_db
		username: user
		password: pass
	jpa:
		hibernate:
			ddl-auto: update
```

## 데이터베이스 초기화
- 프로젝트 루트의 `database/` 폴더에 있는 SQL 스크립트(`01_schema.sql`, `02_yfinance.sql`)를 이용해 로컬 DB를 초기화할 수 있습니다.
- Docker Compose를 이용하면 MySQL 컨테이너와 함께 편리하게 개발 환경을 구성할 수 있습니다.

## 로컬 개발 팁
- IDE(예: IntelliJ, VSCode)에서 Gradle 실행/디버그 구성을 사용하세요.
- `spring-boot-devtools`를 추가하면 코드 변경 시 자동 재시작으로 개발 속도가 빨라집니다.
- 로그 레벨과 포맷은 `application.yml` 또는 `logback-spring.xml`에서 설정하세요.

## 흔한 문제와 해결 방법
- 포트 충돌: `server.port`를 변경하거나 사용 중인 프로세스를 종료하세요.
- DB 접속 오류: `SPRING_DATASOURCE_URL`/자격증명과 DB 서비스 상태를 확인하세요.
- 의존성/빌드 실패: `./gradlew clean build --refresh-dependencies`로 캐시를 초기화하고 재시도하세요.

더 자세한 테스트 및 CI 가이드는 `docs/Test.md`를 확인하세요.

환경 및 설정
- `src/main/resources/application.yml` 또는 환경변수로 구성
