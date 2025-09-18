package com.webproject.backtest_be_spring.presentation.user;

import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.application.user.UserService;
import com.webproject.backtest_be_spring.application.user.command.UpdateUserProfileCommand;
import com.webproject.backtest_be_spring.application.user.dto.UserProfileDto;
import com.webproject.backtest_be_spring.common.security.UserPrincipal;
import com.webproject.backtest_be_spring.domain.user.InvestmentType;
import com.webproject.backtest_be_spring.presentation.user.dto.UpdateProfileRequest;
import com.webproject.backtest_be_spring.presentation.user.dto.UserProfileResponse;
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
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/me")
    public ResponseEntity<UserProfileResponse> me(@AuthenticationPrincipal UserPrincipal principal) {
        if (principal == null) {
            throw new UserNotFoundException("인증 정보가 없습니다.");
        }
        UserProfileDto dto = userService.getProfile(principal.getId());
        return ResponseEntity.ok(toResponse(dto));
    }

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
