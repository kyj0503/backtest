package com.webproject.backtest_be_spring.user.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Objects;

@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50, unique = true)
    private String username;

    @Column(nullable = false, length = 255, unique = true)
    private String email;

    @Column(name = "password_hash", nullable = false, columnDefinition = "VARBINARY(255)")
    private byte[] passwordHash;

    @Column(name = "password_salt", nullable = false, columnDefinition = "VARBINARY(128)")
    private byte[] passwordSalt;

    @Column(name = "password_algo", nullable = false, length = 50)
    private String passwordAlgo = "bcrypt";

    @Column(name = "profile_image", length = 500)
    private String profileImage;

    @Convert(converter = InvestmentTypeConverter.class)
    @Column(name = "investment_type", length = 20)
    private InvestmentType investmentType = InvestmentType.BALANCED;

    @Column(name = "is_admin", nullable = false)
    private boolean admin;

    @Column(name = "is_active", nullable = false)
    private boolean active = true;

    @Column(name = "is_email_verified", nullable = false)
    private boolean emailVerified;

    @Column(name = "last_login_at")
    private Instant lastLoginAt;

    @Column(name = "is_deleted", nullable = false)
    private boolean deleted;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected User() {
    }

    private User(String username, String email, byte[] passwordHash, byte[] passwordSalt, InvestmentType investmentType) {
        this.username = username;
        this.email = email;
        this.passwordHash = passwordHash;
        this.passwordSalt = passwordSalt;
        this.investmentType = investmentType == null ? InvestmentType.BALANCED : investmentType;
    }

    public static User create(String username, String email, String encodedPassword, byte[] salt, InvestmentType investmentType) {
        Objects.requireNonNull(encodedPassword, "encodedPassword must not be null");
        return new User(
                username,
                email,
                encodedPassword.getBytes(StandardCharsets.UTF_8),
                salt,
                investmentType);
    }

    @PrePersist
    public void prePersist() {
        Instant now = Instant.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public String getUsername() {
        return username;
    }

    public String getEmail() {
        return email;
    }

    public byte[] getPasswordHash() {
        return passwordHash;
    }

    public byte[] getPasswordSalt() {
        return passwordSalt;
    }

    public String getPasswordAlgo() {
        return passwordAlgo;
    }

    public String getProfileImage() {
        return profileImage;
    }

    public InvestmentType getInvestmentType() {
        return investmentType;
    }

    public boolean isAdmin() {
        return admin;
    }

    public boolean isActive() {
        return active;
    }

    public boolean isEmailVerified() {
        return emailVerified;
    }

    public Instant getLastLoginAt() {
        return lastLoginAt;
    }

    public boolean isDeleted() {
        return deleted;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void markLogin(Instant loginAt) {
        this.lastLoginAt = loginAt;
    }

    public void updateProfile(String username, InvestmentType investmentType, String profileImage) {
        if (username != null) {
            this.username = username;
        }
        if (investmentType != null) {
            this.investmentType = investmentType;
        }
        if (profileImage != null) {
            this.profileImage = profileImage;
        }
    }

    public void deactivate() {
        this.active = false;
    }

    public void setEmailVerified(boolean emailVerified) {
        this.emailVerified = emailVerified;
    }

    public void changePassword(String encodedPassword, byte[] salt, String algorithm) {
        this.passwordHash = encodedPassword.getBytes(StandardCharsets.UTF_8);
        this.passwordSalt = salt;
        this.passwordAlgo = algorithm;
    }
}
