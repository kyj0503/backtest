package com.webproject.backtest_be_spring.domain.community.model;

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
@Table(name = "posts")
public class Post {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User author;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private PostCategory category = PostCategory.GENERAL;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, columnDefinition = "MEDIUMTEXT")
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(name = "content_type", nullable = false, length = 20)
    private PostContentType contentType = PostContentType.MARKDOWN;

    @Column(name = "view_count", nullable = false)
    private long viewCount = 0;

    @Column(name = "like_count", nullable = false)
    private long likeCount = 0;

    @Column(name = "comment_count", nullable = false)
    private long commentCount = 0;

    @Column(name = "is_pinned", nullable = false)
    private boolean pinned = false;

    @Column(name = "is_featured", nullable = false)
    private boolean featured = false;

    @Column(name = "is_deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private Instant deletedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected Post() {
    }

    private Post(User author, PostCategory category, String title, String content, PostContentType contentType,
            boolean pinned, boolean featured) {
        this.author = author;
        this.category = category;
        this.title = title;
        this.content = content;
        this.contentType = contentType;
        this.pinned = pinned;
        this.featured = featured;
    }

    public static Post create(User author, PostCategory category, String title, String content,
            PostContentType contentType, boolean pinned, boolean featured) {
        return new Post(author, category, title, content, contentType, pinned, featured);
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

    public void update(String title, String content, PostCategory category, PostContentType contentType,
            boolean pinned, boolean featured) {
        this.title = title;
        this.content = content;
        this.category = category;
        this.contentType = contentType;
        this.pinned = pinned;
        this.featured = featured;
    }

    public void markDeleted() {
        this.deleted = true;
        this.deletedAt = Instant.now();
    }

    public boolean isOwnedBy(Long userId) {
        return author != null && author.getId().equals(userId);
    }

    public void incrementViewCount() {
        this.viewCount++;
    }

    public void incrementLikeCount() {
        this.likeCount++;
    }

    public void decrementLikeCount() {
        if (this.likeCount > 0) {
            this.likeCount--;
        }
    }

    public void incrementCommentCount() {
        this.commentCount++;
    }

    public void decrementCommentCount() {
        if (this.commentCount > 0) {
            this.commentCount--;
        }
    }

    public Long getId() {
        return id;
    }

    public User getAuthor() {
        return author;
    }

    public PostCategory getCategory() {
        return category;
    }

    public String getTitle() {
        return title;
    }

    public String getContent() {
        return content;
    }

    public PostContentType getContentType() {
        return contentType;
    }

    public long getViewCount() {
        return viewCount;
    }

    public long getLikeCount() {
        return likeCount;
    }

    public long getCommentCount() {
        return commentCount;
    }

    public boolean isPinned() {
        return pinned;
    }

    public boolean isFeatured() {
        return featured;
    }

    public boolean isDeleted() {
        return deleted;
    }

    public Instant getDeletedAt() {
        return deletedAt;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
