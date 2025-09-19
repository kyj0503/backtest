package com.webproject.backtest_be_spring.infrastructure.community.repository;

import com.webproject.backtest_be_spring.domain.community.model.PostLike;
import com.webproject.backtest_be_spring.domain.community.repository.PostLikeRepository;
import java.util.Optional;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class PostLikeRepositoryAdapter implements PostLikeRepository {

    private final JpaPostLikeRepository jpa;

    public PostLikeRepositoryAdapter(JpaPostLikeRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public PostLike save(PostLike like) {
        return jpa.save(like);
    }

    @Override
    @Transactional
    public void delete(PostLike like) {
        jpa.delete(like);
    }

    @Override
    public Optional<PostLike> findByPostIdAndUserId(Long postId, Long userId) {
        return jpa.findByPostIdAndUserId(postId, userId);
    }

    @Override
    public boolean existsByPostIdAndUserId(Long postId, Long userId) {
        return jpa.existsByPostIdAndUserId(postId, userId);
    }

    @Override
    public long countByPostId(Long postId) {
        return jpa.countByPostId(postId);
    }
}
