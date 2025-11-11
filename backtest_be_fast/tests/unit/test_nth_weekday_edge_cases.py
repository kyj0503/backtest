"""
Nth Weekday 엣지 케이스 테스트

존재하지 않는 N번째 요일 처리 검증
"""
import pytest
from datetime import datetime
from app.services.rebalance_helper import get_nth_weekday_of_month, get_next_nth_weekday, get_weekday_occurrence


class TestEdgeCases:
    """엣지 케이스: N번째 요일이 없는 경우"""
    
    def test_fifth_monday_doesnt_exist_fallback_to_last(self):
        """
        5번째 월요일이 없는 달 (2024년 2월)
        → 마지막 월요일(4번째)로 폴백
        """
        # 2024년 2월은 29일까지 (윤년)
        # 2월 1일 = 목요일
        # 월요일: 5일(1번째), 12일(2번째), 19일(3번째), 26일(4번째)
        # 5번째 월요일은 없음
        
        day = get_nth_weekday_of_month(2024, 2, 0, 5)  # 0 = Monday, 5번째
        
        # 마지막 월요일인 26일로 폴백되어야 함
        assert day == 26
        assert datetime(2024, 2, day).weekday() == 0  # 월요일 확인
        
    def test_fifth_friday_doesnt_exist_in_february(self):
        """
        5번째 금요일이 없는 달 (2024년 2월)
        → 마지막 금요일(4번째)로 폴백
        """
        # 2024년 2월 금요일: 2일(1번째), 9일(2번째), 16일(3번째), 23일(4번째)
        day = get_nth_weekday_of_month(2024, 2, 4, 5)  # 4 = Friday, 5번째
        
        assert day == 23  # 마지막 금요일
        assert datetime(2024, 2, day).weekday() == 4
        
    def test_fifth_saturday_exists_in_march_2024(self):
        """
        5번째 토요일이 존재하는 달 (2024년 3월)
        → 정확히 계산
        """
        # 2024년 3월은 31일까지
        # 3월 1일 = 금요일
        # 토요일: 2일(1번째), 9일(2번째), 16일(3번째), 23일(4번째), 30일(5번째)
        
        day = get_nth_weekday_of_month(2024, 3, 5, 5)  # 5 = Saturday, 5번째
        
        assert day == 30
        assert datetime(2024, 3, day).weekday() == 5
        
    def test_sequence_with_varying_nth_weekday_availability(self):
        """
        5번째 금요일로 시작 → 다음 달에 없음 → 그 다음 달에 다시 있음
        """
        # 2024년 3월 29일 (5번째 금요일)
        start = datetime(2024, 3, 29)
        assert start.weekday() == 4
        
        # 다음 달 (4월) - 5번째 금요일 계산
        next_date = get_next_nth_weekday(start, 'monthly', 1)
        
        # 4월에는 5번째 금요일이 없음 (4월 26일이 4번째 금요일)
        # 폴백 로직에 따라 4월 26일이어야 함
        assert next_date.year == 2024
        assert next_date.month == 4
        assert next_date.day == 26  # 4번째 금요일
        assert next_date.weekday() == 4
        
        # 그 다음 달 (5월) - 5번째 금요일 계산
        next_date2 = get_next_nth_weekday(next_date, 'monthly', 1)
        
        # 5월에는 5번째 금요일이 있음 (5월 31일)
        # 하지만 이전이 4번째였으므로 4번째 금요일로 계산됨
        assert next_date2.year == 2024
        assert next_date2.month == 5
        # 여기서 문제: 5번째로 시작했지만 중간에 4번째로 바뀜
        

