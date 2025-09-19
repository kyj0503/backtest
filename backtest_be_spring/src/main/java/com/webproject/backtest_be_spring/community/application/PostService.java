package com.webproject.backtest_be_spring.community.application;

import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.community.application.command.CreatePostCommand;
import com.webproject.backtest_be_spring.community.application.command.UpdatePostCommand;
import com.webproject.backtest_be_spring.community.application.dto.PostDto;
import com.webproject.backtest_be_spring.community.application.dto.PostSummaryDto;
import com.webproject.backtest_be_spring.community.application.exception.CommunityAccessDeniedException;
import com.webproject.backtest_be_spring.community.application.exception.PostNotFoundException;
import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;
import com.webproject.backtest_be_spring.community.domain.model.PostLike;
import com.webproject.backtest_be_spring.community.domain.repository.PostLikeRepository;
import com.webproject.backtest_be_spring.community.domain.repository.PostRepository;
import com.webproject.backtest_be_spring.community.domain.service.PostDomainService;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import jakarta.transaction.Transactional;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class PostService {

    private final PostRepository postRepository;
    private final PostLikeRepository postLikeRepository;
    private final UserRepository userRepository;
    private final PostDomainService postDomainService;

    public PostService(PostRepository postRepository, PostLikeRepository postLikeRepository,
            UserRepository userRepository, PostDomainService postDomainService) {
        this.postRepository = postRepository;
        this.postLikeRepository = postLikeRepository;
        this.userRepository = userRepository;
        this.postDomainService = postDomainService;
    }

    public PostDto create(Long userId, CreatePostCommand command) {
        User author = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        Post post = Post.create(
                author,
                Optional.ofNullable(command.category()).orElse(PostCategory.GENERAL),
                command.title(),
                command.content(),
                Optional.ofNullable(command.contentType()).orElse(PostContentType.MARKDOWN),
                command.pinned(),
                command.featured());
        postRepository.save(post);
        return PostDto.from(post);
    }

    public PostDto update(Long postId, Long userId, UpdatePostCommand command) {
        Post post = postRepository.findByIdAndDeletedFalse(postId).orElseThrow(() -> new PostNotFoundException(postId));
        verifyOwnershipOrAdmin(post, userId);
        String title = command.title() != null ? command.title() : post.getTitle();
        String content = command.content() != null ? command.content() : post.getContent();
        PostCategory category = Optional.ofNullable(command.category()).orElse(post.getCategory());
        PostContentType contentType = Optional.ofNullable(command.contentType()).orElse(post.getContentType());
        boolean pinned = command.pinned() != null ? command.pinned() : post.isPinned();
        boolean featured = command.featured() != null ? command.featured() : post.isFeatured();
        post.update(title, content, category, contentType, pinned, featured);
        return PostDto.from(post);
    }

    public void delete(Long postId, Long userId) {
        Post post = postRepository.findByIdAndDeletedFalse(postId).orElseThrow(() -> new PostNotFoundException(postId));
        verifyOwnershipOrAdmin(post, userId);
        post.markDeleted();
    }

    public PostDto getPost(Long postId, boolean increaseViewCount) {
        Post post = postRepository.findByIdAndDeletedFalse(postId).orElseThrow(() -> new PostNotFoundException(postId));
        if (increaseViewCount) {
            postDomainService.increaseViewCount(post);
        }
        return PostDto.from(post);
    }

    public Page<PostSummaryDto> getPosts(PostCategory category, String keyword, Pageable pageable) {
        Page<Post> posts;
        if (keyword != null && !keyword.isBlank()) {
            posts = postRepository.search(keyword, pageable);
        } else if (category != null) {
            posts = postRepository.findByCategoryAndDeletedFalse(category, pageable);
        } else {
            posts = postRepository.findByDeletedFalse(pageable);
        }
        return posts.map(PostSummaryDto::from);
    }

    public boolean toggleLike(Long postId, Long userId) {
        Post post = postRepository.findByIdAndDeletedFalse(postId).orElseThrow(() -> new PostNotFoundException(postId));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        Optional<PostLike> existing = postLikeRepository.findByPostIdAndUserId(postId, userId);
        if (existing.isPresent()) {
            postLikeRepository.delete(existing.get());
            postDomainService.decreaseLikeCount(post);
            return false;
        } else {
            postLikeRepository.save(PostLike.create(post, user));
            postDomainService.increaseLikeCount(post);
            return true;
        }
    }

    private void verifyOwnershipOrAdmin(Post post, Long userId) {
        if (post.isOwnedBy(userId)) {
            return;
        }
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        if (!user.isAdmin()) {
            throw new CommunityAccessDeniedException();
        }
    }
}
