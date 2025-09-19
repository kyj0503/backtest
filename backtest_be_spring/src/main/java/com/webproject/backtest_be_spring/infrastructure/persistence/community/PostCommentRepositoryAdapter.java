package com.webproject.backtest_be_spring.infrastructure.persistence.community;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostComment;
import com.webproject.backtest_be_spring.domain.community.repository.PostCommentRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
public class PostCommentRepositoryAdapter implements PostCommentRepository {

    private final JpaPostCommentRepository delegate;

    public PostCommentRepositoryAdapter(JpaPostCommentRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public PostComment save(PostComment comment) {
        return delegate.save(comment);
    }

    @Override
    public Optional<PostComment> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Optional<PostComment> findByIdAndDeletedFalse(Long id) {
        return delegate.findByIdAndDeletedFalse(id);
    }

    @Override
    public List<PostComment> findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(Post post) {
        return delegate.findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(post);
    }

    @Override
    public List<PostComment> findByParentAndDeletedFalseOrderByCreatedAtAsc(PostComment parent) {
        return delegate.findByParentAndDeletedFalseOrderByCreatedAtAsc(parent);
    }

    @Override
    public Page<PostComment> findByPostAndDeletedFalse(Post post, Pageable pageable) {
        return delegate.findByPostAndDeletedFalse(post, pageable);
    }

    @Override
    public long countByPostAndDeletedFalse(Post post) {
        return delegate.countByPostAndDeletedFalse(post);
    }

    @Override
    public long countByDeletedFalse() {
        return delegate.countByDeletedFalse();
    }
}
