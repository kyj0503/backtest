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
