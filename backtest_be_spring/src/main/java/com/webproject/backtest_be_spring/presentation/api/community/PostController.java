package com.webproject.backtest_be_spring.presentation.api.community;

import com.webproject.backtest_be_spring.application.community.PostService;
import com.webproject.backtest_be_spring.application.community.command.CreatePostCommand;
import com.webproject.backtest_be_spring.application.community.command.UpdatePostCommand;
import com.webproject.backtest_be_spring.application.community.dto.PostDto;
import com.webproject.backtest_be_spring.application.community.dto.PostSummaryDto;
import com.webproject.backtest_be_spring.infrastructure.security.UserPrincipal;
import com.webproject.backtest_be_spring.domain.community.model.PostCategory;
import com.webproject.backtest_be_spring.domain.community.model.PostContentType;
import com.webproject.backtest_be_spring.presentation.api.community.dto.PostCreateRequest;
import com.webproject.backtest_be_spring.presentation.api.community.dto.PostLikeResponse;
import com.webproject.backtest_be_spring.presentation.api.community.dto.PostResponse;
import com.webproject.backtest_be_spring.presentation.api.community.dto.PostSummaryResponse;
import com.webproject.backtest_be_spring.presentation.api.community.dto.PostUpdateRequest;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.Locale;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/community/posts")
@Tag(name = "Community", description = "커뮤니티 게시글 API")
public class PostController {

    private final PostService postService;

    public PostController(PostService postService) {
        this.postService = postService;
    }

    @Operation(summary = "게시글 생성", description = "새로운 게시글을 작성합니다.")
    @PostMapping
    public ResponseEntity<PostResponse> create(@AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody PostCreateRequest request) {
        PostDto post = postService.create(principal.getId(), toCreateCommand(request));
        return ResponseEntity.status(HttpStatus.CREATED).body(PostResponse.from(post));
    }

    @Operation(summary = "게시글 수정", description = "기존 게시글을 수정합니다.")
    @PutMapping("/{postId}")
    public ResponseEntity<PostResponse> update(@PathVariable Long postId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody PostUpdateRequest request) {
        PostDto updated = postService.update(postId, principal.getId(), toUpdateCommand(request));
        return ResponseEntity.ok(PostResponse.from(updated));
    }

    @Operation(summary = "게시글 삭제", description = "게시글을 논리 삭제합니다.")
    @DeleteMapping("/{postId}")
    public ResponseEntity<Void> delete(@PathVariable Long postId, @AuthenticationPrincipal UserPrincipal principal) {
        postService.delete(postId, principal.getId());
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "게시글 상세", description = "게시글 상세 정보를 조회합니다.")
    @GetMapping("/{postId}")
    public ResponseEntity<PostResponse> getPost(@PathVariable Long postId,
            @RequestParam(name = "increaseView", defaultValue = "true") boolean increaseView) {
        PostDto dto = postService.getPost(postId, increaseView);
        return ResponseEntity.ok(PostResponse.from(dto));
    }

    @Operation(summary = "게시글 목록", description = "게시글을 페이징하여 조회합니다.")
    @GetMapping
    public ResponseEntity<Page<PostSummaryResponse>> getPosts(
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "keyword", required = false) String keyword,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        PostCategory postCategory = parseCategory(category);
        Page<PostSummaryDto> posts = postService.getPosts(postCategory, keyword, pageable);
        Page<PostSummaryResponse> response = posts.map(PostSummaryResponse::from);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "게시글 좋아요 토글", description = "좋아요를 추가하거나 제거합니다.")
    @PostMapping("/{postId}/like")
    public ResponseEntity<PostLikeResponse> toggleLike(@PathVariable Long postId,
            @AuthenticationPrincipal UserPrincipal principal) {
        boolean liked = postService.toggleLike(postId, principal.getId());
        return ResponseEntity.ok(PostLikeResponse.of(liked));
    }

    private CreatePostCommand toCreateCommand(PostCreateRequest request) {
        return new CreatePostCommand(
                parseCategory(request.category()),
                request.title(),
                request.content(),
                parseContentType(request.contentType()),
                Boolean.TRUE.equals(request.pinned()),
                Boolean.TRUE.equals(request.featured()));
    }

    private UpdatePostCommand toUpdateCommand(PostUpdateRequest request) {
        return new UpdatePostCommand(
                parseCategory(request.category()),
                request.title(),
                request.content(),
                parseContentType(request.contentType()),
                request.pinned(),
                request.featured());
    }

    private PostCategory parseCategory(String category) {
        if (category == null || category.isBlank()) {
            return null;
        }
        try {
            return PostCategory.valueOf(category.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 카테고리입니다: " + category);
        }
    }

    private PostContentType parseContentType(String contentType) {
        if (contentType == null || contentType.isBlank()) {
            return null;
        }
        try {
            return PostContentType.valueOf(contentType.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 컨텐츠 타입입니다: " + contentType);
        }
    }
}
