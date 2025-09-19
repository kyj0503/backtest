# Development Guide — Spring Boot service

Prerequisites:
- JDK 17+
- Gradle (wrapper provided: `./gradlew`)

Run locally:
```bash
cd backtest_be_spring
./gradlew bootRun
```

Run tests:
```bash
./gradlew test
```

Notes:
- Application properties are in `src/main/resources/application.properties`.
- Controllers and entrypoints are under `src/main/java/com/webproject/backtest_be_spring`.
- API 문서는 애플리케이션 실행 후 `http://localhost:8080/swagger-ui.html`에서 확인할 수 있습니다. (Spring Security가 인증을 요구하지 않도록 예외 처리되어 있습니다.)
