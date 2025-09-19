package com.webproject.backtest_be_spring.application.community;

import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.application.community.command.CreateCommentCommand;
import com.webproject.backtest_be_spring.application.community.command.UpdateCommentCommand;
import com.webproject.backtest_be_spring.application.community.dto.CommentDto;
import com.webproject.backtest_be_spring.application.community.exception.CommentNotFoundException;
import com.webproject.backtest_be_spring.application.community.exception.CommunityAccessDeniedException;
import com.webproject.backtest_be_spring.application.community.exception.PostNotFoundException;
import com.webproject.backtest_be_spring.domain.community.model.CommentLike;
import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostComment;
import com.webproject.backtest_be_spring.domain.community.repository.CommentLikeRepository;
import com.webproject.backtest_be_spring.domain.community.repository.PostCommentRepository;
import com.webproject.backtest_be_spring.domain.community.repository.PostRepository;
import com.webproject.backtest_be_spring.domain.community.service.PostDomainService;
import com.webproject.backtest_be_spring.domain.user.model.User;
import com.webproject.backtest_be_spring.domain.user.repository.UserRepository;
import jakarta.transaction.Transactional;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class CommentService {

    private final PostRepository postRepository;
    private final PostCommentRepository postCommentRepository;
    private final CommentLikeRepository commentLikeRepository;
    private final UserRepository userRepository;
    private final PostDomainService postDomainService;

    public CommentService(PostRepository postRepository, PostCommentRepository postCommentRepository,
            CommentLikeRepository commentLikeRepository, UserRepository userRepository,
            PostDomainService postDomainService) {
        this.postRepository = postRepository;
        this.postCommentRepository = postCommentRepository;
        this.commentLikeRepository = commentLikeRepository;
        this.userRepository = userRepository;
        this.postDomainService = postDomainService;
    }

    public CommentDto addComment(Long postId, Long userId, CreateCommentCommand command) {
        Post post = postRepository.findByIdAndDeletedFalse(postId).orElseThrow(() -> new PostNotFoundException(postId));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));

        PostComment parent = null;
        if (command.parentId() != null) {
            parent = postCommentRepository.findByIdAndDeletedFalse(command.parentId())
                    .orElseThrow(() -> new CommentNotFoundException(command.parentId()));
            if (!parent.getPost().getId().equals(postId)) {
                throw new IllegalArgumentException("댓글과 게시글이 일치하지 않습니다.");
            }
        }

        PostComment comment = PostComment.create(post, user, parent, command.content());
        postCommentRepository.save(comment);
        postDomainService.increaseCommentCount(post);
        return CommentDto.from(comment, List.of());
    }

    public CommentDto updateComment(Long commentId, Long userId, UpdateCommentCommand command) {
        PostComment comment = postCommentRepository.findByIdAndDeletedFalse(commentId)
                .orElseThrow(() -> new CommentNotFoundException(commentId));
        verifyOwnershipOrAdmin(comment, userId);
        comment.update(command.content());
        return CommentDto.from(comment, loadChildren(comment));
    }

    public void deleteComment(Long commentId, Long userId) {
        PostComment comment = postCommentRepository.findByIdAndDeletedFalse(commentId)
                .orElseThrow(() -> new CommentNotFoundException(commentId));
        verifyOwnershipOrAdmin(comment, userId);
        comment.markDeleted();
        postDomainService.decreaseCommentCount(comment.getPost());
    }

    public boolean toggleLike(Long commentId, Long userId) {
        PostComment comment = postCommentRepository.findByIdAndDeletedFalse(commentId)
                .orElseThrow(() -> new CommentNotFoundException(commentId));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));

        Optional<CommentLike> existing = commentLikeRepository.findByCommentIdAndUserId(commentId, userId);
        if (existing.isPresent()) {
            commentLikeRepository.delete(existing.get());
            comment.decrementLikeCount();
            return false;
        } else {
            commentLikeRepository.save(CommentLike.create(comment, user));
            comment.incrementLikeCount();
            return true;
        }
    }

    public List<CommentDto> getComments(Long postId) {
        Post post = postRepository.findByIdAndDeletedFalse(postId).orElseThrow(() -> new PostNotFoundException(postId));
        List<PostComment> roots = postCommentRepository
                .findByPostAndParentIsNullAndDeletedFalseOrderByCreatedAtAsc(post);
        List<CommentDto> result = new ArrayList<>();
        for (PostComment root : roots) {
            result.add(CommentDto.from(root, loadChildren(root)));
        }
        return result;
    }

    private List<CommentDto> loadChildren(PostComment parent) {
        List<PostComment> children = postCommentRepository
                .findByParentAndDeletedFalseOrderByCreatedAtAsc(parent);
        List<CommentDto> result = new ArrayList<>();
        for (PostComment child : children) {
            result.add(CommentDto.from(child, loadChildren(child)));
        }
        return result;
    }

    private void verifyOwnershipOrAdmin(PostComment comment, Long userId) {
        if (comment.isOwnedBy(userId)) {
            return;
        }
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        if (!user.isAdmin()) {
            throw new CommunityAccessDeniedException();
        }
    }
}
