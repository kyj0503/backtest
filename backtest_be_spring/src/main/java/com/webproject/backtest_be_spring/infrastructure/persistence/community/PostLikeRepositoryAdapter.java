package com.webproject.backtest_be_spring.infrastructure.persistence.community;

import com.webproject.backtest_be_spring.domain.community.model.PostLike;
import com.webproject.backtest_be_spring.domain.community.repository.PostLikeRepository;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class PostLikeRepositoryAdapter implements PostLikeRepository {

    private final JpaPostLikeRepository delegate;

    public PostLikeRepositoryAdapter(JpaPostLikeRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public PostLike save(PostLike like) {
        return delegate.save(like);
    }

    @Override
    public void delete(PostLike like) {
        delegate.delete(like);
    }

    @Override
    public Optional<PostLike> findByPostIdAndUserId(Long postId, Long userId) {
        return delegate.findByPostIdAndUserId(postId, userId);
    }

    @Override
    public boolean existsByPostIdAndUserId(Long postId, Long userId) {
        return delegate.existsByPostIdAndUserId(postId, userId);
    }

    @Override
    public long countByPostId(Long postId) {
        return delegate.countByPostId(postId);
    }
}
