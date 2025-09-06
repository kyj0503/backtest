"""
날짜 범위 값 객체 (Value Object)

백테스트 기간을 나타내는 불변 객체입니다.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import logging


@dataclass(frozen=True)
class DateRange:
    """백테스트 날짜 범위 값 객체"""
    
    start_date: date
    end_date: date
    
    def __post_init__(self):
        """초기화 후 검증"""
        if self.start_date >= self.end_date:
            raise ValueError(f"시작일({self.start_date})은 종료일({self.end_date})보다 빨라야 합니다.")
        
        # 너무 오래된 날짜 검증
        min_date = date(2000, 1, 1)
        if self.start_date < min_date:
            raise ValueError(f"시작일은 {min_date} 이후여야 합니다.")
        
        # 미래 날짜 검증
        today = date.today()
        if self.end_date > today:
            raise ValueError(f"종료일은 오늘({today}) 이전이어야 합니다.")
    
    @classmethod
    def from_strings(cls, start_str: str, end_str: str) -> "DateRange":
        """문자열로부터 DateRange 객체 생성"""
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            return cls(start_date, end_date)
        except ValueError as e:
            raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD): {e}")
    
    @classmethod
    def last_n_years(cls, years: int) -> "DateRange":
        """최근 N년 기간의 DateRange 생성"""
        if years <= 0:
            raise ValueError("연도는 양수여야 합니다.")
        
        end_date = date.today()
        start_date = date(end_date.year - years, end_date.month, end_date.day)
        return cls(start_date, end_date)
    
    @classmethod
    def last_n_months(cls, months: int) -> "DateRange":
        """최근 N개월 기간의 DateRange 생성"""
        if months <= 0:
            raise ValueError("개월 수는 양수여야 합니다.")
        
        end_date = date.today()
        year = end_date.year
        month = end_date.month - months
        
        # 월 계산 조정
        while month <= 0:
            month += 12
            year -= 1
        
        start_date = date(year, month, end_date.day)
        return cls(start_date, end_date)
    
    def duration_days(self) -> int:
        """기간을 일수로 반환"""
        return (self.end_date - self.start_date).days
    
    def duration_months(self) -> int:
        """기간을 개월수로 추정 반환"""
        return self.duration_days() // 30
    
    def duration_years(self) -> float:
        """기간을 연수로 반환"""
        return self.duration_days() / 365.25
    
    def contains(self, target_date: date) -> bool:
        """특정 날짜가 범위에 포함되는지 확인"""
        return self.start_date <= target_date <= self.end_date
    
    def overlaps_with(self, other: "DateRange") -> bool:
        """다른 DateRange와 겹치는지 확인"""
        return (self.start_date <= other.end_date and 
                other.start_date <= self.end_date)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "duration_days": self.duration_days(),
            "duration_years": round(self.duration_years(), 2)
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.start_date} ~ {self.end_date} ({self.duration_days()}일)"
