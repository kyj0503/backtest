package com.webproject.backtest_be_spring.community.domain.repository;

import com.webproject.backtest_be_spring.community.domain.model.CommentLike;
import java.util.Optional;

public interface CommentLikeRepository {

    CommentLike save(CommentLike like);

    void delete(CommentLike like);

    Optional<CommentLike> findByCommentIdAndUserId(Long commentId, Long userId);

    boolean existsByCommentIdAndUserId(Long commentId, Long userId);

    long countByCommentId(Long commentId);
}
