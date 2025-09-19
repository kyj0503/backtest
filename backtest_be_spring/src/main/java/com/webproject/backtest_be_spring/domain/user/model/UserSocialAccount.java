package com.webproject.backtest_be_spring.domain.user.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "user_social_accounts")
public class UserSocialAccount {

    public enum Provider {
        GOOGLE,
        KAKAO,
        NAVER,
        GITHUB
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Provider provider;

    @Column(name = "provider_id", nullable = false, length = 100)
    private String providerId;

    @Column(name = "provider_email", length = 255)
    private String providerEmail;

    @Column(name = "provider_data", columnDefinition = "TEXT")
    private String providerData;

    @Column(name = "is_active", nullable = false)
    private boolean active = true;

    @Column(name = "linked_at", nullable = false)
    private Instant linkedAt;

    @Column(name = "last_used_at")
    private Instant lastUsedAt;

    protected UserSocialAccount() {
    }

    public UserSocialAccount(User user, Provider provider, String providerId) {
        this.user = user;
        this.provider = provider;
        this.providerId = providerId;
    }

    @PrePersist
    public void prePersist() {
        if (linkedAt == null) {
            linkedAt = Instant.now();
        }
    }

    public void markUsed() {
        this.lastUsedAt = Instant.now();
    }
}
