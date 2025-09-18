package com.webproject.backtest_be_spring.presentation.auth;

import com.webproject.backtest_be_spring.application.auth.AuthService;
import com.webproject.backtest_be_spring.application.auth.command.LoginCommand;
import com.webproject.backtest_be_spring.application.auth.command.RegisterUserCommand;
import com.webproject.backtest_be_spring.application.auth.command.TokenRefreshCommand;
import com.webproject.backtest_be_spring.application.auth.dto.AuthResult;
import com.webproject.backtest_be_spring.application.auth.dto.TokenBundle;
import com.webproject.backtest_be_spring.application.auth.dto.UserSummary;
import com.webproject.backtest_be_spring.domain.user.InvestmentType;
import com.webproject.backtest_be_spring.presentation.auth.dto.AuthResponse;
import com.webproject.backtest_be_spring.presentation.auth.dto.LoginRequest;
import com.webproject.backtest_be_spring.presentation.auth.dto.SignUpRequest;
import com.webproject.backtest_be_spring.presentation.auth.dto.TokenRefreshRequest;
import com.webproject.backtest_be_spring.presentation.auth.dto.TokenResponse;
import com.webproject.backtest_be_spring.presentation.auth.dto.UserResponse;
import jakarta.validation.Valid;
import java.util.Optional;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/signup")
    public ResponseEntity<AuthResponse> signUp(@Valid @RequestBody SignUpRequest request) {
        AuthResult result = authService.register(new RegisterUserCommand(
                request.username(),
                request.email(),
                request.password(),
                parseInvestmentType(request.investmentType())));
        return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(result));
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        AuthResult result = authService.login(new LoginCommand(request.email(), request.password()));
        return ResponseEntity.ok(toResponse(result));
    }

    @PostMapping("/token/refresh")
    public ResponseEntity<AuthResponse> refresh(@Valid @RequestBody TokenRefreshRequest request) {
        AuthResult result = authService.refreshTokens(new TokenRefreshCommand(request.refreshToken()));
        return ResponseEntity.ok(toResponse(result));
    }

    private Optional<InvestmentType> parseInvestmentType(String investmentType) {
        if (investmentType == null || investmentType.isBlank()) {
            return Optional.empty();
        }
        return Optional.of(InvestmentType.fromDatabaseValue(investmentType));
    }

    private AuthResponse toResponse(AuthResult result) {
        UserSummary user = result.user();
        TokenBundle tokens = result.tokens();
        UserResponse userResponse = new UserResponse(
                user.id(),
                user.username(),
                user.email(),
                user.profileImage(),
                user.investmentType(),
                user.emailVerified());
        TokenResponse tokenResponse = new TokenResponse(
                tokens.accessToken(),
                tokens.refreshToken(),
                tokens.tokenType(),
                tokens.accessTokenExpiresAt(),
                tokens.refreshTokenExpiresAt());
        return new AuthResponse(userResponse, tokenResponse);
    }
}
