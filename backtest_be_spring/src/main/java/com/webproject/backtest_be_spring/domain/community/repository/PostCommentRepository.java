package com.webproject.backtest_be_spring.domain.community.repository;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostComment;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PostCommentRepository extends JpaRepository<PostComment, Long> {

    Page<PostComment> findByPostAndDeletedFalse(Post post, Pageable pageable);

    List<PostComment> findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(Post post);

    List<PostComment> findByParentAndDeletedFalseOrderByCreatedAtAsc(PostComment parent);

    Optional<PostComment> findByIdAndDeletedFalse(Long id);

    long countByPostAndDeletedFalse(Post post);

    long countByDeletedFalse();
}
