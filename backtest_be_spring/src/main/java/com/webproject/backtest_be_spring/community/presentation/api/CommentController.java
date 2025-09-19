package com.webproject.backtest_be_spring.community.presentation.api;

import com.webproject.backtest_be_spring.community.application.CommentService;
import com.webproject.backtest_be_spring.community.application.command.CreateCommentCommand;
import com.webproject.backtest_be_spring.community.application.command.UpdateCommentCommand;
import com.webproject.backtest_be_spring.community.application.dto.CommentDto;
import com.webproject.backtest_be_spring.common.security.UserPrincipal;
import com.webproject.backtest_be_spring.community.presentation.api.dto.CommentCreateRequest;
import com.webproject.backtest_be_spring.community.presentation.api.dto.CommentLikeResponse;
import com.webproject.backtest_be_spring.community.presentation.api.dto.CommentResponse;
import com.webproject.backtest_be_spring.community.presentation.api.dto.CommentUpdateRequest;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/community")
@Tag(name = "Community Comments", description = "커뮤니티 댓글 API")
public class CommentController {

    private final CommentService commentService;

    public CommentController(CommentService commentService) {
        this.commentService = commentService;
    }

    @Operation(summary = "댓글 목록", description = "게시글의 댓글 트리를 조회합니다.")
    @GetMapping("/posts/{postId}/comments")
    public ResponseEntity<List<CommentResponse>> getComments(@PathVariable Long postId) {
        List<CommentResponse> responses = commentService.getComments(postId).stream()
                .map(CommentResponse::from)
                .collect(Collectors.toList());
        return ResponseEntity.ok(responses);
    }

    @Operation(summary = "댓글 작성", description = "게시글에 댓글 또는 대댓글을 작성합니다.")
    @PostMapping("/posts/{postId}/comments")
    public ResponseEntity<CommentResponse> addComment(@PathVariable Long postId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody CommentCreateRequest request) {
        CommentDto dto = commentService.addComment(postId, principal.getId(),
                new CreateCommentCommand(request.parentId(), request.content()));
        return ResponseEntity.status(HttpStatus.CREATED).body(CommentResponse.from(dto));
    }

    @Operation(summary = "댓글 수정", description = "댓글 내용을 수정합니다.")
    @PatchMapping("/comments/{commentId}")
    public ResponseEntity<CommentResponse> updateComment(@PathVariable Long commentId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody CommentUpdateRequest request) {
        CommentDto dto = commentService.updateComment(commentId, principal.getId(),
                new UpdateCommentCommand(request.content()));
        return ResponseEntity.ok(CommentResponse.from(dto));
    }

    @Operation(summary = "댓글 삭제", description = "댓글을 논리 삭제합니다.")
    @DeleteMapping("/comments/{commentId}")
    public ResponseEntity<Void> deleteComment(@PathVariable Long commentId,
            @AuthenticationPrincipal UserPrincipal principal) {
        commentService.deleteComment(commentId, principal.getId());
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "댓글 좋아요 토글", description = "댓글 좋아요를 추가하거나 제거합니다.")
    @PostMapping("/comments/{commentId}/like")
    public ResponseEntity<CommentLikeResponse> toggleLike(@PathVariable Long commentId,
            @AuthenticationPrincipal UserPrincipal principal) {
        boolean liked = commentService.toggleLike(commentId, principal.getId());
        return ResponseEntity.ok(CommentLikeResponse.of(liked));
    }
}
