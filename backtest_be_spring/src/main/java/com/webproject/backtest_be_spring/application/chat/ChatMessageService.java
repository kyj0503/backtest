package com.webproject.backtest_be_spring.application.chat;

import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.application.chat.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.application.chat.dto.ChatMessageDto;
import com.webproject.backtest_be_spring.application.chat.exception.ChatAccessDeniedException;
import com.webproject.backtest_be_spring.application.chat.exception.ChatMessageNotFoundException;
import com.webproject.backtest_be_spring.application.chat.exception.ChatRoomNotFoundException;
import com.webproject.backtest_be_spring.domain.chat.model.ChatMessage;
import com.webproject.backtest_be_spring.domain.chat.model.ChatMessageType;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoom;
import com.webproject.backtest_be_spring.domain.chat.model.ChatRoomMember;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatMessageRepository;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatRoomMemberRepository;
import com.webproject.backtest_be_spring.domain.chat.repository.ChatRoomRepository;
import com.webproject.backtest_be_spring.domain.user.model.User;
import com.webproject.backtest_be_spring.domain.user.repository.UserRepository;
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

    public ChatMessageService(ChatRoomRepository chatRoomRepository,
            ChatRoomMemberRepository chatRoomMemberRepository,
            ChatMessageRepository chatMessageRepository,
            UserRepository userRepository) {
        this.chatRoomRepository = chatRoomRepository;
        this.chatRoomMemberRepository = chatRoomMemberRepository;
        this.chatMessageRepository = chatMessageRepository;
        this.userRepository = userRepository;
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
        ChatMessage message = ChatMessage.create(
                room,
                sender,
                Optional.ofNullable(command.messageType()).orElse(ChatMessageType.TEXT),
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
        message.markDeleted();
    }
}
