# Operations Guide — Spring Boot service

Deployment/build:
- Build jar: `./gradlew bootJar` then run `java -jar build/libs/*.jar`.

Health endpoints:
- If Spring Actuator is enabled, check `http://localhost:8080/actuator/health`.

Logging and troubleshooting:
- Check application logs for stack traces. Use `--stacktrace` with Gradle tasks during build.
