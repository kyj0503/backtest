"""
포트폴리오 백테스트 관련 스키마

**Phase 2.3 리팩터링 변경사항**:
- Pydantic schemas는 타입 검증과 파싱만 담당
- 비즈니스 로직 검증은 app/validators/portfolio_validator.py로 이동
- Field 제약조건(gt, ge, le 등)은 FastAPI 문서 생성을 위해 유지
- field_validator는 타입 변환과 기본 포맷 검증만 수행
- 복잡한 비즈니스 규칙은 PortfolioValidator에서 처리

**역할**:
- 포트폴리오 백테스트 요청/응답 데이터 모델 정의
- 기본적인 타입 및 포맷 검증
- Pydantic을 사용한 타입 안전성 제공
- FastAPI 자동 문서 생성

**주요 모델**:
1. PortfolioStock: 개별 종목 설정
   - symbol: 종목 심볼
   - amount: 투자 금액 또는 비중
   - investment_type: lump_sum(일시불) / dca(분할매수)
   - asset_type: stock(주식) / cash(현금)

2. PortfolioBacktestRequest: 포트폴리오 백테스트 요청
   - assets: 포트폴리오 구성 종목 리스트
   - start_date, end_date: 백테스트 기간
   - rebalance_frequency: 리밸런싱 주기
   - commission: 거래 수수료

**기본 검증 (Pydantic)**:
- 날짜 형식: YYYY-MM-DD
- 포트폴리오 크기: 1~10개
- 금액/비중: 양수
- 심볼 포맷: 영문자, 숫자, '.', '-'

**비즈니스 로직 검증 (PortfolioValidator)**:
- 티커 존재 여부 확인
- 날짜 범위 유효성 (최소 30일)
- 미래 날짜 방지
- 비중 합계 검증 (95-105%)
- 중복 종목 검증
- DCA/리밸런싱 주기 유효성

**의존성**:
- pydantic: 데이터 검증

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (요청 모델)
- Backend: app/validators/portfolio_validator.py (비즈니스 로직 검증)
- Backend: app/services/portfolio_service.py (데이터 사용)
- Frontend: src/features/backtest/model/backtest-types.ts (TypeScript 타입)
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np
import re

from ..core.config import settings

# DCA/리밸런싱 주기 프리셋 (Nth Weekday 방식)
# 값: (주기 타입, 간격) - 예: ('weekly', 1) = 매주, ('monthly', 1) = 매월
FREQUENCY_MAP = {
    'weekly_1': ('weekly', 1),      # 1주마다
    'weekly_2': ('weekly', 2),      # 2주마다
    'monthly_1': ('monthly', 1),    # 1개월마다 (Nth Weekday)
    'monthly_2': ('monthly', 2),    # 2개월마다
    'monthly_3': ('monthly', 3),    # 3개월마다 (분기)
    'monthly_6': ('monthly', 6),    # 6개월마다 (반년)
    'monthly_12': ('monthly', 12),  # 12개월마다 (1년)
}

class PortfolioStock(BaseModel):
    """포트폴리오 종목 모델"""
    symbol: str = Field(..., min_length=1, max_length=settings.max_symbol_length, description="주식 심볼")
    amount: Optional[float] = Field(None, gt=0, description="투자 금액 (> 0, weight와 동시 입력 불가)")
    weight: Optional[float] = Field(None, ge=0, le=100, description="비중(%) (0~100, amount와 동시 입력 불가, 소수점 허용)")
    investment_type: Optional[str] = Field("lump_sum", description="투자 방식 (lump_sum, dca)")
    dca_frequency: Optional[str] = Field("monthly_1", description="DCA 주기 (weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12)")
    asset_type: Optional[str] = Field("stock", description="자산 타입 (stock, cash)")
    custom_name: Optional[str] = Field(None, description="현금 자산의 커스텀 이름")
    @field_validator('amount', 'weight')
    @classmethod
    def validate_amount_weight_exclusive(cls, v, info):
        """
        기본 상호 배타성 검증 (FastAPI 조기 검증용)

        Note: 이 필드는 타입 및 기본 제약만 검증함
        """
        # amount와 weight는 동시에 입력 불가
        data = info.data
        amount = data.get('amount')
        weight = data.get('weight')
        if amount is not None and weight is not None:
            raise ValueError('amount와 weight는 동시에 입력할 수 없습니다. 하나만 입력하세요.')
        return v
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v, info):
        """
        기본 심볼 포맷 검증 (FastAPI 조기 검증용)

        Note: 티커 존재 여부 확인 등 상세한 검증은 SymbolValidator에서 수행됨
        """
        # asset_type이 'cash'인 경우 더 유연한 검증
        asset_type = info.data.get('asset_type', 'stock')
        if asset_type == 'cash':
            # 현금 자산은 심볼 제한 없음 (한글 "현금" 등 허용)
            return v

        # CASH는 특별한 심볼로 허용
        if v.upper() == 'CASH':
            return v.upper()

        # 주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 허용
        # 예: AAPL (미국), 005930.KS (한국), 600519.SS (중국)
        if not re.match(r'^[A-Za-z0-9.\-]+$', v):
            raise ValueError('주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.')
        return v.upper()
    
    @field_validator('investment_type')
    @classmethod
    def validate_investment_type(cls, v):
        if v not in ['lump_sum', 'dca']:
            raise ValueError('투자 방식은 lump_sum 또는 dca만 가능합니다.')
        return v
    
    @field_validator('asset_type')
    @classmethod
    def validate_asset_type(cls, v):
        if v not in ['stock', 'cash']:
            raise ValueError('자산 타입은 stock 또는 cash만 가능합니다.')
        return v
    
    @field_validator('dca_frequency')
    @classmethod
    def validate_dca_frequency(cls, v):
        if v not in FREQUENCY_MAP:
            raise ValueError(f'DCA 주기는 {", ".join(FREQUENCY_MAP.keys())} 중 하나여야 합니다.')
        return v

class PortfolioBacktestRequest(BaseModel):
    """포트폴리오 백테스트 요청 모델"""
    portfolio: List[PortfolioStock] = Field(..., min_length=1, max_length=settings.max_portfolio_items, description="포트폴리오 구성")
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")
    commission: float = Field(0.002, ge=0, lt=0.1, description="수수료율 (0 ~ 0.1)")
    rebalance_frequency: str = Field("monthly_1", description="리밸런싱 주기 (weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12, none)")
    strategy: str = Field("buy_and_hold", description="전략명")
    strategy_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="전략 파라미터")
    
    @field_validator('portfolio')
    @classmethod
    def validate_portfolio(cls, v):
        """
        기본 포트폴리오 구성 검증 (FastAPI 조기 검증용)

        Note: 상세한 비즈니스 로직 검증(종목 수 제한, 비중 범위 등)은
        PortfolioValidator에서 수행됨
        """
        if not v:
            raise ValueError('포트폴리오는 최소 1개 종목을 포함해야 합니다.')

        # 중복 종목 검증 (현금 제외)
        stock_symbols = [item.symbol.upper() for item in v if item.asset_type != 'cash']
        if len(stock_symbols) != len(set(stock_symbols)):
            # 중복된 종목 찾기
            seen = set()
            duplicates = set()
            for symbol in stock_symbols:
                if symbol in seen:
                    duplicates.add(symbol)
                seen.add(symbol)
            raise ValueError(f'중복된 종목이 있습니다: {", ".join(sorted(duplicates))}. 같은 종목은 한 번만 추가할 수 있습니다.')

        # amount/weight 혼합 입력 불가, 모두 amount만 입력 or 모두 weight만 입력 or 일부만 weight면 amount 자동 환산
        has_amount = any(item.amount is not None for item in v)
        has_weight = any(item.weight is not None for item in v)
        if has_amount and has_weight:
            raise ValueError('포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다. 혼합 입력 불가.')

        if has_weight:
            total_weight = sum(item.weight or 0 for item in v)
            # 비중 합계 검증: 100% ± 5% 범위 허용 (프론트엔드와 동일)
            # 반올림 오차 및 DCA 계산 오차를 고려하여 95~105% 범위 허용
            if total_weight < 95 or total_weight > 105:  # ±5% 범위 벗어나면 오류
                raise ValueError(f'종목 비중 합계가 95-105% 범위를 벗어났습니다. 현재: {total_weight:.1f}%')
        else:
            total_amount = sum(item.amount or 0 for item in v)
            if total_amount <= 0:
                raise ValueError('총 투자 금액은 0보다 커야 합니다.')
        return v
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """
        날짜 포맷 검증 (타입 변환)

        Note: 이 필드는 날짜 형식만 검증함
        """
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다.')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """
        기본 날짜 순서 검증 (FastAPI 조기 검증용)

        Note: 상세한 비즈니스 로직 검증(기간 제한, 미래 날짜 등)은
        DateValidator에서 수행됨
        """
        if 'start_date' in info.data:
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError('종료 날짜는 시작 날짜보다 이후여야 합니다.')
            if (end - start).days > 365 * settings.max_backtest_duration_years:
                raise ValueError(f'백테스트 기간은 최대 {settings.max_backtest_duration_years}년으로 제한됩니다.')
        return v
    
    @model_validator(mode='after')
    def validate_dca_frequency_against_backtest_period(self):
        """DCA 주기가 백테스트 기간보다 짧거나 같은지 검증"""
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')
        backtest_days = (end - start).days

        for idx, item in enumerate(self.portfolio):
            if item.investment_type == 'dca' and item.dca_frequency:
                # 주기 정보 가져오기
                period_info = FREQUENCY_MAP.get(item.dca_frequency)
                if not period_info:
                    continue
                
                period_type, interval = period_info
                
                # 최소 필요 일수 계산
                if period_type == 'weekly':
                    required_days = interval * 7
                    period_label = f"{interval}주마다"
                elif period_type == 'monthly':
                    required_days = interval * 30  # 근사값 (실제는 Nth Weekday로 계산)
                    period_label = f"{interval}개월마다"
                else:
                    continue
                
                # DCA 주기가 백테스트 기간보다 길면 에러
                if required_days > backtest_days:
                    frequency_labels = {
                        'weekly_1': '매주',
                        'weekly_2': '2주마다',
                        'monthly_1': '매월',
                        'monthly_2': '2개월마다',
                        'monthly_3': '3개월마다 (분기)',
                        'monthly_6': '6개월마다 (반년)',
                        'monthly_12': '12개월마다 (1년)',
                    }
                    frequency_label = frequency_labels.get(item.dca_frequency, period_label)
                    raise ValueError(
                        f'{idx + 1}번째 종목({item.symbol}): DCA 주기가 "{frequency_label} 투자"({required_days}일 기준)인데, '
                        f'백테스트 기간이 {backtest_days}일밖에 안됩니다. '
                        f'DCA 주기는 백테스트 기간보다 짧아야 합니다.'
                    )
        return self

 
