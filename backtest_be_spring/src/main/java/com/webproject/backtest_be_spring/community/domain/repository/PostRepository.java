package com.webproject.backtest_be_spring.community.domain.repository;

import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface PostRepository {

    Post save(Post post);

    Optional<Post> findById(Long id);

    Optional<Post> findByIdAndDeletedFalse(Long id);

    Page<Post> findByDeletedFalse(Pageable pageable);

    Page<Post> findByCategoryAndDeletedFalse(PostCategory category, Pageable pageable);

    Page<Post> search(String keyword, Pageable pageable);

    long countByDeletedFalse();

    void incrementViewCount(Long postId);

    void adjustLikeCount(Long postId, long delta);

    void adjustCommentCount(Long postId, long delta);
}
