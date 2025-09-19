package com.webproject.backtest_be_spring.community.domain.repository;

import com.webproject.backtest_be_spring.community.domain.model.PostLike;
import java.util.Optional;

public interface PostLikeRepository {

    PostLike save(PostLike like);

    void delete(PostLike like);

    Optional<PostLike> findByPostIdAndUserId(Long postId, Long userId);

    boolean existsByPostIdAndUserId(Long postId, Long userId);

    long countByPostId(Long postId);
}
