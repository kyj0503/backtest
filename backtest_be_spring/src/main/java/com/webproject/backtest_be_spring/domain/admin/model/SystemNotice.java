package com.webproject.backtest_be_spring.domain.admin.model;

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
@Table(name = "system_notices")
public class SystemNotice {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(name = "notice_type", nullable = false, length = 20)
    private SystemNoticeType noticeType = SystemNoticeType.GENERAL;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SystemNoticePriority priority = SystemNoticePriority.NORMAL;

    @Column(name = "is_popup", nullable = false)
    private boolean popup = false;

    @Column(name = "is_pinned", nullable = false)
    private boolean pinned = false;

    @Column(name = "start_date")
    private Instant startDate;

    @Column(name = "end_date")
    private Instant endDate;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "author_id", nullable = false)
    private User author;

    @Column(name = "is_active", nullable = false)
    private boolean active = true;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected SystemNotice() {
    }

    private SystemNotice(String title, String content, SystemNoticeType noticeType, SystemNoticePriority priority,
            Boolean popup, Boolean pinned, Instant startDate, Instant endDate, Boolean active, User author) {
        this.title = title;
        this.content = content;
        this.noticeType = noticeType;
        this.priority = priority;
        this.popup = popup != null && popup;
        this.pinned = pinned != null && pinned;
        this.startDate = startDate;
        this.endDate = endDate;
        this.active = active == null || active;
        this.author = author;
    }

    public static SystemNotice create(String title, String content, SystemNoticeType noticeType,
            SystemNoticePriority priority, Boolean popup, Boolean pinned, Instant startDate, Instant endDate,
            Boolean active, User author) {
        return new SystemNotice(title, content, noticeType, priority, popup, pinned, startDate, endDate, active,
                author);
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

    public void update(String title, String content, SystemNoticeType type, SystemNoticePriority priority,
            Boolean popup, Boolean pinned, Instant startDate, Instant endDate, Boolean active) {
        if (title != null) {
            this.title = title;
        }
        if (content != null) {
            this.content = content;
        }
        if (type != null) {
            this.noticeType = type;
        }
        if (priority != null) {
            this.priority = priority;
        }
        if (popup != null) {
            this.popup = popup;
        }
        if (pinned != null) {
            this.pinned = pinned;
        }
        if (startDate != null) {
            this.startDate = startDate;
        }
        if (endDate != null) {
            this.endDate = endDate;
        }
        if (active != null) {
            this.active = active;
        }
    }

    public Long getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getContent() {
        return content;
    }

    public SystemNoticeType getNoticeType() {
        return noticeType;
    }

    public SystemNoticePriority getPriority() {
        return priority;
    }

    public boolean isPopup() {
        return popup;
    }

    public boolean isPinned() {
        return pinned;
    }

    public Instant getStartDate() {
        return startDate;
    }

    public Instant getEndDate() {
        return endDate;
    }

    public User getAuthor() {
        return author;
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
