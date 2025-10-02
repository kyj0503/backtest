package com.webproject.backtest_be_spring.chat.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.webproject.backtest_be_spring.chat.application.command.CreateChatRoomCommand;
import com.webproject.backtest_be_spring.chat.application.dto.ChatRoomDto;
import com.webproject.backtest_be_spring.chat.application.dto.ChatRoomMemberDto;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMemberRole;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomMemberRepository;
import com.webproject.backtest_be_spring.chat.domain.repository.ChatRoomRepository;
import com.webproject.backtest_be_spring.chat.domain.service.ChatRoomDomainService;
import com.webproject.backtest_be_spring.user.domain.model.InvestmentType;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class ChatRoomServiceTest {

    @Mock
    private ChatRoomRepository chatRoomRepository;

    @Mock
    private ChatRoomMemberRepository chatRoomMemberRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private ChatRoomDomainService chatRoomDomainService;

    @InjectMocks
    private ChatRoomService chatRoomService;

    @Test
    @DisplayName("채팅방 생성 시 생성자 회원이 관리자 역할로 추가된다")
    void createRoomRegistersCreatorAsAdmin() {
        User creator = user(1L, "alice", false);
        when(userRepository.findById(1L)).thenReturn(Optional.of(creator));
        when(chatRoomRepository.existsByNameIgnoreCase("스터디방")).thenReturn(false);
        when(chatRoomRepository.save(any(ChatRoom.class))).thenAnswer(invocation -> {
            ChatRoom room = invocation.getArgument(0);
            ReflectionTestUtils.setField(room, "id", 10L);
            ReflectionTestUtils.setField(room, "currentMembers", 0);
            ReflectionTestUtils.setField(room, "createdAt", Instant.now());
            ReflectionTestUtils.setField(room, "updatedAt", Instant.now());
            return room;
        });
        when(chatRoomMemberRepository.save(any(ChatRoomMember.class))).thenAnswer(invocation -> {
            ChatRoomMember member = invocation.getArgument(0);
            ReflectionTestUtils.setField(member, "id", 100L);
            return member;
        });

        CreateChatRoomCommand command = new CreateChatRoomCommand("스터디방", "주식 공부", ChatRoomType.PRIVATE, 50);

        ChatRoomDto result = chatRoomService.createRoom(1L, command);

        assertThat(result.name()).isEqualTo("스터디방");
        assertThat(result.creator().id()).isEqualTo(1L);
        verify(chatRoomMemberRepository).save(any(ChatRoomMember.class));
        verify(chatRoomDomainService).increaseMembers(any(ChatRoom.class));
    }

    @Test
    @DisplayName("비활성 구성원이 다시 참여하면 활성화되고 인원 수가 증가한다")
    void joinRoomReactivatesInactiveMember() {
        User creator = user(1L, "alice", false);
        ChatRoom room = ChatRoom.create("스터디", "테스트", ChatRoomType.PUBLIC, 10, creator);
        ReflectionTestUtils.setField(room, "id", 10L);
        ReflectionTestUtils.setField(room, "currentMembers", 1);
        User memberUser = user(2L, "bob", false);
        ChatRoomMember member = ChatRoomMember.create(room, memberUser, ChatMemberRole.MEMBER);
        member.markInactive();

        when(chatRoomRepository.findByIdAndActiveTrue(10L)).thenReturn(Optional.of(room));
        when(chatRoomMemberRepository.findByRoomIdAndUserId(10L, 2L)).thenReturn(Optional.of(member));
        when(userRepository.findById(2L)).thenReturn(Optional.of(memberUser));

        ChatRoomMemberDto dto = chatRoomService.joinRoom(10L, 2L);

        assertThat(dto.active()).isTrue();
        verify(chatRoomDomainService).increaseMembers(room);
    }

    @Test
    @DisplayName("정원 초과인 채팅방에 입장하면 예외가 발생한다")
    void joinRoomFailsWhenFull() {
        User creator = user(1L, "alice", false);
        ChatRoom room = ChatRoom.create("가득찬 방", "테스트", ChatRoomType.PUBLIC, 1, creator);
        ReflectionTestUtils.setField(room, "id", 20L);
        ReflectionTestUtils.setField(room, "currentMembers", 1);

        when(chatRoomRepository.findByIdAndActiveTrue(20L)).thenReturn(Optional.of(room));
        when(userRepository.findById(3L)).thenReturn(Optional.of(user(3L, "charlie", false)));
        when(chatRoomMemberRepository.findByRoomIdAndUserId(20L, 3L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> chatRoomService.joinRoom(20L, 3L))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("채팅방 인원이 가득 찼습니다");
        verify(chatRoomMemberRepository, never()).save(any(ChatRoomMember.class));
        verify(chatRoomDomainService, never()).increaseMembers(room);
    }

    private User user(Long id, String username, boolean admin) {
        User user = User.create(username, username + "@example.com", "Password!234", new byte[]{1, 2, 3}, InvestmentType.BALANCED);
        ReflectionTestUtils.setField(user, "id", id);
        ReflectionTestUtils.setField(user, "admin", admin);
        return user;
    }
}
