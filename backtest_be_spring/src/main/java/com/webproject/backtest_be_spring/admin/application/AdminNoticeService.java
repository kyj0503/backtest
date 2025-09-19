package com.webproject.backtest_be_spring.admin.application;

import com.webproject.backtest_be_spring.admin.application.command.CreateNoticeCommand;
import com.webproject.backtest_be_spring.admin.application.command.UpdateNoticeCommand;
import com.webproject.backtest_be_spring.admin.application.dto.SystemNoticeDto;
import com.webproject.backtest_be_spring.admin.application.exception.AdminAccessDeniedException;
import com.webproject.backtest_be_spring.admin.application.exception.NoticeNotFoundException;
import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.admin.domain.model.SystemNotice;
import com.webproject.backtest_be_spring.admin.domain.repository.SystemNoticeRepository;
import com.webproject.backtest_be_spring.admin.domain.service.SystemNoticeDomainService;
import com.webproject.backtest_be_spring.user.domain.model.User;
import com.webproject.backtest_be_spring.user.domain.repository.UserRepository;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@Transactional
public class AdminNoticeService {

    private final SystemNoticeRepository systemNoticeRepository;
    private final UserRepository userRepository;
    private final SystemNoticeDomainService systemNoticeDomainService;

    public AdminNoticeService(SystemNoticeRepository systemNoticeRepository, UserRepository userRepository,
            SystemNoticeDomainService systemNoticeDomainService) {
        this.systemNoticeRepository = systemNoticeRepository;
        this.userRepository = userRepository;
        this.systemNoticeDomainService = systemNoticeDomainService;
    }

    public SystemNoticeDto create(Long adminId, CreateNoticeCommand command) {
        User admin = userRepository.findById(adminId)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. id=" + adminId));
        if (!admin.isAdmin()) {
            throw new AdminAccessDeniedException();
        }
        SystemNotice notice = systemNoticeDomainService.create(
                command.title(),
                command.content(),
                command.noticeType(),
                command.priority(),
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
        systemNoticeDomainService.update(notice, command.title(), command.content(), command.noticeType(),
                command.priority(), command.popup(), command.pinned(), command.startDate(), command.endDate(),
                command.active());
        return SystemNoticeDto.from(notice);
    }

    public Page<SystemNoticeDto> getNotices(Pageable pageable) {
        return systemNoticeRepository.findAll(pageable).map(SystemNoticeDto::from);
    }
}
