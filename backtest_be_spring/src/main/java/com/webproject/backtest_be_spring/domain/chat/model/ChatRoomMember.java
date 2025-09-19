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
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "chat_room_members")
public class ChatRoomMember {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "room_id", nullable = false)
    private ChatRoom room;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ChatMemberRole role = ChatMemberRole.MEMBER;

    @Column(name = "joined_at", nullable = false)
    private Instant joinedAt;

    @Column(name = "last_read_at")
    private Instant lastReadAt;

    @Column(name = "is_active", nullable = false)
    private boolean active = true;

    protected ChatRoomMember() {
    }

    private ChatRoomMember(ChatRoom room, User user, ChatMemberRole role) {
        this.room = room;
        this.user = user;
        this.role = role == null ? ChatMemberRole.MEMBER : role;
    }

    public static ChatRoomMember create(ChatRoom room, User user, ChatMemberRole role) {
        return new ChatRoomMember(room, user, role);
    }

    @PrePersist
    public void onCreate() {
        this.joinedAt = Instant.now();
    }

    public void updateRole(ChatMemberRole role) {
        if (role != null) {
            this.role = role;
        }
    }

    public void markInactive() {
        this.active = false;
    }

    public void updateLastReadAt(Instant lastReadAt) {
        this.lastReadAt = lastReadAt;
    }

    public void activate() {
        this.active = true;
        this.joinedAt = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public ChatRoom getRoom() {
        return room;
    }

    public User getUser() {
        return user;
    }

    public ChatMemberRole getRole() {
        return role;
    }

    public Instant getJoinedAt() {
        return joinedAt;
    }

    public Instant getLastReadAt() {
        return lastReadAt;
    }

    public boolean isActive() {
        return active;
    }
}
