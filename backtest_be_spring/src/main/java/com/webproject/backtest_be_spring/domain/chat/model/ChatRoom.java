package com.webproject.backtest_be_spring.domain.chat.model;

import com.webproject.backtest_be_spring.domain.user.model.User;
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
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "chat_rooms")
public class ChatRoom {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(name = "room_type", nullable = false, length = 20)
    private ChatRoomType roomType = ChatRoomType.PUBLIC;

    @Column(name = "max_members")
    private Integer maxMembers = 100;

    @Column(name = "current_members")
    private Integer currentMembers = 0;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by", nullable = false)
    private User createdBy;

    @Column(name = "is_active", nullable = false)
    private boolean active = true;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected ChatRoom() {
    }

    private ChatRoom(String name, String description, ChatRoomType roomType, Integer maxMembers, User createdBy) {
        this.name = name;
        this.description = description;
        this.roomType = roomType;
        this.maxMembers = maxMembers;
        this.createdBy = createdBy;
    }

    public static ChatRoom create(String name, String description, ChatRoomType roomType, Integer maxMembers,
            User creator) {
        return new ChatRoom(name, description, roomType, maxMembers, creator);
    }

    @PrePersist
    public void onCreate() {
        Instant now = Instant.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = Instant.now();
    }

    public void update(String name, String description, ChatRoomType roomType, Integer maxMembers, boolean active) {
        if (name != null) {
            this.name = name;
        }
        if (description != null) {
            this.description = description;
        }
        if (roomType != null) {
            this.roomType = roomType;
        }
        if (maxMembers != null) {
            this.maxMembers = maxMembers;
        }
        this.active = active;
    }

    public void incrementMembers() {
        if (currentMembers == null) {
            currentMembers = 0;
        }
        currentMembers++;
    }

    public void decrementMembers() {
        if (currentMembers == null || currentMembers <= 0) {
            currentMembers = 0;
        } else {
            currentMembers--;
        }
    }

    public boolean hasCapacity() {
        return maxMembers == null || currentMembers < maxMembers;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public ChatRoomType getRoomType() {
        return roomType;
    }

    public Integer getMaxMembers() {
        return maxMembers;
    }

    public Integer getCurrentMembers() {
        return currentMembers;
    }

    public User getCreatedBy() {
        return createdBy;
    }

    public boolean isActive() {
        return active;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
