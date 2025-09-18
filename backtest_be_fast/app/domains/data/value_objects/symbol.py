"""
Data domain - Symbol value objects

주식 심볼과 관련된 값 객체들을 정의합니다.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AssetType(Enum):
    """자산 유형 열거형"""
    STOCK = "stock"
    CASH = "cash"
    ETF = "etf"
    INDEX = "index"


@dataclass(frozen=True)
class Symbol:
    """
    주식 심볼을 나타내는 값 객체
    
    특징:
    - 심볼 형식 검증 (영문 대문자, 1-5자)
    - 자산 유형 구분 (주식, 현금, ETF 등)
    - 정규화된 심볼 형태 보장
    """
    value: str
    asset_type: AssetType = AssetType.STOCK
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        if not self.value:
            raise ValueError("Symbol cannot be empty")
        
        # 현금 자산은 심볼 형식 검증 제외
        if self.asset_type == AssetType.CASH:
            return
        
        # 심볼 정규화 및 검증
        normalized = self.value.upper().strip()
        if not normalized.isalpha():
            raise ValueError(f"Symbol must contain only letters: {self.value}")
        
        if len(normalized) < 1 or len(normalized) > 10:
            raise ValueError(f"Symbol length must be 1-10 characters: {self.value}")
        
        # 정규화된 값으로 업데이트 (frozen 객체이므로 __dict__ 직접 수정)
        object.__setattr__(self, 'value', normalized)
    
    @classmethod
    def stock(cls, symbol: str) -> "Symbol":
        """주식 심볼 생성"""
        return cls(symbol, AssetType.STOCK)
    
    @classmethod
    def cash(cls, name: str = "CASH") -> "Symbol":
        """현금 자산 심볼 생성"""
        return cls(name, AssetType.CASH)
    
    @classmethod
    def etf(cls, symbol: str) -> "Symbol":
        """ETF 심볼 생성"""
        return cls(symbol, AssetType.ETF)
    
    def is_stock(self) -> bool:
        """주식 여부 확인"""
        return self.asset_type == AssetType.STOCK
    
    def is_cash(self) -> bool:
        """현금 자산 여부 확인"""
        return self.asset_type == AssetType.CASH
    
    def is_etf(self) -> bool:
        """ETF 여부 확인"""
        return self.asset_type == AssetType.ETF
    
    def requires_market_data(self) -> bool:
        """시장 데이터가 필요한 자산인지 확인"""
        return self.asset_type != AssetType.CASH
    
    def __str__(self) -> str:
        if self.asset_type == AssetType.CASH:
            return f"CASH({self.value})"
        return self.value
    
    def __hash__(self) -> int:
        return hash((self.value, self.asset_type))


@dataclass(frozen=True)
class MarketInfo:
    """
    시장 정보를 나타내는 값 객체
    
    특징:
    - 시장 코드와 이름 정보
    - 거래 시간대 정보
    - 시장별 특성 관리
    """
    code: str  # NYSE, NASDAQ, KRX 등
    name: str
    timezone: str = "America/New_York"
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        if not self.code or not self.code.strip():
            raise ValueError("Market code cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Market name cannot be empty")
        
        # 코드 정규화
        normalized_code = self.code.upper().strip()
        object.__setattr__(self, 'code', normalized_code)
    
    @classmethod
    def nyse(cls) -> "MarketInfo":
        """뉴욕 증권거래소"""
        return cls("NYSE", "New York Stock Exchange", "America/New_York")
    
    @classmethod
    def nasdaq(cls) -> "MarketInfo":
        """나스닥"""
        return cls("NASDAQ", "NASDAQ Stock Market", "America/New_York")
    
    @classmethod
    def krx(cls) -> "MarketInfo":
        """한국거래소"""
        return cls("KRX", "Korea Exchange", "Asia/Seoul")
    
    def is_us_market(self) -> bool:
        """미국 시장 여부 확인"""
        return self.code in ["NYSE", "NASDAQ"]
    
    def is_korean_market(self) -> bool:
        """한국 시장 여부 확인"""
        return self.code == "KRX"
    
    def __str__(self) -> str:
        return f"{self.code} ({self.name})"


@dataclass(frozen=True)
class TickerInfo:
    """
    티커 상세 정보를 나타내는 값 객체
    
    특징:
    - 심볼과 시장 정보 결합
    - 기업명 및 섹터 정보
    - 티커별 메타데이터 관리
    """
    symbol: Symbol
    market: MarketInfo
    company_name: Optional[str] = None
    sector: Optional[str] = None
    
    def __post_init__(self):
        """객체 생성 후 유효성 검사"""
        # 현금 자산은 시장 정보가 없어도 됨
        if self.symbol.is_cash() and self.market is None:
            return
        
        if not self.symbol.is_cash() and self.market is None:
            raise ValueError("Non-cash assets must have market information")
    
    @classmethod
    def us_stock(cls, symbol: str, company_name: Optional[str] = None, 
                 sector: Optional[str] = None) -> "TickerInfo":
        """미국 주식 티커 정보 생성"""
        return cls(
            Symbol.stock(symbol),
            MarketInfo.nasdaq(),  # 기본값으로 NASDAQ 사용
            company_name,
            sector
        )
    
    @classmethod
    def cash_asset(cls, name: str = "USD") -> "TickerInfo":
        """현금 자산 티커 정보 생성"""
        return cls(
            Symbol.cash(name),
            MarketInfo.nyse(),  # 기본 시장으로 NYSE 사용
            f"Cash ({name})",
            "Cash"
        )
    
    def get_display_name(self) -> str:
        """표시용 이름 반환"""
        if self.company_name:
            return f"{self.symbol} ({self.company_name})"
        return str(self.symbol)
    
    def is_tradeable(self) -> bool:
        """거래 가능한 자산인지 확인"""
        # 현금은 거래하지 않음 (리밸런싱 시에만 조정)
        return not self.symbol.is_cash()
    
    def __str__(self) -> str:
        return self.get_display_name()
    
    def __hash__(self) -> int:
        return hash((self.symbol, self.market.code))
