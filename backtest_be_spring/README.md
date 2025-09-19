# Spring Boot 커뮤니티 백엔드 (backtest_be_spring)

커뮤니티, 채팅, 인증 기능을 담당하는 Spring Boot 기반 백엔드 서비스입니다.

## 빠른 시작
```bash
# 로컬 실행
./gradlew bootRun

# JAR 빌드 후 실행
./gradlew bootJar
java -jar build/libs/*.jar
```

## 주요 기능
- 사용자 인증 및 회원 관리
- 커뮤니티 게시판
- 실시간 채팅
- Spring Security 기반 보안

## API 문서
서버 실행 후 `http://localhost:8080/swagger-ui.html`에서 확인

## 문서
자세한 내용은 [`docs/`](./docs/) 디렉터리를 참조하세요.