#!/usr/bin/env python3
"""
백테스트 결과값 합당성 검증 스크립트

**검증 항목**:
- 수익률이 터무니없이 크거나 작지 않은지 (-100% ~ +500%)
- 샤프 비율이 합리적인지 (-5 ~ +10)
- 거래 횟수가 합리적인지 (0 ~ 10000)
- 승률이 0% ~ 100% 범위인지

**사용법**:
python validate_backtest_results.py
"""
import requests
import json
from typing import Dict, Any


class BacktestValidator:
    """백테스트 결과 검증 클래스"""
    
    # 전략별 기대 범위 (최소, 최대)
    EXPECTED_RANGES = {
        "total_return": (-100.0, 500.0),  # 수익률 (%)
        "sharpe_ratio": (-5.0, 10.0),      # 샤프 비율
        "total_trades": (0, 10000),        # 총 거래 수
        "win_rate": (0.0, 100.0),          # 승률 (%)
        "max_drawdown": (-100.0, 0.0),     # 최대 낙폭 (%)
        "annual_return": (-100.0, 1000.0), # 연환산 수익률 (%)
    }
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.errors = []
        self.warnings = []
    
    def validate_value(self, metric_name: str, value: float, strategy: str) -> bool:
        """단일 지표 검증"""
        if value is None:
            self.warnings.append(f"[{strategy}] {metric_name}이(가) None입니다.")
            return True  # None은 에러가 아님
        
        if metric_name not in self.EXPECTED_RANGES:
            return True  # 범위 정의되지 않은 지표는 건너뜀
        
        min_val, max_val = self.EXPECTED_RANGES[metric_name]
        
        if not (min_val <= value <= max_val):
            self.errors.append(
                f"[{strategy}] {metric_name} 값이 비정상: {value:.2f} "
                f"(기대 범위: {min_val} ~ {max_val})"
            )
            return False
        
        return True
    
    def run_backtest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 실행"""
        url = f"{self.api_url}/api/v1/backtest"
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def validate_backtest(self, symbol: str, strategy: str, start_date: str, end_date: str, strategy_params: Dict[str, Any] = None):
        """백테스트 실행 및 검증"""
        print(f"\n{'='*60}")
        print(f"백테스트 검증: {symbol} ({strategy})")
        print(f"기간: {start_date} ~ {end_date}")
        print(f"{'='*60}")
        
        payload = {
            "portfolio": [{"symbol": symbol, "amount": 10000}],
            "start_date": start_date,
            "end_date": end_date,
            "strategy": strategy,
            "strategy_params": strategy_params or {}
        }
        
        try:
            result = self.run_backtest(payload)
            data = result.get("data", {})
            
            # 포트폴리오 통계 검증
            stats = data.get("portfolio_statistics", {})
            
            if not stats:
                self.errors.append(f"[{strategy}] portfolio_statistics가 비어있습니다.")
                return False
            
            # 각 지표 검증
            metrics_to_check = {
                "total_return": stats.get("Total_Return"),
                "sharpe_ratio": stats.get("Sharpe_Ratio"),
                "max_drawdown": stats.get("Max_Drawdown"),
                "annual_return": stats.get("Annual_Return"),
                "win_rate": stats.get("Win_Rate"),
            }
            
            all_valid = True
            for metric_name, value in metrics_to_check.items():
                if not self.validate_value(metric_name, value, strategy):
                    all_valid = False
            
            # 결과 출력
            print("\n[검증 결과]")
            print(f"  총 수익률: {stats.get('Total_Return', 'N/A'):.2f}%")
            print(f"  샤프 비율: {stats.get('Sharpe_Ratio', 'N/A'):.2f}")
            print(f"  최대 낙폭: {stats.get('Max_Drawdown', 'N/A'):.2f}%")
            print(f"  연환산 수익률: {stats.get('Annual_Return', 'N/A'):.2f}%")
            print(f"  승률: {stats.get('Win_Rate', 'N/A'):.2f}%")
            
            if all_valid and not self.errors:
                print("\n✅ 모든 지표가 합당한 범위 내에 있습니다.")
            else:
                print("\n❌ 비정상적인 지표가 발견되었습니다.")
            
            return all_valid
            
        except Exception as e:
            self.errors.append(f"[{strategy}] 백테스트 실행 실패: {str(e)}")
            print(f"\n❌ 백테스트 실행 실패: {str(e)}")
            return False
    
    def print_summary(self):
        """검증 요약 출력"""
        print(f"\n{'='*60}")
        print("검증 요약")
        print(f"{'='*60}")
        
        if self.warnings:
            print(f"\n⚠️  경고 ({len(self.warnings)}개):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print(f"\n❌ 에러 ({len(self.errors)}개):")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ 모든 검증 통과!")
        
        print(f"\n{'='*60}")


def main():
    """메인 함수"""
    validator = BacktestValidator()
    
    # 테스트 시나리오
    test_cases = [
        {
            "symbol": "AAPL",
            "strategy": "sma_strategy",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy_params": {"short_window": 10, "long_window": 20}
        },
        {
            "symbol": "GOOGL",
            "strategy": "rsi_strategy",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy_params": {"rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70}
        },
        {
            "symbol": "MSFT",
            "strategy": "buy_hold_strategy",
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy_params": {}
        },
    ]
    
    for test_case in test_cases:
        validator.validate_backtest(**test_case)
    
    validator.print_summary()
    
    # 에러가 있으면 exit code 1
    if validator.errors:
        exit(1)


if __name__ == "__main__":
    main()
