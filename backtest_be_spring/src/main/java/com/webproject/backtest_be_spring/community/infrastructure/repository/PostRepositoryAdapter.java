package com.webproject.backtest_be_spring.community.infrastructure.repository;

import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.repository.PostRepository;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class PostRepositoryAdapter implements PostRepository {

    private final JpaPostRepository jpa;

    public PostRepositoryAdapter(JpaPostRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    @Transactional
    public Post save(Post post) {
        return jpa.save(post);
    }

    @Override
    public Optional<Post> findById(Long id) {
        return jpa.findById(id);
    }

    @Override
    public Optional<Post> findByIdAndDeletedFalse(Long id) {
        return jpa.findByIdAndDeletedFalse(id);
    }

    @Override
    public Page<Post> findByDeletedFalse(Pageable pageable) {
        return jpa.findByDeletedFalse(pageable);
    }

    @Override
    public Page<Post> findByCategoryAndDeletedFalse(PostCategory category, Pageable pageable) {
        return jpa.findByCategoryAndDeletedFalse(category, pageable);
    }

    @Override
    public Page<Post> search(String keyword, Pageable pageable) {
        return jpa.search(keyword, pageable);
    }

    @Override
    public long countByDeletedFalse() {
        return jpa.countByDeletedFalse();
    }

    @Override
    @Transactional
    public void incrementViewCount(Long postId) {
        jpa.incrementViewCount(postId);
    }

    @Override
    @Transactional
    public void adjustLikeCount(Long postId, long delta) {
        jpa.adjustLikeCount(postId, delta);
    }

    @Override
    @Transactional
    public void adjustCommentCount(Long postId, long delta) {
        jpa.adjustCommentCount(postId, delta);
    }
}
