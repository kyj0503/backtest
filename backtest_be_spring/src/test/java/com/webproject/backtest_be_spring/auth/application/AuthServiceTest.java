package com.webproject.backtest_be_spring.auth.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.webproject.backtest_be_spring.auth.application.command.LoginCommand;
import com.webproject.backtest_be_spring.auth.application.command.RegisterUserCommand;
import com.webproject.backtest_be_spring.auth.application.command.TokenRefreshCommand;
import com.webproject.backtest_be_spring.auth.application.dto.AuthResult;
import com.webproject.backtest_be_spring.auth.application.exception.InvalidCredentialsException;
import com.webproject.backtest_be_spring.auth.application.exception.InvalidRefreshTokenException;
import com.webproject.backtest_be_spring.auth.application.exception.UserAlreadyExistsException;
import com.webproject.backtest_be_spring.common.security.JwtTokenProvider;
import com.webproject.backtest_be_spring.user.domain.model.UserSession;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import com.webproject.backtest_be_spring.user.domain.repository.UserSessionRepository;
import java.time.Instant;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class AuthServiceTest {

    @Autowired
    private AuthService authService;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private UserSessionRepository userSessionRepository;

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Nested
    @DisplayName("회원 가입")
    class Register {

        @Test
        @DisplayName("새 사용자는 세션과 토큰이 발급된다")
        void createsUserAndSession() {
            AuthResult result = register("alice", uniqueEmail(), "Password!234");

            assertThat(result.user().id()).isNotNull();
            assertThat(result.tokens().accessToken()).isNotBlank();
            assertThat(result.tokens().refreshToken()).isNotBlank();
            assertThat(userRepository.existsByEmail(result.user().email())).isTrue();
        }

        @Test
        @DisplayName("중복 이메일로는 가입할 수 없다")
        void failsOnDuplicateEmail() {
            String email = uniqueEmail();
            register("alice", email, "Password!234");

            RegisterUserCommand duplicate = registerCommand("alice", email, "Password!234");

            assertThatThrownBy(() -> authService.register(duplicate))
                    .isInstanceOf(UserAlreadyExistsException.class);
        }

        @Test
        @DisplayName("같은 사용자명으로는 재가입할 수 없다")
        void failsOnDuplicateUsername() {
            register("alice", uniqueEmail(), "Password!234");
            RegisterUserCommand duplicate = registerCommand("alice", uniqueEmail(), "Password!234");

            assertThatThrownBy(() -> authService.register(duplicate))
                    .isInstanceOf(UserAlreadyExistsException.class);
        }
    }

    @Nested
    @DisplayName("로그인")
    class Login {

        @Test
        @DisplayName("올바른 자격 증명으로 토큰을 획득한다")
        void returnsTokens() {
            String email = uniqueEmail();
            register("alice", email, "Password!234");

            AuthResult result = authService.login(new LoginCommand(email, "Password!234"));

            assertThat(result.tokens().accessToken()).isNotBlank();
            assertThat(result.tokens().refreshToken()).isNotBlank();
        }

        @Test
        @DisplayName("잘못된 비밀번호는 거부된다")
        void rejectsInvalidPassword() {
            String email = uniqueEmail();
            register("alice", email, "Password!234");

            assertThatThrownBy(() -> authService.login(new LoginCommand(email, "WrongPassword")))
                    .isInstanceOf(InvalidCredentialsException.class);
        }

        @Test
        @DisplayName("존재하지 않는 이메일은 인증에 실패한다")
        void rejectsUnknownEmail() {
            assertThatThrownBy(() -> authService.login(new LoginCommand(uniqueEmail(), "Password!234")))
                    .isInstanceOf(InvalidCredentialsException.class);
        }
    }

    @Nested
    @DisplayName("토큰 갱신")
    class RefreshToken {

        @Test
        @DisplayName("정상 리프레시 토큰은 새 토큰을 발급한다")
        void issuesNewTokens() {
            AuthResult initial = register("alice", uniqueEmail(), "Password!234");

            AuthResult refreshed = authService.refreshTokens(new TokenRefreshCommand(initial.tokens().refreshToken()));

            assertThat(refreshed.tokens().accessToken()).isNotEqualTo(initial.tokens().accessToken());
        }

        @Test
        @DisplayName("등록되지 않은 리프레시 토큰은 예외를 발생시킨다")
        void rejectsUnknownToken() {
            assertThatThrownBy(() -> authService.refreshTokens(new TokenRefreshCommand("missing-token")))
                    .isInstanceOf(InvalidRefreshTokenException.class);
        }

        @Test
        @DisplayName("만료된 리프레시 토큰은 세션을 폐기한다")
        void revokesExpiredSession() {
            AuthResult initial = register("alice", uniqueEmail(), "Password!234");

            UserSession session = userSessionRepository
                    .findByRefreshTokenAndRevokedIsFalse(initial.tokens().refreshToken())
                    .orElseThrow();

            session.updateTokens(
                    session.getAccessToken(),
                    session.getRefreshToken(),
                    Instant.now().minusSeconds(5),
                    Instant.now().minusSeconds(1));
            userSessionRepository.save(session);

            assertThatThrownBy(() -> authService.refreshTokens(new TokenRefreshCommand(session.getRefreshToken())))
                    .isInstanceOf(InvalidRefreshTokenException.class);

            UserSession updated = userSessionRepository.findById(session.getId()).orElseThrow();
            assertThat(updated.isRevoked()).isTrue();
        }

        @Test
        @DisplayName("리프레시 토큰의 사용자 정보가 세션과 다르면 세션을 폐기한다")
        void revokesWhenClaimsDoNotMatchSession() {
            AuthResult initial = register("alice", uniqueEmail(), "Password!234");

            UserSession session = userSessionRepository
                    .findByRefreshTokenAndRevokedIsFalse(initial.tokens().refreshToken())
                    .orElseThrow();

            String sessionId = String.valueOf(session.getId());
            String forgedAccess = tokenProvider.generateAccessToken(
                    999L,
                    "intruder",
                    "intruder@example.com",
                    Set.of("ROLE_USER"),
                    sessionId);
            String forgedRefresh = tokenProvider.generateRefreshToken(999L, sessionId);

            session.updateTokens(
                    forgedAccess,
                    forgedRefresh,
                    tokenProvider.getExpiry(forgedAccess),
                    tokenProvider.getExpiry(forgedRefresh));
            userSessionRepository.save(session);

            assertThatThrownBy(() -> authService.refreshTokens(new TokenRefreshCommand(forgedRefresh)))
                    .isInstanceOf(InvalidRefreshTokenException.class);

            UserSession updated = userSessionRepository.findById(session.getId()).orElseThrow();
            assertThat(updated.isRevoked()).isTrue();
        }
    }

    private AuthResult register(String username, String email, String password) {
        return authService.register(registerCommand(username, email, password));
    }

    private RegisterUserCommand registerCommand(String username, String email, String password) {
        return new RegisterUserCommand(username, email, password, Optional.empty());
    }

    private String uniqueEmail() {
        return "user" + UUID.randomUUID().toString().substring(0, 8) + "@example.com";
    }
}
