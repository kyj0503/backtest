package com.webproject.backtest_be_spring.community.domain.repository;

import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostComment;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface PostCommentRepository {

    PostComment save(PostComment comment);

    Optional<PostComment> findById(Long id);

    Optional<PostComment> findByIdAndDeletedFalse(Long id);

    List<PostComment> findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(Post post);

    List<PostComment> findByParentAndDeletedFalseOrderByCreatedAtAsc(PostComment parent);

    Page<PostComment> findByPostAndDeletedFalse(Post post, Pageable pageable);

    long countByPostAndDeletedFalse(Post post);

    long countByDeletedFalse();
}
