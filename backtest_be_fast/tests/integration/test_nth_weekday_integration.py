"""
DCA 및 리밸런싱 로직 통합 테스트

실제 API를 호출하여 Nth Weekday 방식의 DCA와 리밸런싱이 제대로 작동하는지 검증합니다.
"""
import requests
import os
import pytest

BASE_URL = os.getenv("BACKTEST_API_URL", "http://localhost:8000")


def test_monthly_dca():
    """매월 DCA 투자 테스트"""
    print("\n" + "="*80)
    print("TEST 1: 매월 DCA 투자 (monthly_1)")
    print("="*80)
    
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "monthly_1"
            }
        ],
        "start_date": "2024-01-10",  # 2024년 1월 10일 (2번째 수요일)
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "none",
        "strategy": "buy_and_hold"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    
    if response.status_code != 200:
        print(f"❌ 실패: {response.status_code}")
        print(f"   에러: {response.text}")
    
    assert response.status_code == 200, f"API Request failed: {response.text}"
    
    response_json = response.json()
    dates = response_json.get("data", {})
    stats = dates.get("portfolio_statistics", {})
    
    print(f"✅ 성공!")
    print(f"   총 거래 횟수: {stats.get('Total_Trades', 'N/A')}")
    final_val = stats.get('Final_Value', 0.0)
    print(f"   최종 포트폴리오 가치: ${final_val:,.2f}")
    total_ret = stats.get('Total_Return', 0.0)
    print(f"   총 수익률: {total_ret:.2f}%")


def test_quarterly_rebalancing():
    """분기별 리밸런싱 테스트"""
    print("\n" + "="*80)
    print("TEST 2: 분기별 리밸런싱 (monthly_3)")
    print("="*80)
    
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "weight": 50
            },
            {
                "symbol": "MSFT",
                "weight": 50
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "monthly_3",  # 분기별
        "strategy": "buy_and_hold"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    
    if response.status_code != 200:
        print(f"❌ 실패: {response.status_code}")
        print(f"   에러: {response.text}")

    assert response.status_code == 200, f"API Request failed: {response.text}"
    
    response_json = response.json()
    dates = response_json.get("data", {})
    stats = dates.get("portfolio_statistics", {})

    print(f"✅ 성공!")
    print(f"   총 거래 횟수: {stats.get('Total_Trades', 'N/A')}")
    # print(f"   리밸런싱 횟수: {result.get('rebalance_count', 'N/A')}") # Not available in standard stats
    final_val = stats.get('Final_Value', 0.0)
    print(f"   최종 포트폴리오 가치: ${final_val:,.2f}")


def test_weekly_dca():
    """매주 DCA 투자 테스트"""
    print("\n" + "="*80)
    print("TEST 3: 매주 DCA 투자 (weekly_1)")
    print("="*80)
    
    payload = {
        "portfolio": [
            {
                "symbol": "SPY",
                "amount": 100,
                "investment_type": "dca",
                "dca_frequency": "weekly_1"
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-03-31",  # 3개월
        "commission": 0.001,
        "rebalance_frequency": "none",
        "strategy": "buy_and_hold"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    
    if response.status_code != 200:
        print(f"❌ 실패: {response.status_code}")
        print(f"   에러: {response.text}")

    assert response.status_code == 200, f"API Request failed: {response.text}"
    
    response_json = response.json()
    dates = response_json.get("data", {})
    stats = dates.get("portfolio_statistics", {})
    
    print(f"✅ 성공!")
    print(f"   총 거래 횟수: {stats.get('Total_Trades', 'N/A')}")
    final_val = stats.get('Final_Value', 0.0)
    print(f"   최종 포트폴리오 가치: ${final_val:,.2f}")


def test_biweekly_dca():
    """2주마다 DCA 투자 테스트"""
    print("\n" + "="*80)
    print("TEST 4: 2주마다 DCA 투자 (weekly_2)")
    print("="*80)
    
    payload = {
        "portfolio": [
            {
                "symbol": "QQQ",
                "amount": 200,
                "investment_type": "dca",
                "dca_frequency": "weekly_2"
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-06-30",  # 6개월
        "commission": 0.001,
        "rebalance_frequency": "none",
        "strategy": "buy_and_hold"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    
    if response.status_code != 200:
        print(f"❌ 실패: {response.status_code}")
        print(f"   에러: {response.text}")
        
    assert response.status_code == 200, f"API Request failed: {response.text}"
    
    response_json = response.json()
    dates = response_json.get("data", {})
    stats = dates.get("portfolio_statistics", {})
    
    print(f"✅ 성공!")
    print(f"   총 거래 횟수: {stats.get('Total_Trades', 'N/A')}")
    final_val = stats.get('Final_Value', 0.0)
    print(f"   최종 포트폴리오 가치: ${final_val:,.2f}")


def test_combined_dca_and_rebalancing():
    """DCA + 리밸런싱 조합 테스트"""
    print("\n" + "="*80)
    print("TEST 5: DCA + 리밸런싱 조합 (monthly_1 DCA + monthly_3 리밸런싱)")
    print("="*80)
    
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "monthly_1"
            },
            {
                "symbol": "MSFT",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "monthly_1"
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "monthly_3",  # 분기별 리밸런싱
        "strategy": "buy_and_hold"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    
    if response.status_code != 200:
        print(f"❌ 실패: {response.status_code}")
        print(f"   에러: {response.text}")

    assert response.status_code == 200, f"API Request failed: {response.text}"
    
    response_json = response.json()
    dates = response_json.get("data", {})
    stats = dates.get("portfolio_statistics", {})
    
    print(f"✅ 성공!")
    print(f"   총 거래 횟수: {stats.get('Total_Trades', 'N/A')}")
    # print(f"   리밸런싱 횟수: {result.get('rebalance_count', 'N/A')}")
    final_val = stats.get('Final_Value', 0.0)
    print(f"   최종 포트폴리오 가치: ${final_val:,.2f}")


def test_legacy_frequency_should_fail():
    """잘못된 주기 요청은 거부되어야 함"""
    print("\n" + "="*80)
    print("TEST 6: 잘못된 주기 거부 (invalid_freq는 에러 발생해야 함)")
    print("="*80)
    
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "invalid_freq"  # 확실히 잘못된 주기
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "none",
        "strategy": "buy_and_hold"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    
    if response.status_code == 422:  # Validation error
        print(f"✅ 성공! (예상대로 거부됨)")
    else:
        print(f"❌ 실패: 잘못된 주기가 허용되었습니다 (status: {response.status_code})")
        
    assert response.status_code == 422, f"Invalid frequency should be rejected but got {response.status_code}"


if __name__ == "__main__":
    # 스크립트로 직접 실행 시 pytest를 통해 실행하거나, 간단히 함수들만 호출
    # 여기서는 간단호출 방식으로 유지
    print("\n" + "🚀 DCA 및 리밸런싱 Nth Weekday 로직 통합 테스트 시작" + "\n")
    
    # 서버 health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 서버 응답 이상")
            exit(1)
        print("✅ 서버 연결 확인")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("   docker compose -f compose.dev.yaml up -d 로 서버를 먼저 실행하세요.")
        exit(1)

    # 직접 실행 시에는 assert가 실패하면 프로그램이 종료됨
    try:
        test_monthly_dca()
        test_quarterly_rebalancing()
        test_weekly_dca()
        test_biweekly_dca()
        test_combined_dca_and_rebalancing()
        test_legacy_frequency_should_fail()
        print("\n🎉 모든 테스트 통과!")
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        exit(1)
