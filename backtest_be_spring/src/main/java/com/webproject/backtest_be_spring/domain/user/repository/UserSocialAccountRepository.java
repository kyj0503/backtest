package com.webproject.backtest_be_spring.domain.user.repository;

import com.webproject.backtest_be_spring.domain.user.UserSocialAccount;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserSocialAccountRepository extends JpaRepository<UserSocialAccount, Long> {

    Optional<UserSocialAccount> findByProviderAndProviderId(UserSocialAccount.Provider provider, String providerId);
}
