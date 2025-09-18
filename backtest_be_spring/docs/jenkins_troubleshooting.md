# Jenkins Troubleshooting — Spring Boot service

This file collects common Jenkins build/run issues for the Spring Boot app.

Common fixes:
- Ensure Gradle wrapper is executable (`chmod +x gradlew`) on the agent.
- Check Java version compatibility (use JDK 17).
- Increase heap if builds fail with OOM in Gradle daemon.
