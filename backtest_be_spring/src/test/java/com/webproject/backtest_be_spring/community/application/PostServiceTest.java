package com.webproject.backtest_be_spring.community.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.community.application.command.CreatePostCommand;
import com.webproject.backtest_be_spring.community.application.command.UpdatePostCommand;
import com.webproject.backtest_be_spring.community.application.dto.PostDto;
import com.webproject.backtest_be_spring.community.application.exception.CommunityAccessDeniedException;
import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;
import com.webproject.backtest_be_spring.community.domain.model.PostLike;
import com.webproject.backtest_be_spring.community.domain.repository.PostLikeRepository;
import com.webproject.backtest_be_spring.community.domain.repository.PostRepository;
import com.webproject.backtest_be_spring.community.domain.service.PostDomainService;
import com.webproject.backtest_be_spring.user.domain.model.InvestmentType;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class PostServiceTest {

    @Mock
    private PostRepository postRepository;

    @Mock
    private PostLikeRepository postLikeRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private PostDomainService postDomainService;

    @InjectMocks
    private PostService postService;

    @Test
    @DisplayName("게시글 생성은 작성자를 확인하고 게시글을 저장한다")
    void createPostPersistsEntity() {
        User author = user(1L, "alice", false);
        when(userRepository.findById(1L)).thenReturn(Optional.of(author));
        when(postRepository.save(any(Post.class))).thenAnswer(invocation -> {
            Post saved = invocation.getArgument(0);
            ReflectionTestUtils.setField(saved, "id", 10L);
            return saved;
        });

        CreatePostCommand command = new CreatePostCommand(
                PostCategory.GENERAL,
                "첫 글",
                "내용",
                PostContentType.MARKDOWN,
                false,
                false);

        PostDto result = postService.create(1L, command);

        assertThat(result.title()).isEqualTo("첫 글");
        assertThat(result.category()).isEqualTo(PostCategory.GENERAL);
        verify(postRepository).save(any(Post.class));
    }

    @Test
    @DisplayName("존재하지 않는 작성자는 게시글을 작성할 수 없다")
    void createPostFailsWhenUserMissing() {
        when(userRepository.findById(1L)).thenReturn(Optional.empty());

        CreatePostCommand command = new CreatePostCommand(
                PostCategory.GENERAL,
                "첫 글",
                "내용",
                PostContentType.MARKDOWN,
                false,
                false);

        assertThatThrownBy(() -> postService.create(1L, command))
                .isInstanceOf(UserNotFoundException.class);
        verify(postRepository, never()).save(any(Post.class));
    }

    @Test
    @DisplayName("관리자는 다른 사용자의 게시글을 수정할 수 있다")
    void updateAllowsAdmin() {
        User owner = user(1L, "alice", false);
        Post post = Post.create(owner, PostCategory.GENERAL, "제목", "내용", PostContentType.MARKDOWN, false, false);
        ReflectionTestUtils.setField(post, "id", 55L);

        User admin = user(2L, "admin", true);

        when(postRepository.findByIdAndDeletedFalse(55L)).thenReturn(Optional.of(post));
        when(userRepository.findById(2L)).thenReturn(Optional.of(admin));

        UpdatePostCommand command = new UpdatePostCommand(
                PostCategory.STRATEGY,
                "수정된 제목",
                "새 내용",
                PostContentType.TEXT,
                true,
                false);

        PostDto updated = postService.update(55L, 2L, command);

        assertThat(updated.title()).isEqualTo("수정된 제목");
        assertThat(updated.category()).isEqualTo(PostCategory.STRATEGY);
    }

    @Test
    @DisplayName("소유자가 아니고 관리자도 아니면 게시글을 삭제할 수 없다")
    void deleteRejectsUnauthorizedUser() {
        User owner = user(1L, "alice", false);
        Post post = Post.create(owner, PostCategory.GENERAL, "제목", "내용", PostContentType.MARKDOWN, false, false);
        ReflectionTestUtils.setField(post, "id", 100L);

        when(postRepository.findByIdAndDeletedFalse(100L)).thenReturn(Optional.of(post));
        when(userRepository.findById(3L)).thenReturn(Optional.of(user(3L, "bob", false)));

        assertThatThrownBy(() -> postService.delete(100L, 3L))
                .isInstanceOf(CommunityAccessDeniedException.class);
    }

    @Test
    @DisplayName("좋아요 토글은 첫 클릭에서 좋아요를 추가한다")
    void toggleLikeAddsWhenNotPresent() {
        User owner = user(1L, "alice", false);
        User liker = user(2L, "bob", false);
        Post post = Post.create(owner, PostCategory.GENERAL, "제목", "내용", PostContentType.MARKDOWN, false, false);
        ReflectionTestUtils.setField(post, "id", 200L);

        when(postRepository.findByIdAndDeletedFalse(200L)).thenReturn(Optional.of(post));
        when(userRepository.findById(2L)).thenReturn(Optional.of(liker));
        when(postLikeRepository.findByPostIdAndUserId(200L, 2L)).thenReturn(Optional.empty());

        boolean liked = postService.toggleLike(200L, 2L);

        assertThat(liked).isTrue();
        verify(postLikeRepository).save(any(PostLike.class));
        verify(postDomainService).increaseLikeCount(post);
    }

    @Test
    @DisplayName("좋아요 토글은 이미 눌린 경우 좋아요를 제거한다")
    void toggleLikeRemovesWhenPresent() {
        User owner = user(1L, "alice", false);
        User liker = user(2L, "bob", false);
        Post post = Post.create(owner, PostCategory.GENERAL, "제목", "내용", PostContentType.MARKDOWN, false, false);
        ReflectionTestUtils.setField(post, "id", 201L);

        PostLike existing = PostLike.create(post, liker);

        when(postRepository.findByIdAndDeletedFalse(201L)).thenReturn(Optional.of(post));
        when(userRepository.findById(2L)).thenReturn(Optional.of(liker));
        when(postLikeRepository.findByPostIdAndUserId(201L, 2L)).thenReturn(Optional.of(existing));

        boolean liked = postService.toggleLike(201L, 2L);

        assertThat(liked).isFalse();
        verify(postLikeRepository).delete(existing);
        verify(postDomainService).decreaseLikeCount(post);
    }

    private User user(Long id, String username, boolean admin) {
        User user = User.create(username, username + "@example.com", "Password!234", new byte[]{1, 2, 3}, InvestmentType.BALANCED);
        ReflectionTestUtils.setField(user, "id", id);
        ReflectionTestUtils.setField(user, "admin", admin);
        return user;
    }
}
