package com.webproject.backtest_be_spring.common.presentation.handler;

import com.webproject.backtest_be_spring.auth.application.exception.InvalidCredentialsException;
import com.webproject.backtest_be_spring.auth.application.exception.InvalidRefreshTokenException;
import com.webproject.backtest_be_spring.auth.application.exception.UserAlreadyExistsException;
import com.webproject.backtest_be_spring.auth.application.exception.UserNotFoundException;
import com.webproject.backtest_be_spring.admin.application.exception.AdminAccessDeniedException;
import com.webproject.backtest_be_spring.admin.application.exception.NoticeNotFoundException;
import com.webproject.backtest_be_spring.admin.application.exception.ReportNotFoundException;
import com.webproject.backtest_be_spring.community.application.exception.CommentNotFoundException;
import com.webproject.backtest_be_spring.community.application.exception.CommunityAccessDeniedException;
import com.webproject.backtest_be_spring.community.application.exception.PostNotFoundException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatAccessDeniedException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatMessageNotFoundException;
import com.webproject.backtest_be_spring.chat.application.exception.ChatRoomNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(UserAlreadyExistsException.class)
    public ResponseEntity<ErrorResponse> handleUserAlreadyExists(UserAlreadyExistsException ex, HttpServletRequest request) {
        return build(HttpStatus.CONFLICT, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler({InvalidCredentialsException.class, InvalidRefreshTokenException.class})
    public ResponseEntity<ErrorResponse> handleInvalidCredentials(RuntimeException ex, HttpServletRequest request) {
        return build(HttpStatus.UNAUTHORIZED, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler(UserNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleUserNotFound(UserNotFoundException ex, HttpServletRequest request) {
        return build(HttpStatus.NOT_FOUND, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler({PostNotFoundException.class, CommentNotFoundException.class})
    public ResponseEntity<ErrorResponse> handleCommunityNotFound(RuntimeException ex, HttpServletRequest request) {
        return build(HttpStatus.NOT_FOUND, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler(CommunityAccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleCommunityAccessDenied(CommunityAccessDeniedException ex,
            HttpServletRequest request) {
        return build(HttpStatus.FORBIDDEN, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler({ChatRoomNotFoundException.class, ChatMessageNotFoundException.class,
            ReportNotFoundException.class, NoticeNotFoundException.class})
    public ResponseEntity<ErrorResponse> handleDomainNotFound(RuntimeException ex, HttpServletRequest request) {
        return build(HttpStatus.NOT_FOUND, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler(ChatAccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleChatAccessDenied(ChatAccessDeniedException ex,
            HttpServletRequest request) {
        return build(HttpStatus.FORBIDDEN, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler(AdminAccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAdminAccessDenied(AdminAccessDeniedException ex,
            HttpServletRequest request) {
        return build(HttpStatus.FORBIDDEN, ex.getMessage(), request.getRequestURI());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, BindException.class, IllegalArgumentException.class})
    public ResponseEntity<ErrorResponse> handleValidation(Exception ex, HttpServletRequest request) {
        return build(HttpStatus.BAD_REQUEST, "잘못된 요청입니다.", request.getRequestURI());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneral(Exception ex, HttpServletRequest request) {
        return build(HttpStatus.INTERNAL_SERVER_ERROR, ex.getMessage(), request.getRequestURI());
    }

    private ResponseEntity<ErrorResponse> build(HttpStatus status, String message, String path) {
        return ResponseEntity.status(status)
                .body(ErrorResponse.of(status.value(), status.getReasonPhrase(), message, path));
    }
}
