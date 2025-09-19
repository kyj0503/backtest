# 02. 개발 가이드 — Spring Boot 커뮤니티 서비스

## 요구 사항
- JDK 17+
- Gradle (래퍼 제공: `./gradlew`)

## 빠른 시작
```bash
cd backtest_be_spring
./gradlew bootRun
```

서버가 `http://localhost:8080`에서 실행됩니다.

## 빌드 및 배포
```bash
# 테스트 실행
./gradlew test

# JAR 파일 빌드
./gradlew bootJar

# 빌드된 JAR 실행
java -jar build/libs/*.jar
```

## API 문서
서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8080/swagger-ui.html`

Spring Security 설정에서 API 문서는 인증 없이 접근 가능하도록 예외 처리되어 있습니다.

## 개발 환경 설정

### IntelliJ IDEA
자동 재시작을 위해 `spring-boot-devtools`가 포함되어 있습니다:

1. `Settings > Build, Execution, Deployment > Compiler`
2. "Build project automatically" 체크
3. `Ctrl+Shift+A` → "Registry" 검색
4. `compiler.automake.allow.when.app.running` 활성화

이제 코드 수정 시 자동으로 애플리케이션이 재시작됩니다.

## 설정 파일
- 메인 설정: `src/main/resources/application.yml` (또는 `.properties`)
- 프로파일별 설정: `application-{profile}.yml`

## 패키지 구조
```
src/main/java/com/webproject/backtest_be_spring/
├── controller/     # REST API 컨트롤러
├── service/        # 비즈니스 로직
├── repository/     # 데이터 액세스
├── entity/         # JPA 엔티티
├── dto/           # 데이터 전송 객체
├── config/        # 설정 클래스
└── security/      # 보안 설정
```

## 헬스체크
Spring Actuator가 활성화된 경우:
```bash
curl http://localhost:8080/actuator/health
```

## 트러블슈팅
- 포트 충돌: `server.port` 속성 변경 또는 `SERVER_PORT` 환경변수 설정
- 빌드 오류: `./gradlew clean build --stacktrace`로 상세 오류 확인
- Gradle 권한 오류: `chmod +x gradlew`로 실행 권한 부여
