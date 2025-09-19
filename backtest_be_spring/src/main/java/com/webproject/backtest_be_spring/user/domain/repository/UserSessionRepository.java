package com.webproject.backtest_be_spring.user.domain.repository;

import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.model.UserSession;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserSessionRepository extends JpaRepository<UserSession, Long> {

    Optional<UserSession> findByRefreshTokenAndRevokedIsFalse(String refreshToken);

    List<UserSession> findAllByUserAndRevokedIsFalseAndRefreshExpiresAtAfter(User user, Instant now);
}
