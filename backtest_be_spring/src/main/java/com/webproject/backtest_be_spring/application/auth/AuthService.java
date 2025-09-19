package com.webproject.backtest_be_spring.application.auth;

import com.webproject.backtest_be_spring.application.auth.command.LoginCommand;
import com.webproject.backtest_be_spring.application.auth.command.RegisterUserCommand;
import com.webproject.backtest_be_spring.application.auth.command.TokenRefreshCommand;
import com.webproject.backtest_be_spring.application.auth.dto.AuthResult;
import com.webproject.backtest_be_spring.application.auth.dto.TokenBundle;
import com.webproject.backtest_be_spring.application.auth.dto.UserSummary;
import com.webproject.backtest_be_spring.application.auth.exception.InvalidCredentialsException;
import com.webproject.backtest_be_spring.application.auth.exception.InvalidRefreshTokenException;
import com.webproject.backtest_be_spring.application.auth.exception.UserAlreadyExistsException;
import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.infrastructure.security.JwtTokenProvider;
import com.webproject.backtest_be_spring.domain.user.model.InvestmentType;
import com.webproject.backtest_be_spring.domain.user.model.User;
import com.webproject.backtest_be_spring.domain.user.model.UserSession;
import com.webproject.backtest_be_spring.domain.user.repository.UserRepository;
import com.webproject.backtest_be_spring.domain.user.repository.UserSessionRepository;
import io.jsonwebtoken.Claims;
import jakarta.transaction.Transactional;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class AuthService {

    private final UserRepository userRepository;
    private final UserSessionRepository userSessionRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider tokenProvider;

    public AuthService(
            UserRepository userRepository,
            UserSessionRepository userSessionRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider tokenProvider
    ) {
        this.userRepository = userRepository;
        this.userSessionRepository = userSessionRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenProvider = tokenProvider;
    }

    public AuthResult register(RegisterUserCommand command) {
        validateUniqueUser(command.email(), command.username());

        String encodedPassword = passwordEncoder.encode(command.password());
        byte[] salt = extractSalt(encodedPassword);
        InvestmentType investmentType = command.investmentType().orElse(InvestmentType.BALANCED);

        User user = User.create(command.username(), command.email(), encodedPassword, salt, investmentType);
        try {
            userRepository.save(user);
            UserSession session = createSessionForUser(user);
            return mapToAuthResult(user, session);
        } catch (DataIntegrityViolationException ex) {
            throw new UserAlreadyExistsException("이미 등록된 사용자입니다.", ex);
        }
    }

    public AuthResult login(LoginCommand command) {
        User user = userRepository.findByEmail(command.email())
                .orElseThrow(InvalidCredentialsException::new);

        String encodedPassword = new String(user.getPasswordHash(), StandardCharsets.UTF_8);
        if (!passwordEncoder.matches(command.password(), encodedPassword)) {
            throw new InvalidCredentialsException();
        }

        user.markLogin(Instant.now());

        UserSession session = createSessionForUser(user);
        return mapToAuthResult(user, session);
    }

    public AuthResult refreshTokens(TokenRefreshCommand command) {
        UserSession session = userSessionRepository
                .findByRefreshTokenAndRevokedIsFalse(command.refreshToken())
                .orElseThrow(InvalidRefreshTokenException::new);

        if (session.getRefreshExpiresAt() != null && session.getRefreshExpiresAt().isBefore(Instant.now())) {
            session.revoke();
            userSessionRepository.save(session);
            throw new InvalidRefreshTokenException();
        }

        if (!tokenProvider.isTokenValid(command.refreshToken())) {
            session.revoke();
            userSessionRepository.save(session);
            throw new InvalidRefreshTokenException();
        }

        Claims claims = tokenProvider.parseClaims(command.refreshToken());
        if (!String.valueOf(session.getUser().getId()).equals(claims.getSubject())) {
            session.revoke();
            userSessionRepository.save(session);
            throw new InvalidRefreshTokenException();
        }

        String sessionId = String.valueOf(session.getId());
        String newAccessToken = tokenProvider.generateAccessToken(
                session.getUser().getId(),
                session.getUser().getUsername(),
                session.getUser().getEmail(),
                rolesFor(session.getUser()),
                String.valueOf(session.getId()));
        String newRefreshToken = tokenProvider.generateRefreshToken(session.getUser().getId(), sessionId);

        Instant accessExpiry = tokenProvider.getExpiry(newAccessToken);
        Instant refreshExpiry = tokenProvider.getExpiry(newRefreshToken);

        session.updateTokens(newAccessToken, newRefreshToken, accessExpiry, refreshExpiry);
        userSessionRepository.save(session);

        return mapToAuthResult(session.getUser(), session);
    }

    private void validateUniqueUser(String email, String username) {
        if (userRepository.existsByEmail(email)) {
            throw new UserAlreadyExistsException("이미 등록된 이메일입니다.");
        }
        if (userRepository.existsByUsername(username)) {
            throw new UserAlreadyExistsException("이미 사용 중인 사용자명입니다.");
        }
    }

    private UserSession createSessionForUser(User user) {
        UserSession session = UserSession.newSession(user);

        String placeholderAccess = "PENDING-" + UUID.randomUUID();
        String placeholderRefresh = "PENDING-" + UUID.randomUUID();
        Instant now = Instant.now();
        session.initializeTokens(placeholderAccess, placeholderRefresh, now, now);
        userSessionRepository.save(session);

        String sessionId = String.valueOf(session.getId());
        String accessToken = tokenProvider.generateAccessToken(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                rolesFor(user),
                sessionId);
        String refreshToken = tokenProvider.generateRefreshToken(user.getId(), sessionId);
        Instant accessExpiry = tokenProvider.getExpiry(accessToken);
        Instant refreshExpiry = tokenProvider.getExpiry(refreshToken);

        session.updateTokens(accessToken, refreshToken, accessExpiry, refreshExpiry);
        return userSessionRepository.save(session);
    }

    private Set<String> rolesFor(User user) {
        Set<String> roles = new HashSet<>();
        roles.add("ROLE_USER");
        if (user.isAdmin()) {
            roles.add("ROLE_ADMIN");
        }
        return roles;
    }

    private byte[] extractSalt(String encodedPassword) {
        if (encodedPassword == null || encodedPassword.length() < 29) {
            return encodedPassword == null ? new byte[0] : encodedPassword.getBytes(StandardCharsets.UTF_8);
        }
        String saltPart = encodedPassword.substring(7, 29);
        return saltPart.getBytes(StandardCharsets.UTF_8);
    }

    private AuthResult mapToAuthResult(User user, UserSession session) {
        return new AuthResult(
                new UserSummary(
                        user.getId(),
                        user.getUsername(),
                        user.getEmail(),
                        user.getProfileImage(),
                        user.getInvestmentType() == null ? null : user.getInvestmentType().toDatabaseValue(),
                        user.isEmailVerified()),
                new TokenBundle(
                        session.getAccessToken(),
                        session.getRefreshToken(),
                        session.getTokenType(),
                        session.getAccessExpiresAt(),
                        session.getRefreshExpiresAt()));
    }
}
