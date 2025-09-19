package com.webproject.backtest_be_spring.chat.domain.service;

import com.webproject.backtest_be_spring.chat.domain.model.ChatRoom;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

@Service
public class ChatRoomDomainService {

    public void increaseMembers(ChatRoom room) {
        Assert.notNull(room, "room must not be null");
        room.incrementMembers();
    }

    public void decreaseMembers(ChatRoom room) {
        Assert.notNull(room, "room must not be null");
        room.decrementMembers();
    }

    public void deactivate(ChatRoom room) {
        Assert.notNull(room, "room must not be null");
        room.update(room.getName(), room.getDescription(), room.getRoomType(), room.getMaxMembers(), false);
    }
}
