package com.webproject.backtest_be_spring.domain.community.service;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.repository.PostRepository;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

@Service
public class PostDomainService {

    private final PostRepository postRepository;

    public PostDomainService(PostRepository postRepository) {
        this.postRepository = postRepository;
    }

    public void increaseViewCount(Post post) {
        Assert.notNull(post, "post must not be null");
        postRepository.incrementViewCount(post.getId());
        post.incrementViewCount();
    }

    public void increaseLikeCount(Post post) {
        adjustLikeCount(post, 1);
    }

    public void decreaseLikeCount(Post post) {
        adjustLikeCount(post, -1);
    }

    public void increaseCommentCount(Post post) {
        adjustCommentCount(post, 1);
    }

    public void decreaseCommentCount(Post post) {
        adjustCommentCount(post, -1);
    }

    private void adjustLikeCount(Post post, long delta) {
        Assert.notNull(post, "post must not be null");
        postRepository.adjustLikeCount(post.getId(), delta);
        if (delta > 0) {
            post.incrementLikeCount();
        } else {
            post.decrementLikeCount();
        }
    }

    private void adjustCommentCount(Post post, long delta) {
        Assert.notNull(post, "post must not be null");
        postRepository.adjustCommentCount(post.getId(), delta);
        if (delta > 0) {
            post.incrementCommentCount();
        } else {
            post.decrementCommentCount();
        }
    }
}
