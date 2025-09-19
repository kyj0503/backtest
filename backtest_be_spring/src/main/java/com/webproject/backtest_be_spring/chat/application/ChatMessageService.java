package com.webproject.backtest_be_spring.chat.application;

import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.chat.application.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.chat.application.dto.ChatMessageDto;
import com.webproject.backtest_be_spring.chat.application.exception.ChatAccessDeniedException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatMessageNotFoundException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatRoomNotFoundException;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessage;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessageType;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatMessageRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomMemberRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomRepository;
import com.webproject.backtest_be_spring.chat.domain.service.ChatMessageDomainService;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import jakarta.transaction.Transactional;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class ChatMessageService {

    private final ChatRoomRepository chatRoomRepository;
    private final ChatRoomMemberRepository chatRoomMemberRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final UserRepository userRepository;
    private final ChatMessageDomainService chatMessageDomainService;

    public ChatMessageService(ChatRoomRepository chatRoomRepository,
            ChatRoomMemberRepository chatRoomMemberRepository,
            ChatMessageRepository chatMessageRepository,
            UserRepository userRepository,
            ChatMessageDomainService chatMessageDomainService) {
        this.chatRoomRepository = chatRoomRepository;
        this.chatRoomMemberRepository = chatRoomMemberRepository;
        this.chatMessageRepository = chatMessageRepository;
        this.userRepository = userRepository;
        this.chatMessageDomainService = chatMessageDomainService;
    }

    public ChatMessageDto sendMessage(Long roomId, Long userId, SendChatMessageCommand command) {
        ChatRoom room = chatRoomRepository.findByIdAndActiveTrue(roomId)
                .orElseThrow(() -> new ChatRoomNotFoundException(roomId));
        ChatRoomMember member = chatRoomMemberRepository.findByRoomIdAndUserId(roomId, userId)
                .filter(ChatRoomMember::isActive)
                .orElseThrow(ChatAccessDeniedException::new);
        User sender = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
        ChatMessage replyTo = null;
        if (command.replyToId() != null) {
            replyTo = chatMessageRepository.findById(command.replyToId())
                    .orElseThrow(() -> new ChatMessageNotFoundException(command.replyToId()));
        }
        ChatMessage message = chatMessageDomainService.create(
                room,
                sender,
                command.messageType(),
                command.content(),
                command.fileUrl(),
                command.fileName(),
                command.fileSize(),
                replyTo);
        chatMessageRepository.save(message);
        member.updateLastReadAt(Instant.now());
        return ChatMessageDto.from(message);
    }

    public Page<ChatMessageDto> getMessages(Long roomId, Pageable pageable) {
        Page<ChatMessage> messages = chatMessageRepository
                .findByRoomIdAndDeletedFalseOrderByCreatedAtDesc(roomId, pageable);
        return messages.map(ChatMessageDto::from);
    }

    public List<ChatMessageDto> getRecentMessages(Long roomId) {
        return chatMessageRepository.findTop50ByRoomIdAndDeletedFalseOrderByCreatedAtDesc(roomId)
                .stream()
                .map(ChatMessageDto::from)
                .collect(Collectors.toList());
    }

    public void deleteMessage(Long messageId, Long userId) {
        ChatMessage message = chatMessageRepository.findById(messageId)
                .orElseThrow(() -> new ChatMessageNotFoundException(messageId));
        if (!message.getSender().getId().equals(userId)) {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + userId));
            if (!user.isAdmin()) {
                throw new ChatAccessDeniedException();
            }
        }
        chatMessageDomainService.delete(message);
    }
}
