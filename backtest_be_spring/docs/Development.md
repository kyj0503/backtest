# 개발 가이드 — Spring Boot

로컬 개발, 디렉터리, 설정, 테스트 실행 방법을 정리한다.

## 요구 사항
- Java 17+
- Gradle Wrapper
- (선택) Docker, Docker Compose

## 디렉터리
- `src/main/java` 애플리케이션 소스
- `src/main/resources` 설정(application.yml), 정적 리소스
- `src/test/java` 테스트 코드
- `build.gradle`, `settings.gradle` 빌드 스크립트

## 빠른 시작(로컬)
```bash
cd backtest_be_spring
./gradlew bootRun
```

기본 포트는 8080이다. 프로파일 지정 예시:
```bash
SPRING_PROFILES_ACTIVE=dev ./gradlew bootRun
```

## 빌드(프로덕션)
```bash
./gradlew bootJar
java -jar build/libs/*.jar
```

## 테스트
```bash
./gradlew test
```

테스트 리포트: `build/reports/tests/test/index.html`

## 환경/설정
- 기본 설정: `src/main/resources/application.yml`
- 환경별 설정: `application-dev.yml`, `application-prod.yml`
- 민감한 값은 환경 변수 또는 시크릿 매니저 사용

예시(application.yml 일부)
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
- 루트 `database/`의 SQL 스크립트(`01_schema.sql`, `02_yfinance.sql`)로 초기화한다.
- 개발 스택은 Compose로 MySQL을 기동할 수 있다. dev Compose는 Spring 컨테이너를 포함하지 않는다.

## 개발 팁
- IDE에서 Gradle 실행/디버그 구성을 사용한다.
- `spring-boot-devtools`로 코드 변경 자동 재시작을 활성화한다.
- 로그 레벨/포맷은 `application.yml` 또는 `logback-spring.xml`에서 조정한다.

## 문제 해결
- 포트 충돌: `server.port` 변경 또는 점유 프로세스 종료
- DB 접속 오류: `SPRING_DATASOURCE_*` 값 및 DB 상태 확인
- 의존성/빌드 실패: `./gradlew clean build --refresh-dependencies`

자세한 테스트/CI 안내는 `docs/Test.md`를 참고한다.
