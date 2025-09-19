package com.webproject.backtest_be_spring.presentation.api.chat;

import com.webproject.backtest_be_spring.application.chat.ChatRoomService;
import com.webproject.backtest_be_spring.application.chat.command.CreateChatRoomCommand;
import com.webproject.backtest_be_spring.application.chat.command.UpdateChatRoomCommand;
import com.webproject.backtest_be_spring.application.chat.dto.ChatRoomDto;
import com.webproject.backtest_be_spring.application.chat.dto.ChatRoomMemberDto;
import com.webproject.backtest_be_spring.infrastructure.security.UserPrincipal;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomType;
import com.webproject.backtest_be_spring.presentation.api.chat.dto.ChatRoomCreateRequest;
import com.webproject.backtest_be_spring.presentation.api.chat.dto.ChatRoomMemberResponse;
import com.webproject.backtest_be_spring.presentation.api.chat.dto.ChatRoomResponse;
import com.webproject.backtest_be_spring.presentation.api.chat.dto.ChatRoomUpdateRequest;
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
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/chat/rooms")
@Tag(name = "Chat Rooms", description = "채팅방 관리 API")
public class ChatRoomController {

    private final ChatRoomService chatRoomService;

    public ChatRoomController(ChatRoomService chatRoomService) {
        this.chatRoomService = chatRoomService;
    }

    @Operation(summary = "채팅방 생성", description = "새로운 채팅방을 생성합니다.")
    @PostMapping
    public ResponseEntity<ChatRoomResponse> createRoom(@AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody ChatRoomCreateRequest request) {
        ChatRoomDto dto = chatRoomService.createRoom(principal.getId(),
                new CreateChatRoomCommand(
                        request.name(),
                        request.description(),
                        parseRoomType(request.roomType()),
                        request.maxMembers()));
        return ResponseEntity.status(HttpStatus.CREATED).body(ChatRoomResponse.from(dto));
    }

    @Operation(summary = "채팅방 수정", description = "채팅방 정보를 수정합니다.")
    @PutMapping("/{roomId}")
    public ResponseEntity<ChatRoomResponse> updateRoom(@PathVariable Long roomId,
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody ChatRoomUpdateRequest request) {
        ChatRoomDto dto = chatRoomService.updateRoom(roomId, principal.getId(),
                new UpdateChatRoomCommand(
                        request.name(),
                        request.description(),
                        parseRoomType(request.roomType()),
                        request.maxMembers(),
                        request.active()));
        return ResponseEntity.ok(ChatRoomResponse.from(dto));
    }

    @Operation(summary = "채팅방 삭제", description = "채팅방을 비활성화합니다.")
    @DeleteMapping("/{roomId}")
    public ResponseEntity<Void> deleteRoom(@PathVariable Long roomId, @AuthenticationPrincipal UserPrincipal principal) {
        chatRoomService.deleteRoom(roomId, principal.getId());
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "채팅방 상세", description = "채팅방 정보를 조회합니다.")
    @GetMapping("/{roomId}")
    public ResponseEntity<ChatRoomResponse> getRoom(@PathVariable Long roomId) {
        return ResponseEntity.ok(ChatRoomResponse.from(chatRoomService.getRoom(roomId)));
    }

    @Operation(summary = "채팅방 목록", description = "활성화된 채팅방을 조회합니다.")
    @GetMapping
    public ResponseEntity<Page<ChatRoomResponse>> getRooms(
            @RequestParam(name = "type", required = false) String type,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        ChatRoomType roomType = parseRoomType(type);
        Page<ChatRoomResponse> response = chatRoomService.getRooms(roomType, pageable)
                .map(ChatRoomResponse::from);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "채팅방 참여", description = "채팅방에 입장합니다.")
    @PostMapping("/{roomId}/join")
    public ResponseEntity<ChatRoomMemberResponse> joinRoom(@PathVariable Long roomId,
            @AuthenticationPrincipal UserPrincipal principal) {
        ChatRoomMemberDto dto = chatRoomService.joinRoom(roomId, principal.getId());
        return ResponseEntity.status(HttpStatus.CREATED).body(ChatRoomMemberResponse.from(dto));
    }

    @Operation(summary = "채팅방 퇴장", description = "채팅방에서 나갑니다.")
    @PostMapping("/{roomId}/leave")
    public ResponseEntity<Void> leaveRoom(@PathVariable Long roomId,
            @AuthenticationPrincipal UserPrincipal principal) {
        chatRoomService.leaveRoom(roomId, principal.getId());
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "채팅방 멤버", description = "채팅방에 참여 중인 멤버 목록을 반환합니다.")
    @GetMapping("/{roomId}/members")
    public ResponseEntity<List<ChatRoomMemberResponse>> getMembers(@PathVariable Long roomId) {
        List<ChatRoomMemberResponse> members = chatRoomService.getMembers(roomId).stream()
                .map(ChatRoomMemberResponse::from)
                .collect(Collectors.toList());
        return ResponseEntity.ok(members);
    }

    private ChatRoomType parseRoomType(String type) {
        if (type == null || type.isBlank()) {
            return null;
        }
        try {
            return ChatRoomType.valueOf(type.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("지원하지 않는 채팅방 타입입니다: " + type);
        }
    }
}
