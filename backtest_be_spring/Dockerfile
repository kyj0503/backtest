FROM eclipse-temurin:17-jdk-jammy

WORKDIR /app

# Use dedicated Gradle cache directory outside of source tree
ENV GRADLE_USER_HOME=/home/gradle/.gradle
RUN mkdir -p ${GRADLE_USER_HOME} && chown -R root:root ${GRADLE_USER_HOME}

# Copy Gradle wrapper and build files
COPY gradlew gradlew
COPY gradle gradle
COPY build.gradle settings.gradle ./
COPY src ./src

# Make wrapper executable
RUN chmod +x ./gradlew

# Build the application
RUN ./gradlew bootJar -x test --no-daemon

# Run the jar
EXPOSE 8002
CMD ["java", "-jar", "build/libs/backtest-be-spring-0.0.1-SNAPSHOT.jar"]
