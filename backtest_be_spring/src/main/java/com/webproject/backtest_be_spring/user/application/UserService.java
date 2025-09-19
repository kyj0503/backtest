package com.webproject.backtest_be_spring.user.application;

import com.webproject.backtest_be_spring.auth.application.exception.UserAlreadyExistsException;
import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.user.application.command.UpdateUserProfileCommand;
import com.webproject.backtest_be_spring.user.application.dto.UserProfileDto;
import com.webproject.backtest_be_spring.user.domain.model.InvestmentType;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import java.util.Optional;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional(readOnly = true)
    public UserProfileDto getProfile(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다."));
        return toDto(user);
    }

    public UserProfileDto updateProfile(Long userId, UpdateUserProfileCommand command) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다."));

        command.username().ifPresent(newUsername -> {
            if (!newUsername.equals(user.getUsername()) && userRepository.existsByUsername(newUsername)) {
                throw new UserAlreadyExistsException("이미 사용 중인 사용자명입니다.");
            }
        });

        Optional<InvestmentType> newInvestment = command.investmentType();
        user.updateProfile(
                command.username().orElse(null),
                newInvestment.orElse(null),
                command.profileImage().orElse(null));

        return toDto(user);
    }

    private UserProfileDto toDto(User user) {
        return new UserProfileDto(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getProfileImage(),
                user.getInvestmentType() == null ? null : user.getInvestmentType().toDatabaseValue(),
                user.isEmailVerified(),
                user.getCreatedAt(),
                user.getUpdatedAt());
    }
}
