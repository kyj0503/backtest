package com.webproject.backtest_be_spring.user.presentation.api;

import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.user.application.UserService;
import com.webproject.backtest_be_spring.user.application.command.UpdateUserProfileCommand;
import com.webproject.backtest_be_spring.user.application.dto.UserProfileDto;
import com.webproject.backtest_be_spring.common.security.UserPrincipal;
import com.webproject.backtest_be_spring.user.domain.model.InvestmentType;
import com.webproject.backtest_be_spring.user.presentation.api.dto.UpdateProfileRequest;
import com.webproject.backtest_be_spring.user.presentation.api.dto.UserProfileResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.Optional;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "Users", description = "사용자 프로필 조회/수정 API")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @Operation(summary = "내 프로필 조회", description = "현재 로그인한 사용자의 프로필 정보를 반환합니다.")
    @GetMapping("/me")
    public ResponseEntity<UserProfileResponse> me(@AuthenticationPrincipal UserPrincipal principal) {
        if (principal == null) {
            throw new UserNotFoundException("인증 정보가 없습니다.");
        }
        UserProfileDto dto = userService.getProfile(principal.getId());
        return ResponseEntity.ok(toResponse(dto));
    }

    @Operation(summary = "내 프로필 수정", description = "닉네임, 프로필 이미지, 투자 성향 등을 수정합니다.")
    @PatchMapping("/me")
    public ResponseEntity<UserProfileResponse> updateProfile(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody UpdateProfileRequest request) {
        if (principal == null) {
            throw new UserNotFoundException("인증 정보가 없습니다.");
        }
        UpdateUserProfileCommand command = new UpdateUserProfileCommand(
                Optional.ofNullable(request.username()),
                Optional.ofNullable(request.profileImage()),
                parseInvestment(request.investmentType()));
        UserProfileDto dto = userService.updateProfile(principal.getId(), command);
        return ResponseEntity.ok(toResponse(dto));
    }

    private Optional<InvestmentType> parseInvestment(String investmentType) {
        if (investmentType == null || investmentType.isBlank()) {
            return Optional.empty();
        }
        return Optional.of(InvestmentType.fromDatabaseValue(investmentType));
    }

    private UserProfileResponse toResponse(UserProfileDto dto) {
        return new UserProfileResponse(
                dto.id(),
                dto.username(),
                dto.email(),
                dto.profileImage(),
                dto.investmentType(),
                dto.emailVerified(),
                dto.createdAt(),
                dto.updatedAt());
    }
}
