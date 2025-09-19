package com.webproject.backtest_be_spring.community.infrastructure.repository;

import com.webproject.backtest_be_spring.community.domain.model.CommentLike;
import com.webproject.backtest_be_spring.community.domain.repository.CommentLikeRepository;
import java.util.Optional;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class CommentLikeRepositoryAdapter implements CommentLikeRepository {

    private final JpaCommentLikeRepository jpa;

    public CommentLikeRepositoryAdapter(JpaCommentLikeRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public CommentLike save(CommentLike like) {
        return jpa.save(like);
    }

    @Override
    @Transactional
    public void delete(CommentLike like) {
        jpa.delete(like);
    }

    @Override
    public Optional<CommentLike> findByCommentIdAndUserId(Long commentId, Long userId) {
        return jpa.findByCommentIdAndUserId(commentId, userId);
    }

    @Override
    public boolean existsByCommentIdAndUserId(Long commentId, Long userId) {
        return jpa.existsByCommentIdAndUserId(commentId, userId);
    }

    @Override
    public long countByCommentId(Long commentId) {
        return jpa.countByCommentId(commentId);
    }
}
