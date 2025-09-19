package com.webproject.backtest_be_spring.community.infrastructure.repository;

import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostComment;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JpaPostCommentRepository extends JpaRepository<PostComment, Long> {

    Optional<PostComment> findByIdAndDeletedFalse(Long id);

    List<PostComment> findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(Post post);

    List<PostComment> findByParentAndDeletedFalseOrderByCreatedAtAsc(PostComment parent);

    Page<PostComment> findByPostAndDeletedFalse(Post post, Pageable pageable);

    long countByPostAndDeletedFalse(Post post);

    long countByDeletedFalse();
}
