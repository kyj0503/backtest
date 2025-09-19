package com.webproject.backtest_be_spring.chat.application;

import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.chat.application.command.CreateChatRoomCommand;
import com.webproject.backtest_be_spring.chat.application.command.UpdateChatRoomCommand;
import com.webproject.backtest_be_spring.chat.application.dto.ChatRoomDto;
import com.webproject.backtest_be_spring.chat.application.dto.ChatRoomMemberDto;
import com.webproject.backtest_be_spring.chat.application.exception.ChatAccessDeniedException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatRoomNotFoundException;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMemberRole;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomMemberRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomRepository;
import com.webproject.backtest_be_spring.chat.domain.service.ChatRoomDomainService;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import jakarta.transaction.Transactional;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class ChatRoomService {

    private final ChatRoomRepository chatRoomRepository;
    private final ChatRoomMemberRepository chatRoomMemberRepository;
    private final UserRepository userRepository;
    private final ChatRoomDomainService chatRoomDomainService;

    public ChatRoomService(ChatRoomRepository chatRoomRepository, ChatRoomMemberRepository chatRoomMemberRepository,
            UserRepository userRepository, ChatRoomDomainService chatRoomDomainService) {
        this.chatRoomRepository = chatRoomRepository;
        this.chatRoomMemberRepository = chatRoomMemberRepository;
        this.userRepository = userRepository;
        this.chatRoomDomainService = chatRoomDomainService;
    }

    public ChatRoomDto createRoom(Long userId, CreateChatRoomCommand command) {
        User creator = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        if (chatRoomRepository.existsByNameIgnoreCase(command.name())) {
            throw new IllegalArgumentException("이미 존재하는 채팅방 이름입니다.");
        }
        ChatRoom room = ChatRoom.create(
                command.name(),
                command.description(),
                Optional.ofNullable(command.roomType()).orElse(ChatRoomType.PUBLIC),
                command.maxMembers(),
                creator);
        chatRoomRepository.save(room);
        ChatRoomMember member = ChatRoomMember.create(room, creator, ChatMemberRole.ADMIN);
        chatRoomMemberRepository.save(member);
        chatRoomDomainService.increaseMembers(room);
        return ChatRoomDto.from(room);
    }

    public ChatRoomDto updateRoom(Long roomId, Long userId, UpdateChatRoomCommand command) {
        ChatRoom room = chatRoomRepository.findById(roomId).orElseThrow(() -> new ChatRoomNotFoundException(roomId));
        verifyRoomAdmin(room, userId);
        room.update(
                command.name(),
                command.description(),
                Optional.ofNullable(command.roomType()).orElse(room.getRoomType()),
                command.maxMembers(),
                command.active() != null ? command.active() : room.isActive());
        return ChatRoomDto.from(room);
    }

    public void deleteRoom(Long roomId, Long userId) {
        ChatRoom room = chatRoomRepository.findById(roomId).orElseThrow(() -> new ChatRoomNotFoundException(roomId));
        verifyRoomAdmin(room, userId);
        chatRoomDomainService.deactivate(room);
    }

    public ChatRoomDto getRoom(Long roomId) {
        ChatRoom room = chatRoomRepository.findById(roomId).orElseThrow(() -> new ChatRoomNotFoundException(roomId));
        return ChatRoomDto.from(room);
    }

    public Page<ChatRoomDto> getRooms(ChatRoomType type, Pageable pageable) {
        Page<ChatRoom> rooms;
        if (type != null) {
            rooms = chatRoomRepository.findByRoomTypeAndActiveTrue(type, pageable);
        } else {
            rooms = chatRoomRepository.findByActiveTrue(pageable);
        }
        return rooms.map(ChatRoomDto::from);
    }

    public ChatRoomMemberDto joinRoom(Long roomId, Long userId) {
        ChatRoom room = chatRoomRepository.findByIdAndActiveTrue(roomId)
                .orElseThrow(() -> new ChatRoomNotFoundException(roomId));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));

        ChatRoomMember member = chatRoomMemberRepository.findByRoomIdAndUserId(roomId, userId)
                .map(existing -> {
                    if (!existing.isActive()) {
                        existing.activate();
                        chatRoomDomainService.increaseMembers(room);
                    }
                    return existing;
                })
                .orElseGet(() -> {
                    if (!room.hasCapacity()) {
                        throw new IllegalStateException("채팅방 인원이 가득 찼습니다.");
                    }
                    ChatRoomMember created = ChatRoomMember.create(room, user, ChatMemberRole.MEMBER);
                    chatRoomMemberRepository.save(created);
                    chatRoomDomainService.increaseMembers(room);
                    return created;
                });
        return ChatRoomMemberDto.from(member);
    }

    public void leaveRoom(Long roomId, Long userId) {
        ChatRoomMember member = chatRoomMemberRepository.findByRoomIdAndUserId(roomId, userId)
                .orElseThrow(() -> new ChatAccessDeniedException());
        if (member.isActive()) {
            member.markInactive();
            chatRoomDomainService.decreaseMembers(member.getRoom());
        }
    }

    public List<ChatRoomMemberDto> getMembers(Long roomId) {
        return chatRoomMemberRepository.findByRoomIdAndActiveTrue(roomId).stream()
                .map(ChatRoomMemberDto::from)
                .collect(Collectors.toList());
    }

    private void verifyRoomAdmin(ChatRoom room, Long userId) {
        if (room.getCreatedBy().getId().equals(userId)) {
            return;
        }
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        if (!user.isAdmin()) {
            throw new ChatAccessDeniedException();
        }
    }
}
