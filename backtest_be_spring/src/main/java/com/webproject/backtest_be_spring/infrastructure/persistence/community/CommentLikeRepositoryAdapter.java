package com.webproject.backtest_be_spring.infrastructure.persistence.community;

import com.webproject.backtest_be_spring.domain.community.model.CommentLike;
import com.webproject.backtest_be_spring.domain.community.repository.CommentLikeRepository;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class CommentLikeRepositoryAdapter implements CommentLikeRepository {

    private final JpaCommentLikeRepository delegate;

    public CommentLikeRepositoryAdapter(JpaCommentLikeRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public CommentLike save(CommentLike like) {
        return delegate.save(like);
    }

    @Override
    public void delete(CommentLike like) {
        delegate.delete(like);
    }

    @Override
    public Optional<CommentLike> findByCommentIdAndUserId(Long commentId, Long userId) {
        return delegate.findByCommentIdAndUserId(commentId, userId);
    }

    @Override
    public boolean existsByCommentIdAndUserId(Long commentId, Long userId) {
        return delegate.existsByCommentIdAndUserId(commentId, userId);
    }

    @Override
    public long countByCommentId(Long commentId) {
        return delegate.countByCommentId(commentId);
    }
}
