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
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@Tag(name = "Authentication", description = "회원 인증 및 토큰 발급 API")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @Operation(summary = "회원 가입", description = "신규 사용자를 등록하고 액세스/리프레시 토큰을 발급합니다.")
    @PostMapping("/signup")
    public ResponseEntity<AuthResponse> signUp(@Valid @RequestBody SignUpRequest request) {
        AuthResult result = authService.register(new RegisterUserCommand(
                request.username(),
                request.email(),
                request.password(),
                parseInvestmentType(request.investmentType())));
        return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(result));
    }

    @Operation(summary = "이메일 로그인", description = "이메일과 비밀번호로 로그인하여 토큰을 발급받습니다.")
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        AuthResult result = authService.login(new LoginCommand(request.email(), request.password()));
        return ResponseEntity.ok(toResponse(result));
    }

    @Operation(summary = "토큰 갱신", description = "리프레시 토큰을 사용해 새로운 액세스/리프레시 토큰을 발급합니다.")
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
