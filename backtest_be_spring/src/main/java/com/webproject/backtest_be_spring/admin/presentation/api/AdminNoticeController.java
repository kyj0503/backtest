package com.webproject.backtest_be_spring.admin.presentation.api;

import com.webproject.backtest_be_spring.admin.application.AdminNoticeService;
import com.webproject.backtest_be_spring.admin.application.command.CreateNoticeCommand;
import com.webproject.backtest_be_spring.admin.application.command.UpdateNoticeCommand;
import com.webproject.backtest_be_spring.admin.application.dto.SystemNoticeDto;
import com.webproject.backtest_be_spring.common.security.UserPrincipal;
import com.webproject.backtest_be_spring.admin.domain.model.SystemNoticePriority;
import com.webproject.backtest_be_spring.admin.domain.model.SystemNoticeType;
import com.webproject.backtest_be_spring.admin.presentation.api.dto.NoticeCreateRequest;
import com.webproject.backtest_be_spring.admin.presentation.api.dto.NoticeResponse;
import com.webproject.backtest_be_spring.admin.presentation.api.dto.NoticeUpdateRequest;
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
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin/notices")
@Tag(name = "Admin Notices", description = "공지사항 관리 API")
@PreAuthorize("hasRole('ADMIN')")
public class AdminNoticeController {

    private final AdminNoticeService adminNoticeService;

    public AdminNoticeController(AdminNoticeService adminNoticeService) {
        this.adminNoticeService = adminNoticeService;
    }

    @Operation(summary = "공지 생성", description = "새로운 공지사항을 등록합니다.")
    @PostMapping
    public ResponseEntity<NoticeResponse> createNotice(@AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody NoticeCreateRequest request) {
        SystemNoticeDto dto = adminNoticeService.create(principal.getId(),
                new CreateNoticeCommand(
                        request.title(),
                        request.content(),
                        parseNoticeType(request.noticeType()),
                        parsePriority(request.priority()),
                        request.popup(),
                        request.pinned(),
                        request.startDate(),
                        request.endDate(),
                        request.active()));
        return ResponseEntity.status(HttpStatus.CREATED).body(NoticeResponse.from(dto));
    }

    @Operation(summary = "공지 수정", description = "공지사항 내용을 수정합니다.")
    @PutMapping("/{noticeId}")
    public ResponseEntity<NoticeResponse> updateNotice(@PathVariable Long noticeId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody NoticeUpdateRequest request) {
        SystemNoticeDto dto = adminNoticeService.update(principal.getId(), noticeId,
                new UpdateNoticeCommand(
                        request.title(),
                        request.content(),
                        parseNoticeType(request.noticeType()),
                        parsePriority(request.priority()),
                        request.popup(),
                        request.pinned(),
                        request.startDate(),
                        request.endDate(),
                        request.active()));
        return ResponseEntity.ok(NoticeResponse.from(dto));
    }

    @Operation(summary = "공지 목록", description = "공지사항을 페이징하여 조회합니다.")
    @GetMapping
    public ResponseEntity<Page<NoticeResponse>> getNotices(
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<NoticeResponse> responses = adminNoticeService.getNotices(pageable).map(NoticeResponse::from);
        return ResponseEntity.ok(responses);
    }

    private SystemNoticeType parseNoticeType(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return SystemNoticeType.valueOf(value.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 공지 유형입니다: " + value);
        }
    }

    private SystemNoticePriority parsePriority(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return SystemNoticePriority.valueOf(value.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 공지 우선순위입니다: " + value);
        }
    }
}
