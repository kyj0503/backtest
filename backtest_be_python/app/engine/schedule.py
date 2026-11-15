"""적립(DCA)·리밸런싱 예정일 (Go internal/schedule).

월 단위 주기는 시작일의 "N번째 요일"을 유지한다. 그 달에 N번째 요일이 없으면 그 달의 마지막 같은
요일로 맞춘다. 주 단위는 7일·14일 간격이다. 월을 30일로 근사하지 않는다(F03).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

# 이름 → (주 단위 여부, 간격)
FREQUENCIES = {
    "weekly_1": (True, 1),
    "weekly_2": (True, 2),
    "monthly_1": (False, 1),
    "monthly_2": (False, 2),
    "monthly_3": (False, 3),
    "monthly_6": (False, 6),
    "monthly_12": (False, 12),
}

NAMES = ["weekly_1", "weekly_2", "monthly_1", "monthly_2", "monthly_3", "monthly_6", "monthly_12"]


def known(name: object) -> bool:
    return isinstance(name, str) and name in FREQUENCIES


def _nth_weekday(cursor: date, months: int, weekday: int, nth: int) -> date:
    """cursor의 달에서 months만큼 뒤 달의 nth(0부터) 번째 weekday."""
    total = cursor.year * 12 + (cursor.month - 1) + months
    first = date(total // 12, total % 12 + 1, 1)
    offset = (weekday - first.weekday() + 7) % 7
    candidate = first + timedelta(days=offset + 7 * nth)
    if candidate.month != first.month:
        candidate -= timedelta(days=7)
    return candidate


def dates(start: int, end: int, name: str) -> List[int]:
    """start 다음의 예정일들(start 제외, end 포함). 주기 이름이 틀리면 빈 목록."""
    f = FREQUENCIES.get(name) if isinstance(name, str) else None
    if f is None:
        return []
    weekly, interval = f
    out: List[int] = []
    start_d = date.fromordinal(start)
    nth = (start_d.day - 1) // 7
    weekday = start_d.weekday()
    cursor = start_d
    while True:
        if weekly:
            cursor = cursor + timedelta(days=7 * interval)
        else:
            cursor = _nth_weekday(cursor, interval, weekday, nth)
        o = cursor.toordinal()
        if o > end:
            return out
        out.append(o)