class TestConsistencyProblem:
    """일관성 문제: N이 변경되는 문제"""
    
    def test_problem_nth_changes_over_time(self):
        """
        문제 시나리오: 5번째 금요일로 시작했지만 
        없는 달을 거치면서 4번째로 변경됨
        """
        # 1월 31일 (5번째 수요일) - 실제로는 없음, 테스트용
        # 1월의 마지막 수요일로 계산
        jan_day = get_nth_weekday_of_month(2024, 1, 2, 5)
        jan_date = datetime(2024, 1, jan_day)
        
        # 몇 번째 수요일인지 계산
        week_of_month = (jan_date.day - 1) // 7 + 1
        
        print(f"1월: {jan_date.date()}, {week_of_month}번째 수요일")
        
        # 2월로 이동
        feb_date = get_next_nth_weekday(jan_date, 'monthly', 1)
        feb_week = (feb_date.day - 1) // 7 + 1
        
        print(f"2월: {feb_date.date()}, {feb_week}번째 수요일")
        
        # N이 변경되었는지 확인
        # 이것이 문제: 원래 5번째로 시작했지만 계속 유지되지 않음


class TestProposedSolution:
    """제안된 해결책: Fallback 전략 명확화"""
    
    def test_solution_1_rollover_to_next_month_first(self):
        """
        해결책 1: 다음 달 첫 번째 해당 요일로 이월
        
        예: 2024년 2월에 5번째 금요일이 없으면
        → 3월 첫 번째 금요일 (3월 1일)
        
        장점: 투자/리밸런싱을 절대 건너뛰지 않음
        단점: 한 달 안에 두 번 실행될 수 있음
        """
        pass  # 구현 필요
        
    def test_solution_2_use_last_occurrence(self):
        """
        해결책 2: 해당 월의 마지막 해당 요일 사용 (현재 구현)
        
        예: 2024년 2월에 5번째 금요일이 없으면
        → 2월 마지막 금요일 (2월 23일, 4번째)
        
        장점: 간단하고 예측 가능
        단점: "몇 번째" 개념이 달마다 달라질 수 있음
        """
        # 현재 구현이 이 방식
        day = get_nth_weekday_of_month(2024, 2, 4, 5)
        assert day == 23  # 4번째 금요일이지만 반환됨
        
    def test_solution_3_skip_month(self):
        """
        해결책 3: 해당 월 건너뛰고 다다음 달로
        
        예: 2024년 2월에 5번째 금요일이 없으면
        → 2024년 3월 5번째 금요일 (3월 29일)
        
        장점: 일관성 유지 (항상 5번째)
        단점: 투자/리밸런싱 주기가 불규칙해짐
        """
        pass  # 구현 필요


class TestRecommendation:
    """권장 사항 테스트"""
    
    def test_recommended_approach_for_dca(self):
        """
        DCA(분할 매수)에 권장: 해결책 2 (마지막 해당 요일 사용)
        
        이유:
        - 투자를 절대 건너뛰지 않음
        - 월말 효과 (month-end effect) 최소화
        - 구현 간단
        """
        # 5번째 금요일 DCA 시작 (실제로는 4번째지만 원본 N=5로 설정)
        start = datetime(2024, 1, 26)  # 1월 4번째 금요일
        original_nth = 5  # 사용자가 5번째를 선택했다고 가정
        
        # 매월 DCA 실행
        dates = [start]
        current = start
        
        for _ in range(12):
            current = get_next_nth_weekday(current, 'monthly', 1, original_nth=original_nth)
            dates.append(current)
            
        # 모든 날짜가 금요일인지 확인
        for date in dates:
            assert date.weekday() == 4, f"{date} is not Friday"
            
        # 모든 달에 투자되었는지 확인 (년도 포함해서 unique하게)
        year_months = [(d.year, d.month) for d in dates]
        assert len(set(year_months)) == len(dates), f"Duplicate year-months detected: {year_months}"
        
        print("\n매월 DCA 날짜 (original_nth=5 유지):")
        for date in dates:
            week_num = get_weekday_occurrence(date)
            print(f"  {date.date()} ({week_num}번째 금요일)")
        
        # 각 날짜가 5번째 또는 마지막 금요일인지 확인
        for date in dates:
            week_num = get_weekday_occurrence(date)
            # 5번째이거나, 해당 월의 마지막 금요일이어야 함
            assert week_num >= 4, f"{date} is only {week_num}th Friday"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
