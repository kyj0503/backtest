"""HTTP 상태 코드로 바로 옮겨지는 계산·시세 오류 (Go internal/apperr와 같은 분류).

    validation   422  요청 값이 잘못됨
    not_found    404  시세가 없음
    unavailable  503  외부 제공업체·DB를 지금 쓸 수 없음 (Retry-After: 30)

detail은 응답 본문 {"detail": ...}에 그대로 실린다.
"""
from __future__ import annotations


class AppError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"{status} {detail}")
        self.status = status
        self.detail = detail


def validation(detail: str) -> AppError:
    return AppError(422, detail)


def not_found(detail: str) -> AppError:
    return AppError(404, detail)


def unavailable(detail: str) -> AppError:
    return AppError(503, detail)


def is_not_found(err: BaseException) -> bool:
    return isinstance(err, AppError) and err.status == 404
