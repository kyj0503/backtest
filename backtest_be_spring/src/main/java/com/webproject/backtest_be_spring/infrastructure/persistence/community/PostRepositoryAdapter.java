package com.webproject.backtest_be_spring.infrastructure.persistence.community;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostCategory;
import com.webproject.backtest_be_spring.domain.community.repository.PostRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
public class PostRepositoryAdapter implements PostRepository {

    private final JpaPostRepository delegate;

    public PostRepositoryAdapter(JpaPostRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public Post save(Post post) {
        return delegate.save(post);
    }

    @Override
    public Optional<Post> findById(Long id) {
        return delegate.findById(id);
    }

    @Override
    public Optional<Post> findByIdAndDeletedFalse(Long id) {
        return delegate.findByIdAndDeletedFalse(id);
    }

    @Override
    public Page<Post> findByDeletedFalse(Pageable pageable) {
        return delegate.findByDeletedFalse(pageable);
    }

    @Override
    public Page<Post> findByCategoryAndDeletedFalse(PostCategory category, Pageable pageable) {
        return delegate.findByCategoryAndDeletedFalse(category, pageable);
    }

    @Override
    public Page<Post> search(String keyword, Pageable pageable) {
        return delegate.search(keyword, pageable);
    }

    @Override
    public long countByDeletedFalse() {
        return delegate.countByDeletedFalse();
    }

    @Override
    public void incrementViewCount(Long postId) {
        delegate.incrementViewCount(postId);
    }

    @Override
    public void adjustLikeCount(Long postId, long delta) {
        delegate.adjustLikeCount(postId, delta);
    }

    @Override
    public void adjustCommentCount(Long postId, long delta) {
        delegate.adjustCommentCount(postId, delta);
    }
}
