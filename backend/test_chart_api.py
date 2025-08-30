#!/usr/bin/env python3
"""
백테스트 차트 데이터 API 테스트 스크립트
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

# API 기본 설정
BASE_URL = "http://localhost:8001/api/v1"
HEADERS = {"Content-Type": "application/json"}

def test_chart_data_api():
    """차트 데이터 API 테스트"""
    print("🚀 백테스트 차트 데이터 API 테스트 시작...")
    
    # 테스트 파라미터
    test_params = {
        "ticker": "AAPL",
        "start_date": "2023-01-01", 
        "end_date": "2023-06-30",
        "initial_cash": 10000,
        "strategy": "sma_crossover",
        "strategy_params": {
            "short_window": 10,
            "long_window": 20
        },
        "commission": 0.002
    }
    
    print(f"📊 테스트 파라미터:")
    print(f"   - 티커: {test_params['ticker']}")
    print(f"   - 기간: {test_params['start_date']} ~ {test_params['end_date']}")
    print(f"   - 전략: {test_params['strategy']}")
    print(f"   - 초기자금: ${test_params['initial_cash']:,}")
    
    try:
        start_time = time.time()
        
        # API 호출
        response = requests.post(
            f"{BASE_URL}/backtest/chart-data",
            headers=HEADERS,
            json=test_params,
            timeout=60  # 60초 타임아웃
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  API 호출 시간: {execution_time:.2f}초")
        
        if response.status_code == 200:
            print("✅ API 호출 성공!")
            
            # 응답 데이터 분석
            data = response.json()
            analyze_chart_data(data)
            
            # 샘플 데이터 출력
            print_sample_data(data)
            
            return True
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"   오류 메시지: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API 호출 타임아웃 (60초 초과)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ API 서버 연결 실패")
        print("   서버가 실행 중인지 확인하세요: http://localhost:8001")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False

def analyze_chart_data(data):
    """차트 데이터 분석 및 출력"""
    print("\n📈 차트 데이터 분석:")
    
    # 기본 정보
    print(f"   🎯 티커: {data['ticker']}")
    print(f"   🔧 전략: {data['strategy']}")
    print(f"   📅 기간: {data['start_date']} ~ {data['end_date']}")
    
    # 데이터 크기
    ohlc_count = len(data['ohlc_data'])
    equity_count = len(data['equity_data'])
    trade_count = len(data['trade_markers'])
    indicator_count = len(data['indicators'])
    
    print(f"   📊 OHLC 데이터: {ohlc_count:,}개")
    print(f"   💰 자산 데이터: {equity_count:,}개")
    print(f"   🔄 거래 마커: {trade_count}개")
    print(f"   📉 기술 지표: {indicator_count}개")
    
    # 통계 요약
    stats = data['summary_stats']
    print(f"\n📊 성과 요약:")
    print(f"   💹 총 수익률: {stats['total_return_pct']:.2f}%")
    print(f"   🎯 총 거래 수: {stats['total_trades']}")
    print(f"   🏆 승률: {stats['win_rate_pct']:.1f}%")
    print(f"   📉 최대 손실: {stats['max_drawdown_pct']:.2f}%")
    print(f"   📈 샤프 비율: {stats['sharpe_ratio']:.3f}")
    print(f"   💪 수익 팩터: {stats['profit_factor']:.2f}")
    
    # 데이터 품질 검사
    print(f"\n🔍 데이터 품질 검사:")
    
    # OHLC 데이터 검사
    if ohlc_count > 0:
        first_ohlc = data['ohlc_data'][0]
        last_ohlc = data['ohlc_data'][-1]
        print(f"   📅 첫 데이터: {first_ohlc['date']} (종가: ${first_ohlc['close']:.2f})")
        print(f"   📅 마지막 데이터: {last_ohlc['date']} (종가: ${last_ohlc['close']:.2f})")
        
        # 가격 범위 검사
        prices = [item['close'] for item in data['ohlc_data']]
        min_price = min(prices)
        max_price = max(prices)
        print(f"   💰 가격 범위: ${min_price:.2f} ~ ${max_price:.2f}")
    
    # 거래 분석
    if trade_count > 0:
        entry_trades = [t for t in data['trade_markers'] if t['type'] == 'entry']
        exit_trades = [t for t in data['trade_markers'] if t['type'] == 'exit']
        print(f"   🟢 진입 거래: {len(entry_trades)}개")
        print(f"   🔴 청산 거래: {len(exit_trades)}개")
        
        # 수익성 거래 분석
        profitable_trades = [t for t in exit_trades if t.get('pnl_pct', 0) > 0]
        if exit_trades:
            win_rate = len(profitable_trades) / len(exit_trades) * 100
            print(f"   ✅ 실제 승률: {win_rate:.1f}%")
    
    # 지표 분석
    if indicator_count > 0:
        print(f"   📊 지표 목록:")
        for indicator in data['indicators']:
            indicator_data_count = len(indicator['data'])
            print(f"      - {indicator['name']}: {indicator_data_count}개 데이터 포인트 ({indicator['color']})")

def print_sample_data(data):
    """샘플 데이터 출력"""
    print(f"\n🔍 샘플 데이터:")
    
    # OHLC 샘플
    if data['ohlc_data']:
        print(f"   📊 OHLC 샘플 (첫 3개):")
        for i, item in enumerate(data['ohlc_data'][:3]):
            print(f"      {i+1}. {item['date']}: O${item['open']:.2f} H${item['high']:.2f} L${item['low']:.2f} C${item['close']:.2f} V{item['volume']:,}")
    
    # 자산 곡선 샘플
    if data['equity_data']:
        print(f"   💰 자산 곡선 샘플 (첫 3개):")
        for i, item in enumerate(data['equity_data'][:3]):
            print(f"      {i+1}. {item['date']}: 자산${item['equity']:.2f} 수익률{item['return_pct']:.2f}% 손실{item['drawdown_pct']:.2f}%")
    
    # 거래 마커 샘플
    if data['trade_markers']:
        print(f"   🔄 거래 마커 샘플 (첫 5개):")
        for i, trade in enumerate(data['trade_markers'][:5]):
            pnl_str = f" P&L:{trade['pnl_pct']:.2f}%" if trade.get('pnl_pct') is not None else ""
            print(f"      {i+1}. {trade['date']} {trade['type'].upper()} {trade['side'].upper()} ${trade['price']:.2f} x{trade['size']:.0f}{pnl_str}")

def test_api_errors():
    """API 오류 처리 테스트"""
    print(f"\n🧪 API 오류 처리 테스트:")
    
    # 잘못된 티커 테스트
    print(f"   1. 잘못된 티커 테스트...")
    invalid_params = {
        "ticker": "INVALID_TICKER_123",
        "start_date": "2023-01-01",
        "end_date": "2023-01-31",
        "initial_cash": 10000,
        "strategy": "sma_crossover"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/backtest/chart-data",
            headers=HEADERS,
            json=invalid_params,
            timeout=30
        )
        
        if response.status_code == 400 or response.status_code == 500:
            print(f"      ✅ 예상된 오류 응답: {response.status_code}")
        else:
            print(f"      ⚠️  예상과 다른 응답: {response.status_code}")
            
    except Exception as e:
        print(f"      ⚠️  오류 테스트 중 예외: {str(e)}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("🎯 백테스트 차트 데이터 API 테스트")
    print("=" * 60)
    
    # 서버 상태 확인
    try:
        health_response = requests.get(f"{BASE_URL}/backtest/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API 서버 상태: 정상")
        else:
            print(f"⚠️  API 서버 상태: 비정상 ({health_response.status_code})")
    except:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   서버를 먼저 실행하세요: python run_server.py")
        sys.exit(1)
    
    # 차트 데이터 API 테스트
    success = test_chart_data_api()
    
    # 오류 처리 테스트
    test_api_errors()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 모든 테스트 완료!")
        print("🚀 프론트엔드에서 다음 URL로 API를 호출할 수 있습니다:")
        print(f"   POST {BASE_URL}/backtest/chart-data")
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main() 