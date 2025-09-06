"""
데이터 도메인 이벤트들
"""
from datetime import datetime, date
from typing import Dict, Any, Optional, List

from app.events import DomainEvent


class MarketDataUpdatedEvent(DomainEvent):
    """시장 데이터 업데이트 이벤트"""
    
    def __init__(self, symbol: str, data_source: str, data_points_count: int,
                 date_range_start: str, date_range_end: str,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.symbol = symbol
        self.data_source = data_source
        self.data_points_count = data_points_count
        self.date_range_start = date_range_start
        self.date_range_end = date_range_end
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'symbol': self.symbol,
            'data_source': self.data_source,
            'data_points_count': self.data_points_count,
            'date_range_start': self.date_range_start,
            'date_range_end': self.date_range_end
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketDataUpdatedEvent':
        return cls(
            symbol=data['symbol'],
            data_source=data['data_source'],
            data_points_count=data['data_points_count'],
            date_range_start=data['date_range_start'],
            date_range_end=data['date_range_end'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class DataQualityIssueDetectedEvent(DomainEvent):
    """데이터 품질 문제 감지 이벤트"""
    
    def __init__(self, symbol: str, issue_type: str, issue_description: str,
                 affected_date_range: Dict[str, str], severity: str,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.symbol = symbol
        self.issue_type = issue_type
        self.issue_description = issue_description
        self.affected_date_range = affected_date_range
        self.severity = severity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'symbol': self.symbol,
            'issue_type': self.issue_type,
            'issue_description': self.issue_description,
            'affected_date_range': self.affected_date_range,
            'severity': self.severity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataQualityIssueDetectedEvent':
        return cls(
            symbol=data['symbol'],
            issue_type=data['issue_type'],
            issue_description=data['issue_description'],
            affected_date_range=data['affected_date_range'],
            severity=data['severity'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class CorrelationAnalysisCompletedEvent(DomainEvent):
    """상관관계 분석 완료 이벤트"""
    
    def __init__(self, analysis_id: str, symbols: List[str], correlation_matrix: Dict[str, float],
                 analysis_period: Dict[str, str], significant_correlations: List[Dict[str, Any]],
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.analysis_id = analysis_id
        self.symbols = symbols
        self.correlation_matrix = correlation_matrix
        self.analysis_period = analysis_period
        self.significant_correlations = significant_correlations
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'analysis_id': self.analysis_id,
            'symbols': self.symbols,
            'correlation_matrix': self.correlation_matrix,
            'analysis_period': self.analysis_period,
            'significant_correlations': self.significant_correlations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrelationAnalysisCompletedEvent':
        return cls(
            analysis_id=data['analysis_id'],
            symbols=data['symbols'],
            correlation_matrix=data['correlation_matrix'],
            analysis_period=data['analysis_period'],
            significant_correlations=data['significant_correlations'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class DataCacheHitEvent(DomainEvent):
    """데이터 캐시 히트 이벤트"""
    
    def __init__(self, symbol: str, cache_type: str, date_range: Dict[str, str],
                 cache_age_seconds: float, data_points_retrieved: int,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.symbol = symbol
        self.cache_type = cache_type
        self.date_range = date_range
        self.cache_age_seconds = cache_age_seconds
        self.data_points_retrieved = data_points_retrieved
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'symbol': self.symbol,
            'cache_type': self.cache_type,
            'date_range': self.date_range,
            'cache_age_seconds': self.cache_age_seconds,
            'data_points_retrieved': self.data_points_retrieved
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataCacheHitEvent':
        return cls(
            symbol=data['symbol'],
            cache_type=data['cache_type'],
            date_range=data['date_range'],
            cache_age_seconds=data['cache_age_seconds'],
            data_points_retrieved=data['data_points_retrieved'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class DataCacheMissEvent(DomainEvent):
    """데이터 캐시 미스 이벤트"""
    
    def __init__(self, symbol: str, cache_type: str, date_range: Dict[str, str],
                 fallback_source: str, fetch_time_seconds: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.symbol = symbol
        self.cache_type = cache_type
        self.date_range = date_range
        self.fallback_source = fallback_source
        self.fetch_time_seconds = fetch_time_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'symbol': self.symbol,
            'cache_type': self.cache_type,
            'date_range': self.date_range,
            'fallback_source': self.fallback_source,
            'fetch_time_seconds': self.fetch_time_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataCacheMissEvent':
        return cls(
            symbol=data['symbol'],
            cache_type=data['cache_type'],
            date_range=data['date_range'],
            fallback_source=data['fallback_source'],
            fetch_time_seconds=data['fetch_time_seconds'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )


class OutlierDetectedEvent(DomainEvent):
    """이상치 감지 이벤트"""
    
    def __init__(self, symbol: str, outlier_date: str, outlier_value: float,
                 expected_range: Dict[str, float], outlier_type: str,
                 detection_method: str, confidence_score: float,
                 event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        super().__init__(event_id, occurred_at)
        self.symbol = symbol
        self.outlier_date = outlier_date
        self.outlier_value = outlier_value
        self.expected_range = expected_range
        self.outlier_type = outlier_type
        self.detection_method = detection_method
        self.confidence_score = confidence_score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'symbol': self.symbol,
            'outlier_date': self.outlier_date,
            'outlier_value': self.outlier_value,
            'expected_range': self.expected_range,
            'outlier_type': self.outlier_type,
            'detection_method': self.detection_method,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutlierDetectedEvent':
        return cls(
            symbol=data['symbol'],
            outlier_date=data['outlier_date'],
            outlier_value=data['outlier_value'],
            expected_range=data['expected_range'],
            outlier_type=data['outlier_type'],
            detection_method=data['detection_method'],
            confidence_score=data['confidence_score'],
            event_id=data['event_id'],
            occurred_at=datetime.fromisoformat(data['occurred_at'])
        )
