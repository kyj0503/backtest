package com.webproject.backtest_be_spring.presentation.websocket.chat;

import com.webproject.backtest_be_spring.application.chat.ChatMessagingFacade;
import com.webproject.backtest_be_spring.application.chat.command.SendChatMessageCommand;
import com.webproject.backtest_be_spring.infrastructure.security.UserPrincipal;
import com.webproject.backtest_be_spring.domain.chat.model.ChatMessageType;
import com.webproject.backtest_be_spring.presentation.api.chat.dto.ChatMessageRequest;
import jakarta.validation.Valid;
import java.security.Principal;
import java.util.Locale;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Controller;

@Controller
public class ChatWebSocketController {

    private final ChatMessagingFacade chatMessagingFacade;

    public ChatWebSocketController(ChatMessagingFacade chatMessagingFacade) {
        this.chatMessagingFacade = chatMessagingFacade;
    }

    @MessageMapping("/chat/{roomId}")
    public void handleChat(@DestinationVariable Long roomId, @Payload @Valid ChatMessageRequest request,
            Principal principal) {
        UserPrincipal user = extractPrincipal(principal);
        chatMessagingFacade.send(roomId, user.getId(), toCommand(request));
    }

    private UserPrincipal extractPrincipal(Principal principal) {
        if (principal instanceof UsernamePasswordAuthenticationToken token
                && token.getPrincipal() instanceof UserPrincipal userPrincipal) {
            return userPrincipal;
        }
        if (principal instanceof UserPrincipal userPrincipal) {
            return userPrincipal;
        }
        throw new IllegalStateException("인증되지 않은 사용자입니다.");
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
