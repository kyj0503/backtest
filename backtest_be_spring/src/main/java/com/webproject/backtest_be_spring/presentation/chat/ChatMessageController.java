package com.webproject.backtest_be_spring.presentation.chat;

import com.webproject.backtest_be_spring.application.chat.ChatMessageService;
import com.webproject.backtest_be_spring.application.chat.ChatMessagingFacade;
import com.webproject.backtest_be_spring.application.chat.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.application.chat.dto.ChatMessageDto;
import com.webproject.backtest_be_spring.common.security.UserPrincipal;
import com.webproject.backtest_be_spring.domain.chat.ChatMessageType;
import com.webproject.backtest_be_spring.presentation.chat.dto.ChatMessageRequest;
import com.webproject.backtest_be_spring.presentation.chat.dto.ChatMessageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;
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
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/chat")
@Tag(name = "Chat Messages", description = "채팅 메시지 API")
public class ChatMessageController {

    private final ChatMessageService chatMessageService;
    private final ChatMessagingFacade chatMessagingFacade;

    public ChatMessageController(ChatMessageService chatMessageService, ChatMessagingFacade chatMessagingFacade) {
        this.chatMessageService = chatMessageService;
        this.chatMessagingFacade = chatMessagingFacade;
    }

    @Operation(summary = "채팅 메시지 전송", description = "REST API를 이용해 메시지를 전송합니다.")
    @PostMapping("/rooms/{roomId}/messages")
    public ResponseEntity<ChatMessageResponse> sendMessage(@PathVariable Long roomId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody ChatMessageRequest request) {
        ChatMessageDto dto = chatMessagingFacade.send(roomId, principal.getId(), toCommand(request));
        return ResponseEntity.status(HttpStatus.CREATED).body(ChatMessageResponse.from(dto));
    }

    @Operation(summary = "채팅 메시지 조회", description = "채팅방의 메시지를 페이징으로 조회합니다.")
    @GetMapping("/rooms/{roomId}/messages")
    public ResponseEntity<Page<ChatMessageResponse>> getMessages(@PathVariable Long roomId,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "50") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<ChatMessageResponse> responses = chatMessageService.getMessages(roomId, pageable)
                .map(ChatMessageResponse::from);
        return ResponseEntity.ok(responses);
    }

    @Operation(summary = "최근 메시지", description = "채팅방의 최신 50개 메시지를 조회합니다.")
    @GetMapping("/rooms/{roomId}/messages/recent")
    public ResponseEntity<List<ChatMessageResponse>> getRecentMessages(@PathVariable Long roomId) {
        List<ChatMessageResponse> responses = chatMessageService.getRecentMessages(roomId).stream()
                .map(ChatMessageResponse::from)
                .collect(Collectors.toList());
        return ResponseEntity.ok(responses);
    }

    @Operation(summary = "채팅 메시지 삭제", description = "채팅 메시지를 삭제합니다.")
    @DeleteMapping("/messages/{messageId}")
    public ResponseEntity<Void> deleteMessage(@PathVariable Long messageId,
            @AuthenticationPrincipal UserPrincipal principal) {
        chatMessageService.deleteMessage(messageId, principal.getId());
        return ResponseEntity.noContent().build();
    }

    private SendChatMessageCommand toCommand(ChatMessageRequest request) {
        return new SendChatMessageCommand(
                parseMessageType(request.messageType()),
                request.content(),
                request.fileUrl(),
                request.fileName(),
                request.fileSize(),
                request.replyToId());
    }

    private ChatMessageType parseMessageType(String type) {
        if (type == null || type.isBlank()) {
            return ChatMessageType.TEXT;
        }
        try {
            return ChatMessageType.valueOf(type.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 메시지 타입입니다: " + type);
        }
    }
}
