#!/usr/bin/env python3
"""성능 벤치마크 스크립트

SQL 최적화의 실제 성능 개선 효과를 측정합니다:
1. 포트폴리오 데이터 로딩: 순차 vs 병렬 (asyncio.gather)
2. 티커 정보 조회: 개별 조회 vs 배치 조회

사용법:
    python scripts/benchmark_performance.py
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.repositories.stock_repository import get_stock_repository

# 테스트용 종목 (18개)
TEST_SYMBOLS_18 = [
    'GOOGL', 'V', 'AMD', 'JPM', 'NFLX', 'DIS', 'JNJ', 'AAPL', 'META', 
    'MSFT', 'PG', 'CSCO', 'AMZN', 'INTC', 'BAC', 'NVDA', 'TSLA', 'WMT'
]

# ... (BenchmarkTimer class and benchmark functions remain the same) ...

async def run_benchmarks():
    """모든 벤치마크 실행"""
    print("\n" + "🚀 " * 20)
    print("          성능 벤치마크 테스트 시작")
    print("🚀 " * 20)
    
    # 테스트 기간 설정 (2020-2024, 5년)
    start_date = '2020-01-01'
    end_date = '2024-12-31'
    
    print(f"\n테스트 기간: {start_date} ~ {end_date}")
    
    # =========================================================================
    # 1. 포트폴리오 데이터 로딩 벤치마크
    # =========================================================================
    print_section_header("1. 포트폴리오 데이터 로딩 벤치마크")
    
    symbols = TEST_SYMBOLS_18
    label = "18개 종목 (5년치 데이터)"
    
    print(f"\n📊 {label} 테스트:")
    
    # 순차 로딩
    seq_time, seq_success = await benchmark_portfolio_loading_sequential(
        symbols, start_date, end_date
    )
    print_benchmark_result(
        f"순차 로딩 - {label}",
        len(symbols),
        seq_time,
        seq_success
    )
    
    # 병렬 로딩
    par_time, par_success = await benchmark_portfolio_loading_parallel(
        symbols, start_date, end_date
    )
    print_benchmark_result(
        f"병렬 로딩 - {label}",
        len(symbols),
        par_time,
        par_success,
        baseline_elapsed=seq_time
    )
    
    # =========================================================================
    # 2. 티커 정보 조회 벤치마크
    # =========================================================================
    print_section_header("2. 티커 정보 조회 벤치마크")
    
    tickers = TEST_SYMBOLS_18
    label = "18개 종목"
    
    print(f"\n📊 {label} 테스트:")
    
    # 개별 조회
    ind_time, ind_success = benchmark_ticker_info_individual(tickers)
    print_benchmark_result(
        f"개별 조회 - {label}",
        len(tickers),
        ind_time,
        ind_success
    )
    
    # 배치 조회
    batch_time, batch_success = benchmark_ticker_info_batch(tickers)
    print_benchmark_result(
        f"배치 조회 - {label}",
        len(tickers),
        batch_time,
        batch_success,
        baseline_elapsed=ind_time
    )
    
    # =========================================================================
    # 종료
    # =========================================================================
    print("\n" + "✅ " * 20)
    print("          벤치마크 테스트 완료")
    print("✅ " * 20 + "\n")

class BenchmarkTimer:
    """성능 측정 타이머"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def elapsed(self) -> float:
        """경과 시간 (초)"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

async def benchmark_portfolio_loading_sequential(
    symbols: List[str],
    start_date: str,
    end_date: str
) -> Tuple[float, int]:
    """포트폴리오 데이터 순차 로딩 벤치마크
    
    Returns:
        (총 실행 시간, 성공한 종목 수)
    """
    stock_repository = get_stock_repository()
    
    with BenchmarkTimer("포트폴리오 순차 로딩") as timer:
        success_count = 0
        for symbol in symbols:
            try:
                result = await asyncio.to_thread(
                    stock_repository.load_stock_data,
                    symbol,
                    start_date,
                    end_date
                )
                if result is not None and not result.empty:
                    success_count += 1
                    # 데이터 검증 로그
                    first_date = result.index[0].strftime('%Y-%m-%d') if hasattr(result.index, 'strftime') else str(result.index[0])
                    last_date = result.index[-1].strftime('%Y-%m-%d') if hasattr(result.index, 'strftime') else str(result.index[-1])
                    print(f"  ✅ {symbol}: {len(result)}행 ({first_date} ~ {last_date})")
                else:
                    print(f"  ⚠️  {symbol}: 데이터 없음")
            except Exception as e:
                print(f"  ⚠️  {symbol} 로드 실패: {e}")
    
    return timer.elapsed, success_count

async def benchmark_portfolio_loading_parallel(
    symbols: List[str],
    start_date: str,
    end_date: str
) -> Tuple[float, int]:
    """포트폴리오 데이터 병렬 로딩 벤치마크 (현재 최적화)
    
    Returns:
        (총 실행 시간, 성공한 종목 수)
    """
    stock_repository = get_stock_repository()
    
    with BenchmarkTimer("포트폴리오 병렬 로딩") as timer:
        # 병렬 로드 태스크 생성
        load_tasks = [
            asyncio.to_thread(stock_repository.load_stock_data, symbol, start_date, end_date)
            for symbol in symbols
        ]
        
        # 병렬 실행
        results = await asyncio.gather(*load_tasks, return_exceptions=True)
        
        # 성공 카운트 및 검증
        success_count = 0
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                print(f"  ⚠️  {symbol} 병렬 로드 실패: {result}")
            elif result is not None and not result.empty:
                success_count += 1
                # 병렬 로딩은 로그가 섞일 수 있으므로 요약해서 출력하거나 필요시 주석 해제
                # first_date = result.index[0].strftime('%Y-%m-%d')
                # last_date = result.index[-1].strftime('%Y-%m-%d')
                # print(f"  ✅ {symbol}: {len(result)}행") 
            else:
                print(f"  ⚠️  {symbol}: 데이터 없음")
                
    return timer.elapsed, success_count

def benchmark_ticker_info_individual(tickers: List[str]) -> Tuple[float, int]:
    """티커 정보 개별 조회 벤치마크
    
    Returns:
        (총 실행 시간, 성공한 조회 수)
    """
    stock_repository = get_stock_repository()
    
    with BenchmarkTimer("티커 정보 개별 조회") as timer:
        success_count = 0
        sample_printed = False
        for ticker in tickers:
            try:
                result = stock_repository.get_ticker_info(ticker)
                if result:
                    success_count += 1
                    if not sample_printed:
                        print(f"  ✅ [검증] 개별 조회 샘플 ({ticker}): {result}")
                        sample_printed = True
            except Exception as e:
                print(f"  ⚠️  {ticker} 정보 조회 실패: {e}")
    
    return timer.elapsed, success_count

def benchmark_ticker_info_batch(tickers: List[str]) -> Tuple[float, int]:
    """티커 정보 배치 조회 벤치마크 (현재 최적화)
    
    Returns:
        (총 실행 시간, 성공한 조회 수)
    """
    stock_repository = get_stock_repository()
    
    with BenchmarkTimer("티커 정보 배치 조회") as timer:
        result = stock_repository.get_tickers_info_batch(tickers)
        success_count = len(result)
        
        # 검증용 샘플 출력 (첫 2개)
        if result:
            print(f"  ✅ [검증] 배치 조회 결과 수: {len(result)}개")
            for i, (ticker, info) in enumerate(result.items()):
                if i < 2:
                    print(f"  ✅ [검증] 배치 조회 샘플 ({ticker}): {info}")
                else:
                    break
    
    return timer.elapsed, success_count

def print_section_header(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_benchmark_result(
    test_name: str,
    item_count: int,
    elapsed: float,
    success_count: int,
    baseline_elapsed: float = None
):
    """벤치마크 결과 출력"""
    avg_time = elapsed / item_count if item_count > 0 else 0
    
    result_parts = [
        f"[{test_name}]",
        f"{elapsed:.2f}초",
        f"(항목당 {avg_time:.3f}초,",
        f"성공 {success_count}/{item_count}개)"
    ]
    
    if baseline_elapsed:
        speedup = baseline_elapsed / elapsed if elapsed > 0 else 0
        result_parts.append(f"→ {speedup:.1f}배 빠름")
    
    print("  " + " ".join(result_parts))

if __name__ == "__main__":
    print("성능 벤치마크 스크립트 실행 중...")
    print("데이터베이스 연결 및 데이터 로딩 준비 중...\n")
    
    try:
        asyncio.run(run_benchmarks())
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
