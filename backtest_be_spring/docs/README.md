# 01. Spring Boot 백엔드 문서 개요 (backtest_be_spring)

이 디렉터리는 커뮤니티, 채팅, 멤버 관리, 인증 기능을 담당하는 Spring Boot 백엔드 관련 문서를 모아둔 장소입니다. 실제 코드와 설정에 맞춰 작성되어 있으며, 빠르게 개발 환경을 세팅하고 API를 이해하는 데 목적이 있습니다.

## 기술 스택
- Java 17, Spring Boot 3.4.3
- Spring Web, Spring Data JPA, Spring Security
- Spring Validation
- Gradle 빌드 시스템

## 실행 방법
- 로컬 실행: `./gradlew bootRun` (포트 8080)
- JAR 빌드: `./gradlew bootJar`
- 테스트: `./gradlew test`
- 헬스체크: `GET /actuator/health` (Actuator 활성화 시)

## 디렉터리 개요
- `src/main/java/`: Java 소스 코드
- `src/main/resources/`: 설정 파일 (application.yml/properties)
- `src/test/`: 테스트 코드

## 주요 기능
- 커뮤니티 게시판 및 댓글
- 실시간 채팅
- 사용자 인증 및 세션 관리
- 회원 관리

## 환경변수
Spring Boot 표준 설정을 따라 `application.yml` 또는 환경변수로 설정:
- `SERVER_PORT`: 서버 포트 (기본 8080)
- 데이터베이스 연결 정보
- Spring Security 설정

## 문서 색인
- 02. 개발 가이드: `./DEVELOPMENT_GUIDE.md`
