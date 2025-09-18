package com.webproject.backtest_be_spring.application.user;

import com.webproject.backtest_be_spring.application.auth.exception.UserAlreadyExistsException;
import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.application.user.command.UpdateUserProfileCommand;
import com.webproject.backtest_be_spring.application.user.dto.UserProfileDto;
import com.webproject.backtest_be_spring.domain.user.InvestmentType;
import com.webproject.backtest_be_spring.domain.user.User;
import com.webproject.backtest_be_spring.domain.user.repository.UserRepository;
import jakarta.transaction.Transactional;
import java.util.Optional;
import org.springframework.stereotype.Service;

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
