package com.webproject.backtest_be_spring.application.admin;

import com.webproject.backtest_be_spring.application.admin.command.CreateNoticeCommand;
import com.webproject.backtest_be_spring.application.admin.command.UpdateNoticeCommand;
import com.webproject.backtest_be_spring.application.admin.dto.SystemNoticeDto;
import com.webproject.backtest_be_spring.application.admin.exception.AdminAccessDeniedException;
import com.webproject.backtest_be_spring.application.admin.exception.NoticeNotFoundException;
import com.webproject.backtest_be_spring.application.auth.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.domain.admin.model.SystemNotice;
import com.webproject.backtest_be_spring.domain.admin.model.SystemNoticePriority;
import com.webproject.backtest_be_spring.domain.admin.model.SystemNoticeType;
import com.webproject.backtest_be_spring.domain.admin.repository.SystemNoticeRepository;
import com.webproject.backtest_be_spring.domain.user.model.User;
import com.webproject.backtest_be_spring.domain.user.repository.UserRepository;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class AdminNoticeService {

    private final SystemNoticeRepository systemNoticeRepository;
    private final UserRepository userRepository;

    public AdminNoticeService(SystemNoticeRepository systemNoticeRepository, UserRepository userRepository) {
        this.systemNoticeRepository = systemNoticeRepository;
        this.userRepository = userRepository;
    }

    public SystemNoticeDto create(Long adminId, CreateNoticeCommand command) {
        User admin = userRepository.findById(adminId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + adminId));
        if (!admin.isAdmin()) {
            throw new AdminAccessDeniedException();
        }
        if (command.title() == null || command.title().isBlank()) {
            throw new IllegalArgumentException("공지 제목은 필수입니다.");
        }
        if (command.content() == null || command.content().isBlank()) {
            throw new IllegalArgumentException("공지 내용은 필수입니다.");
        }
        SystemNotice notice = SystemNotice.create(
                command.title(),
                command.content(),
                command.noticeType() != null ? command.noticeType() : SystemNoticeType.GENERAL,
                command.priority() != null ? command.priority() : SystemNoticePriority.NORMAL,
                command.popup(),
                command.pinned(),
                command.startDate(),
                command.endDate(),
                command.active(),
                admin);
        systemNoticeRepository.save(notice);
        return SystemNoticeDto.from(notice);
    }

    public SystemNoticeDto update(Long adminId, Long noticeId, UpdateNoticeCommand command) {
        User admin = userRepository.findById(adminId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + adminId));
        if (!admin.isAdmin()) {
            throw new AdminAccessDeniedException();
        }
        SystemNotice notice = systemNoticeRepository.findById(noticeId)
                .orElseThrow(() -> new NoticeNotFoundException(noticeId));
        notice.update(command.title(), command.content(), command.noticeType(), command.priority(), command.popup(),
                command.pinned(), command.startDate(), command.endDate(), command.active());
        return SystemNoticeDto.from(notice);
    }

    public Page<SystemNoticeDto> getNotices(Pageable pageable) {
        return systemNoticeRepository.findAll(pageable).map(SystemNoticeDto::from);
    }
}
