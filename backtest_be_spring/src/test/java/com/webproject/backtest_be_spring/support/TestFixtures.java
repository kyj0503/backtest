package com.webproject.backtest_be_spring.support;

import com.webproject.backtest_be_spring.chat.domain.model.ChatMemberRole;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessage;
import com.webproject.backtest_be_spring.chat.domain.model.ChatMessageType;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomMember;
import com.webproject.backtest_be_spring.chat.domain.model.ChatRoomType;
import com.webproject.backtest_be_spring.community.domain.model.Post;
import com.webproject.backtest_be_spring.community.domain.model.PostCategory;
import com.webproject.backtest_be_spring.community.domain.model.PostComment;
import com.webproject.backtest_be_spring.community.domain.model.PostContentType;
import com.webproject.backtest_be_spring.community.domain.model.PostLike;
import com.webproject.backtest_be_spring.user.domain.model.InvestmentType;
import com.webproject.backtest_be_spring.user.domain.model.User;
import java.time.Instant;
import org.springframework.test.util.ReflectionTestUtils;

public final class TestFixtures {

    private TestFixtures() {
    }

    public static User user(long id, String username, boolean admin) {
        User user = User.create(
                username,
                username + "@example.com",
                "Password!234",
                new byte[] {1, 2, 3},
                InvestmentType.BALANCED);
        ReflectionTestUtils.setField(user, "id", id);
        ReflectionTestUtils.setField(user, "admin", admin);
        return user;
    }

    public static ChatRoom chatRoom(long id, User creator, ChatRoomType type, int maxMembers) {
        ChatRoom room = ChatRoom.create(
                "room-" + id,
                "채팅방 설명",
                type,
                maxMembers,
                creator);
        ReflectionTestUtils.setField(room, "id", id);
        ReflectionTestUtils.setField(room, "currentMembers", 0);
        ReflectionTestUtils.setField(room, "createdAt", Instant.now());
        ReflectionTestUtils.setField(room, "updatedAt", Instant.now());
        return room;
    }

    public static ChatRoomMember chatMember(long id, ChatRoom room, User user, ChatMemberRole role, boolean active) {
        ChatRoomMember member = ChatRoomMember.create(room, user, role);
        ReflectionTestUtils.setField(member, "id", id);
        if (!active) {
            member.markInactive();
        }
        return member;
    }

    public static ChatMessage chatMessage(long id, ChatRoom room, User sender, ChatMessageType type, String content) {
        ChatMessage message = ChatMessage.create(room, sender, type, content, null, null, null, null);
        ReflectionTestUtils.setField(message, "id", id);
        ReflectionTestUtils.setField(message, "createdAt", Instant.now());
        ReflectionTestUtils.setField(message, "updatedAt", Instant.now());
        return message;
    }

    public static Post post(long id, User author, PostCategory category) {
        Post post = Post.create(author, category, "제목-" + id, "내용", PostContentType.MARKDOWN, false, false);
        ReflectionTestUtils.setField(post, "id", id);
        ReflectionTestUtils.setField(post, "createdAt", Instant.now());
        ReflectionTestUtils.setField(post, "updatedAt", Instant.now());
        return post;
    }

    public static PostComment comment(long id, Post post, User author, PostComment parent, String content) {
        PostComment comment = PostComment.create(post, author, parent, content);
        ReflectionTestUtils.setField(comment, "id", id);
        ReflectionTestUtils.setField(comment, "createdAt", Instant.now());
        ReflectionTestUtils.setField(comment, "updatedAt", Instant.now());
        return comment;
    }

    public static PostLike postLike(Post post, User user) {
        return PostLike.create(post, user);
    }
}

