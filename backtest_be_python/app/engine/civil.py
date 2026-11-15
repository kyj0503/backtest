"""시간대 없는 달력 날짜 (Go internal/civil).

날짜는 date.toordinal() 정수로 다룬다. 비교·차이·더하기가 정수 연산이 되고 시간대 변환으로
날짜가 밀리는 일이 없다.
"""
from __future__ import annotations

import re
from datetime import date
from typing import List, Optional

_LAYOUT = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse(s: object) -> Optional[int]:
    """YYYY-MM-DD만 받는다(Go time.Parse("2006-01-02")와 같다). 아니면 None."""
    if not isinstance(s, str) or not _LAYOUT.match(s):
        return None
    try:
        return date.fromisoformat(s).toordinal()
    except ValueError:
        return None


def fmt(d: int) -> str:
    return date.fromordinal(d).isoformat()


def date_keys(start: int, n: int) -> List[str]:
    return [date.fromordinal(start + i).isoformat() for i in range(n)]
