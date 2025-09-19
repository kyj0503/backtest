package com.webproject.backtest_be_spring.admin.domain.service;

import com.webproject.backtest_be_spring.admin.domain.model.SystemNotice;
import com.webproject.backtest_be_spring.admin.domain.model.SystemNoticePriority;
import com.webproject.backtest_be_spring.admin.domain.model.SystemNoticeType;
import com.webproject.backtest_be_spring.user.domain.model.User;
import java.time.Instant;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

@Service
public class SystemNoticeDomainService {

    public SystemNotice create(String title, String content, SystemNoticeType type, SystemNoticePriority priority,
            Boolean popup, Boolean pinned, Instant startDate, Instant endDate, Boolean active, User creator) {
        if (title == null || title.isBlank()) {
            throw new IllegalArgumentException("공지 제목은 필수입니다.");
        }
        if (content == null || content.isBlank()) {
            throw new IllegalArgumentException("공지 내용은 필수입니다.");
        }
        SystemNoticeType resolvedType = type == null ? SystemNoticeType.GENERAL : type;
        SystemNoticePriority resolvedPriority = priority == null ? SystemNoticePriority.NORMAL : priority;
        return SystemNotice.create(title, content, resolvedType, resolvedPriority, popup, pinned, startDate, endDate, active, creator);
    }

    public void update(SystemNotice notice, String title, String content, SystemNoticeType type, SystemNoticePriority priority,
            Boolean popup, Boolean pinned, Instant startDate, Instant endDate, Boolean active) {
        Assert.notNull(notice, "notice must not be null");
        notice.update(title, content, type, priority, popup, pinned, startDate, endDate, active);
    }

}
