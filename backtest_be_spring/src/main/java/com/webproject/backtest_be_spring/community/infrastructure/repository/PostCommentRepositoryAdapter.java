package com.webproject.backtest_be_spring.community.infrastructure.repository;

import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostComment;
import com.webproject.backtest_be_spring.community.domain.repository.PostCommentRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class PostCommentRepositoryAdapter implements PostCommentRepository {

    private final JpaPostCommentRepository jpa;

    public PostCommentRepositoryAdapter(JpaPostCommentRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public PostComment save(PostComment comment) {
        return jpa.save(comment);
    }

    @Override
    public Optional<PostComment> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Optional<PostComment> findByIdAndDeletedFalse(Long id) {
        return jpa.findByIdAndDeletedFalse(id);
    }

    @Override
    public List<PostComment> findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(Post post) {
        return jpa.findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(post);
    }

    @Override
    public List<PostComment> findByParentAndDeletedFalseOrderByCreatedAtAsc(PostComment parent) {
        return jpa.findByParentAndDeletedFalseOrderByCreatedAtAsc(parent);
    }

    @Override
    public Page<PostComment> findByPostAndDeletedFalse(Post post, Pageable pageable) {
        return jpa.findByPostAndDeletedFalse(post, pageable);
    }

    @Override
    public long countByPostAndDeletedFalse(Post post) {
        return jpa.countByPostAndDeletedFalse(post);
    }

    @Override
    public long countByDeletedFalse() {
        return jpa.countByDeletedFalse();
    }
}
