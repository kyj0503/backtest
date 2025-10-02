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
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import com.webproject.backtest_be_spring.user.domain.repository.UserSessionRepository;
import com.webproject.backtest_be_spring.user.domain.model.UserSession;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
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

    @Test
    @DisplayName("회원 가입 시 사용자와 세션이 생성된다")
    void registerCreatesUserAndSession() {
        RegisterUserCommand command = new RegisterUserCommand(
                "alice",
                "alice@example.com",
                "Password!234",
                Optional.empty());

        AuthResult result = authService.register(command);

        assertThat(result.user().id()).isNotNull();
        assertThat(result.tokens().accessToken()).isNotBlank();
        assertThat(result.tokens().refreshToken()).isNotBlank();
        assertThat(userRepository.existsByEmail("alice@example.com")).isTrue();
    }

    @Test
    @DisplayName("중복 이메일 회원 가입 시 예외가 발생한다")
    void registerFailsOnDuplicateEmail() {
        RegisterUserCommand command = new RegisterUserCommand(
                "alice",
                "alice@example.com",
                "Password!234",
                Optional.empty());

        authService.register(command);

        assertThatThrownBy(() -> authService.register(command))
                .isInstanceOf(UserAlreadyExistsException.class);
    }

    @Test
    @DisplayName("로그인 성공 시 액세스/리프레시 토큰을 반환한다")
    void loginReturnsTokens() {
        RegisterUserCommand command = new RegisterUserCommand(
                "alice",
                "alice@example.com",
                "Password!234",
                Optional.empty());
        authService.register(command);

        AuthResult result = authService.login(new LoginCommand("alice@example.com", "Password!234"));

        assertThat(result.tokens().accessToken()).isNotBlank();
        assertThat(result.tokens().refreshToken()).isNotBlank();
    }

    @Test
    @DisplayName("잘못된 비밀번호로 로그인 시 예외가 발생한다")
    void loginFailsOnInvalidPassword() {
        RegisterUserCommand command = new RegisterUserCommand(
                "alice",
                "alice@example.com",
                "Password!234",
                Optional.empty());
        authService.register(command);

        assertThatThrownBy(() -> authService.login(new LoginCommand("alice@example.com", "WrongPassword")))
                .isInstanceOf(InvalidCredentialsException.class);
    }

    @Test
    @DisplayName("리프레시 토큰으로 새 토큰을 발급한다")
    void refreshTokenIssuesNewTokens() {
        RegisterUserCommand command = new RegisterUserCommand(
                "alice",
                "alice@example.com",
                "Password!234",
                Optional.empty());
        AuthResult initial = authService.register(command);

        AuthResult refreshed = authService.refreshTokens(new TokenRefreshCommand(initial.tokens().refreshToken()));

        assertThat(refreshed.tokens().accessToken()).isNotEqualTo(initial.tokens().accessToken());
    }

    @Test
    @DisplayName("등록되지 않은 리프레시 토큰은 예외를 발생시킨다")
    void refreshTokenFailsWhenTokenUnknown() {
        assertThatThrownBy(() -> authService.refreshTokens(new TokenRefreshCommand("missing-token")))
                .isInstanceOf(InvalidRefreshTokenException.class);
    }

    @Test
    @DisplayName("만료된 리프레시 토큰은 세션을 폐기한다")
    void refreshTokenFailsWhenExpired() {
        RegisterUserCommand command = new RegisterUserCommand(
                "alice",
                "alice@example.com",
                "Password!234",
                Optional.empty());
        AuthResult initial = authService.register(command);

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
}
