package com.webproject.backtest_be_spring.community.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.webproject.backtest_be_spring.community.application.command.CreateCommentCommand;
import com.webproject.backtest_be_spring.community.application.dto.CommentDto;
import com.webproject.backtest_be_spring.community.application.exception.CommunityAccessDeniedException;
import com.webproject.backtest_be_spring.community.domain.model.CommentLike;
import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.model.PostComment;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;
import com.webproject.backtest_be_spring.community.domain.repository.CommentLikeRepository;
import com.webproject.backtest_be_spring.community.domain.repository.PostCommentRepository;
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
class CommentServiceTest {

    @Mock
    private PostRepository postRepository;

    @Mock
    private PostCommentRepository postCommentRepository;

    @Mock
    private CommentLikeRepository commentLikeRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private PostDomainService postDomainService;

    @InjectMocks
    private CommentService commentService;

    @Test
    @DisplayName("댓글 작성 시 게시글 댓글 수가 증가한다")
    void addCommentIncrementsPostCount() {
        Post post = post(1L);
        User author = user(2L, "commenter", false);
        PostComment saved = PostComment.create(post, author, null, "첫 댓글");
        ReflectionTestUtils.setField(saved, "id", 10L);

        when(postRepository.findByIdAndDeletedFalse(1L)).thenReturn(Optional.of(post));
        when(userRepository.findById(2L)).thenReturn(Optional.of(author));
        when(postCommentRepository.save(any(PostComment.class))).thenReturn(saved);

        CommentDto dto = commentService.addComment(1L, 2L, new CreateCommentCommand(null, "첫 댓글"));

        assertThat(dto.content()).isEqualTo("첫 댓글");
        verify(postCommentRepository).save(any(PostComment.class));
        verify(postDomainService).increaseCommentCount(post);
    }

    @Test
    @DisplayName("부모 댓글이 다른 게시글에 속하면 예외가 발생한다")
    void addCommentFailsWhenParentMismatch() {
        Post post = post(1L);
        Post anotherPost = post(2L);
        User author = user(2L, "commenter", false);
        PostComment parent = PostComment.create(anotherPost, author, null, "부모");
        ReflectionTestUtils.setField(parent, "id", 20L);

        when(postRepository.findByIdAndDeletedFalse(1L)).thenReturn(Optional.of(post));
        when(userRepository.findById(2L)).thenReturn(Optional.of(author));
        when(postCommentRepository.findByIdAndDeletedFalse(20L)).thenReturn(Optional.of(parent));

        assertThatThrownBy(() -> commentService.addComment(1L, 2L, new CreateCommentCommand(20L, "대댓글")))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("댓글과 게시글이 일치하지 않습니다");
        verify(postCommentRepository, never()).save(any(PostComment.class));
    }

    @Test
    @DisplayName("이미 눌린 댓글 좋아요는 재호출 시 제거된다")
    void toggleLikeRemovesExistingLike() {
        Post post = post(1L);
        User author = user(2L, "writer", false);
        User liker = user(3L, "liker", false);
        PostComment comment = PostComment.create(post, author, null, "댓글");
        ReflectionTestUtils.setField(comment, "id", 30L);
        ReflectionTestUtils.setField(comment, "likeCount", 1L);
        CommentLike existing = CommentLike.create(comment, liker);

        when(postCommentRepository.findByIdAndDeletedFalse(30L)).thenReturn(Optional.of(comment));
        when(userRepository.findById(3L)).thenReturn(Optional.of(liker));
        when(commentLikeRepository.findByCommentIdAndUserId(30L, 3L)).thenReturn(Optional.of(existing));

        boolean liked = commentService.toggleLike(30L, 3L);

        assertThat(liked).isFalse();
        assertThat(comment.getLikeCount()).isZero();
        verify(commentLikeRepository).delete(existing);
    }

    @Test
    @DisplayName("관리자는 본인 댓글이 아니어도 삭제할 수 있다")
    void deleteCommentByAdmin() {
        Post post = post(1L);
        User writer = user(2L, "writer", false);
        PostComment comment = PostComment.create(post, writer, null, "댓글");
        ReflectionTestUtils.setField(comment, "id", 40L);
        User admin = user(99L, "admin", true);

        when(postCommentRepository.findByIdAndDeletedFalse(40L)).thenReturn(Optional.of(comment));
        when(userRepository.findById(99L)).thenReturn(Optional.of(admin));

        commentService.deleteComment(40L, 99L);

        assertThat(comment.isDeleted()).isTrue();
        verify(postDomainService).decreaseCommentCount(post);
    }

    @Test
    @DisplayName("좋아요가 없으면 새로운 좋아요를 추가한다")
    void toggleLikeAddsWhenNotPresent() {
        Post post = post(1L);
        User writer = user(2L, "writer", false);
        User liker = user(3L, "liker", false);
        PostComment comment = PostComment.create(post, writer, null, "댓글");
        ReflectionTestUtils.setField(comment, "id", 41L);

        when(postCommentRepository.findByIdAndDeletedFalse(41L)).thenReturn(Optional.of(comment));
        when(userRepository.findById(3L)).thenReturn(Optional.of(liker));
        when(commentLikeRepository.findByCommentIdAndUserId(41L, 3L)).thenReturn(Optional.empty());

        boolean liked = commentService.toggleLike(41L, 3L);

        assertThat(liked).isTrue();
        assertThat(comment.getLikeCount()).isEqualTo(1L);
        verify(commentLikeRepository).save(any(CommentLike.class));
    }

    @Test
    @DisplayName("관리자가 아니고 작성자도 아니면 댓글을 삭제할 수 없다")
    void deleteCommentRejectsUnauthorizedUser() {
        Post post = post(1L);
        User writer = user(2L, "writer", false);
        User requester = user(4L, "guest", false);
        PostComment comment = PostComment.create(post, writer, null, "댓글");
        ReflectionTestUtils.setField(comment, "id", 50L);

        when(postCommentRepository.findByIdAndDeletedFalse(50L)).thenReturn(Optional.of(comment));
        when(userRepository.findById(4L)).thenReturn(Optional.of(requester));

        assertThatThrownBy(() -> commentService.deleteComment(50L, 4L))
                .isInstanceOf(CommunityAccessDeniedException.class);
        assertThat(comment.isDeleted()).isFalse();
        verify(postDomainService, never()).decreaseCommentCount(post);
    }

    private Post post(Long id) {
        User author = user(10L, "author", false);
        Post post = Post.create(author, PostCategory.GENERAL, "제목", "내용", PostContentType.MARKDOWN, false, false);
        ReflectionTestUtils.setField(post, "id", id);
        return post;
    }

    private User user(Long id, String username, boolean admin) {
        User user = User.create(username, username + "@example.com", "Password!234", new byte[]{1, 2, 3}, InvestmentType.BALANCED);
        ReflectionTestUtils.setField(user, "id", id);
        ReflectionTestUtils.setField(user, "admin", admin);
        return user;
    }
}
