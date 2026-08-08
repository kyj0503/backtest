"""
포트폴리오 백테스트 관련 스키마

**검증 아키텍처 (P2-04, 배치5에서 통합)**:
과거에는 "타입/포맷은 여기서, 비즈니스 규칙은 app/validators/portfolio_validator.py의
PortfolioValidator에서"라는 2계층 설계를 문서에만 적어 두었지만, PortfolioValidator는
실제로는 어디에서도 import되지 않는 죽은 코드였다 (app/validators/__init__.py의
재export 외에는 참조가 전혀 없었음). 그 결과 rebalance_frequency 멤버십 검증,
미래 end_date 검증이 포트폴리오 경로에 전혀 존재하지 않았고, PortfolioStock.symbol의
field_validator는 asset_type보다 먼저 선언되어 있어 asset_type='cash'에 대한 심볼
우회 분기가 죽은 코드였다(정상적인 한글 현금 이름이 422로 거부됨). 배치5에서
PortfolioValidator는 삭제했고, 그 규칙들은 각 필드가 실제로 정의된 이 파일로
통합했다:
- 필드 하나만 보면 되는 규칙(형식, 범위, 멤버십)은 @field_validator.
- 다른 필드 값을 함께 봐야 하는 규칙(symbol 형식이 asset_type에 따라 달라짐)은
  선언 순서와 무관하게 실행되는 @model_validator(mode='after').
- "오늘 날짜"에 의존하지 않고 요청 자체의 구조만으로 판단 가능한 규칙은 전부
  여기(스키마)에 있다. 유일한 예외는 최소 백테스트 기간(30일) 검증인데, 이 스키마를
  직접 생성해 짧은 기간으로 내부 엔진(DCA/리밸런싱/시뮬레이션)만 단위테스트하는
  기존 테스트가 다수 있어(schema 레벨에 두면 전부 깨짐) app/api/v1/endpoints/
  backtest.py의 엔드포인트 레벨에 두었다 (자세한 이유는 그 파일 참고).

**역할**:
- 포트폴리오 백테스트 요청/응답 데이터 모델 정의
- 타입, 포맷, 필드 간 일관성, 날짜/주기 멤버십 검증
- Pydantic을 사용한 타입 안전성 제공
- FastAPI 자동 문서 생성

**주요 모델**:
1. PortfolioStock: 개별 종목 설정
   - symbol: 종목 심볼 (asset_type='cash'면 형식 제한 없음)
   - amount: 투자 금액 또는 비중
   - investment_type: lump_sum(일시불) / dca(분할매수)
   - asset_type: stock(주식) / cash(현금)

2. PortfolioBacktestRequest: 포트폴리오 백테스트 요청
   - assets: 포트폴리오 구성 종목 리스트
   - start_date, end_date: 백테스트 기간 (end_date는 미래 불가)
   - rebalance_frequency: 리밸런싱 주기 (FREQUENCY_MAP ∪ {'none'} 멤버십 강제)
   - commission: 거래 수수료

**검증 항목**:
- 날짜 형식: YYYY-MM-DD, end_date는 미래 불가, end_date > start_date
- 포트폴리오 크기: Field(min_length=1, max_length=settings.max_portfolio_items)
- 금액/비중: 양수, 95-105% 합계(비중 모드)
- 심볼 포맷: 영문자, 숫자, '.', '-' (현금 자산 제외)
- rebalance_frequency / dca_frequency: FREQUENCY_MAP(+'none') 멤버십
- 중복 종목 검증, DCA 주기 vs 백테스트 기간 검증

**의존성**:
- pydantic: 데이터 검증

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (요청 모델 + 최소 기간 검증)
- Backend: app/services/portfolio_service.py (데이터 사용)
- Frontend: src/features/backtest/model/backtest-types.ts (TypeScript 타입)
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np
import re

from ..core.config import settings
from .requests import StrategyType

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

    @model_validator(mode='after')
    def validate_symbol_format(self):
        """
        심볼 형식을 asset_type에 따라 검증한다 (P2-04).

        과거에는 이 검사가 @field_validator('symbol')이었는데, symbol 필드가
        asset_type보다 먼저 선언돼 있어 pydantic v2의 선언 순서 검증 규칙상
        info.data에 asset_type이 아직 채워지지 않은 상태로 실행됐다(항상 기본값
        'stock' 취급). model_validator(mode='after')는 모든 필드가 채워진 뒤
        실행되므로 선언 순서와 무관하게 self.asset_type을 안전하게 참조한다.

        Note: 티커 존재 여부 확인 등 상세한 검증은 이 계층에서 하지 않음
        """
        if self.asset_type == 'cash':
            # 현금 자산은 심볼 제한 없음 (한글 "예금", "현금" 등 커스텀 이름 허용)
            return self

        if self.symbol.upper() == 'CASH':
            # CASH는 asset_type이 명시적으로 'cash'가 아니어도 특별한 심볼로 허용
            self.symbol = self.symbol.upper()
            return self

        # 주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 허용
        # 예: AAPL (미국), 005930.KS (한국), 600519.SS (중국)
        if not re.match(r'^[A-Za-z0-9.\-]+$', self.symbol):
            raise ValueError('주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.')
        self.symbol = self.symbol.upper()
        return self

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
    strategy: str = Field("buy_hold_strategy", description="전략명")
    strategy_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="전략 파라미터")
    
    @field_validator('portfolio')
    @classmethod
    def validate_portfolio(cls, v):
        """
        포트폴리오 구성 검증: 중복 종목(현금 제외), amount/weight 혼합 입력,
        비중 합계(95-105%) 또는 총 투자금액(>0)을 검증한다. 종목 수 제한은
        Field(min_length, max_length)로 처리됨.
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
    
    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        """
        전략명 검증 (FastAPI 조기 검증용)

        Note: StrategyType Enum에 정의되지 않은 값은 거부함 (P2-03)
        """
        valid_strategies = {s.value for s in StrategyType}
        if v not in valid_strategies:
            raise ValueError(f'유효하지 않은 전략입니다: {v}. 허용된 값: {", ".join(sorted(valid_strategies))}')
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
        날짜 순서 + 미래 날짜 검증 (P2-04)

        Note: 최소 백테스트 기간(30일) 검증은 이 스키마가 아니라
        app/api/v1/endpoints/backtest.py의 엔드포인트 레벨에서 수행됨 (이유는
        이 파일 상단 모듈 docstring 참고).
        """
        end = datetime.strptime(v, '%Y-%m-%d')

        # 미래 날짜 방지: 과거에는 검증이 전혀 없어 임의의 미래 end_date가
        # 그대로 통과했다 (P2-04).
        today = datetime.now().date()
        if end.date() > today:
            raise ValueError(f'종료 날짜는 미래일 수 없습니다: {v} (오늘: {today.isoformat()})')

        if 'start_date' in info.data:
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            # end == start(0일짜리 기간)도 거부한다. 기존에는 `end < start`만
            # 검사해 0일짜리 기간이 통과했는데, 에러 메시지("종료 날짜는 시작
            # 날짜보다 이후여야 합니다")의 의미상 이미 거부됐어야 하는
            # off-by-one이었다.
            if end <= start:
                raise ValueError('종료 날짜는 시작 날짜보다 이후여야 합니다.')
            if (end - start).days > 365 * settings.max_backtest_duration_years:
                raise ValueError(f'백테스트 기간은 최대 {settings.max_backtest_duration_years}년으로 제한됩니다.')
        return v

    @field_validator('rebalance_frequency')
    @classmethod
    def validate_rebalance_frequency(cls, v):
        """
        리밸런싱 주기 멤버십 검증 (P2-04)

        Note: 과거에는 자유 문자열(str)이라 오타/잘못된 값이 검증 없이 통과했다.
        그 값은 app/services/rebalance_helper.py::RebalanceHelper.is_rebalance_date()의
        FREQUENCY_MAP.get(frequency)에서 조용히 None이 되어 logger.warning()만
        남기고 리밸런싱을 경고 없이 비활성화시켰다 -- 사용자는 리밸런싱이 켜져
        있다고 믿지만 실제로는 한 번도 실행되지 않는다. 여기서 막아 422로 즉시
        드러나게 한다.
        """
        valid_values = set(FREQUENCY_MAP.keys()) | {'none'}
        if v not in valid_values:
            raise ValueError(
                f'유효하지 않은 리밸런싱 주기입니다: {v}. '
                f'허용된 값: {", ".join(sorted(valid_values))}'
            )
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

 
