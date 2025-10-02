package com.webproject.backtest_be_spring.chat.application;

import static com.webproject.backtest_be_spring.support.TestFixtures.chatMember;
import static com.webproject.backtest_be_spring.support.TestFixtures.chatMessage;
import static com.webproject.backtest_be_spring.support.TestFixtures.chatRoom;
import static com.webproject.backtest_be_spring.support.TestFixtures.user;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.webproject.backtest_be_spring.chat.application.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.chat.application.dto.ChatMessageDto;
import com.webproject.backtest_be_spring.chat.application.exception.ChatAccessDeniedException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatMessageNotFoundException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatRoomNotFoundException;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessage;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessageType;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatMessageRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomMemberRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomRepository;
import com.webproject.backtest_be_spring.chat.domain.service.ChatMessageDomainService;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ChatMessageServiceTest {

    @Mock
    private ChatRoomRepository chatRoomRepository;

    @Mock
    private ChatRoomMemberRepository chatRoomMemberRepository;

    @Mock
    private ChatMessageRepository chatMessageRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private ChatMessageDomainService chatMessageDomainService;

    @InjectMocks
    private ChatMessageService chatMessageService;

    @Test
    @DisplayName("활성 구성원은 채팅 메시지를 보낼 수 있다")
    void sendMessageSucceedsForActiveMember() {
        User sender = user(1L, "alice", false);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatRoomMember member = ChatRoomMember.create(room, sender, null);
        when(chatRoomRepository.findByIdAndActiveTrue(10L)).thenReturn(Optional.of(room));
        when(chatRoomMemberRepository.findByRoomIdAndUserId(10L, 1L)).thenReturn(Optional.of(member));
        when(userRepository.findById(1L)).thenReturn(Optional.of(sender));

        ChatMessage message = chatMessage(30L, room, sender, ChatMessageType.TEXT, "hello");
        when(chatMessageDomainService.create(any(), any(), any(), any(), any(), any(), any(), any())).thenReturn(message);

        ChatMessageDto result = chatMessageService.sendMessage(10L, 1L, new SendChatMessageCommand(ChatMessageType.TEXT, "hello", null, null, null, null));

        assertThat(result.id()).isEqualTo(30L);
        assertThat(result.content()).isEqualTo("hello");
        assertThat(member.getLastReadAt()).isNotNull();
        verify(chatMessageRepository).save(message);
    }

    @Test
    @DisplayName("채팅방이 없으면 메시지를 보낼 수 없다")
    void sendMessageFailsWhenRoomMissing() {
        when(chatRoomRepository.findByIdAndActiveTrue(10L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> chatMessageService.sendMessage(10L, 1L,
                new SendChatMessageCommand(ChatMessageType.TEXT, "hello", null, null, null, null)))
                .isInstanceOf(ChatRoomNotFoundException.class);
    }

    @Test
    @DisplayName("비활성 구성원은 메시지를 보낼 수 없다")
    void sendMessageFailsWhenMemberInactive() {
        User sender = user(1L, "alice", false);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatRoomMember member = ChatRoomMember.create(room, sender, null);
        member.markInactive();
        when(chatRoomRepository.findByIdAndActiveTrue(10L)).thenReturn(Optional.of(room));
        when(chatRoomMemberRepository.findByRoomIdAndUserId(10L, 1L)).thenReturn(Optional.of(member));

        assertThatThrownBy(() -> chatMessageService.sendMessage(10L, 1L,
                new SendChatMessageCommand(ChatMessageType.TEXT, "hello", null, null, null, null)))
                .isInstanceOf(ChatAccessDeniedException.class);
    }

    @Test
    @DisplayName("메시지 작성자가 아니더라도 관리자는 메시지를 삭제할 수 있다")
    void deleteMessageAllowsAdmin() {
        User sender = user(1L, "alice", false);
        User admin = user(2L, "admin", true);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatMessage message = chatMessage(300L, room, sender, ChatMessageType.TEXT, "hello");

        when(chatMessageRepository.findById(300L)).thenReturn(Optional.of(message));
        when(userRepository.findById(2L)).thenReturn(Optional.of(admin));

        chatMessageService.deleteMessage(300L, 2L);

        verify(chatMessageDomainService).delete(message);
    }

    @Test
    @DisplayName("관리자가 아니면 다른 사용자의 메시지를 삭제할 수 없다")
    void deleteMessageRejectsNonAdmin() {
        User sender = user(1L, "alice", false);
        User other = user(3L, "bob", false);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatMessage message = chatMessage(301L, room, sender, ChatMessageType.TEXT, "hello");

        when(chatMessageRepository.findById(301L)).thenReturn(Optional.of(message));
        when(userRepository.findById(3L)).thenReturn(Optional.of(other));

        assertThatThrownBy(() -> chatMessageService.deleteMessage(301L, 3L))
                .isInstanceOf(ChatAccessDeniedException.class);
        verify(chatMessageDomainService, never()).delete(any(ChatMessage.class));
    }

    @Test
    @DisplayName("존재하지 않는 사용자는 메시지를 보낼 수 없다")
    void sendMessageFailsWhenUserMissing() {
        User sender = user(1L, "alice", false);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatRoomMember member = chatMember(200L, room, sender, null, true);

        when(chatRoomRepository.findByIdAndActiveTrue(10L)).thenReturn(Optional.of(room));
        when(chatRoomMemberRepository.findByRoomIdAndUserId(10L, 1L)).thenReturn(Optional.of(member));
        when(userRepository.findById(1L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> chatMessageService.sendMessage(10L, 1L,
                        new SendChatMessageCommand(ChatMessageType.TEXT, "hello", null, null, null, null)))
                .isInstanceOf(UserNotFoundException.class);
        verify(chatMessageDomainService, never()).create(any(), any(), any(), any(), any(), any(), any(), any());
    }

    @Test
    @DisplayName("답장 대상이 존재하지 않으면 메시지 생성에 실패한다")
    void sendMessageFailsWhenReplyTargetMissing() {
        User sender = user(1L, "alice", false);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatRoomMember member = chatMember(200L, room, sender, null, true);

        when(chatRoomRepository.findByIdAndActiveTrue(10L)).thenReturn(Optional.of(room));
        when(chatRoomMemberRepository.findByRoomIdAndUserId(10L, 1L)).thenReturn(Optional.of(member));
        when(userRepository.findById(1L)).thenReturn(Optional.of(sender));
        when(chatMessageRepository.findById(999L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> chatMessageService.sendMessage(10L, 1L,
                        new SendChatMessageCommand(ChatMessageType.TEXT, "hello", null, null, null, 999L)))
                .isInstanceOf(ChatMessageNotFoundException.class);
        verify(chatMessageRepository, never()).save(any(ChatMessage.class));
    }

    @Test
    @DisplayName("작성자는 자신의 메시지를 삭제할 수 있다")
    void deleteMessageAllowsOwner() {
        User sender = user(1L, "alice", false);
        ChatRoom room = chatRoom(10L, sender, ChatRoomType.PUBLIC, 100);
        ChatMessage message = chatMessage(400L, room, sender, ChatMessageType.TEXT, "hello");

        when(chatMessageRepository.findById(400L)).thenReturn(Optional.of(message));

        chatMessageService.deleteMessage(400L, 1L);

        verify(chatMessageDomainService).delete(message);
        verify(userRepository, never()).findById(anyLong());
    }
}
