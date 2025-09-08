# 현금 자산 처리 가이드

## 개요

백테스팅 시스템에서 현금 자산은 무위험 자산으로 처리되며, 시간이 지나도 가치가 변하지 않습니다. 이는 실제 현금을 보유하는 것과 동일한 개념으로, 포트폴리오에서 리스크 완화 역할을 수행합니다.

## 기술적 구현

### 자산 타입 구분

```python
class PortfolioStock(BaseModel):
    symbol: str = Field(..., description="종목 심볼 또는 현금 식별자")
    weight: float = Field(..., description="포트폴리오 내 비중")
    asset_type: str = Field(default="stock", description="자산 타입: stock 또는 cash")
```

### 현금 자산 특징

1. **데이터 수집 없음**: yfinance API 호출하지 않음
2. **고정 수익률**: 0% 수익률 보장
3. **변동성 없음**: 일일 변동률 0%
4. **가치 유지**: 초기 투자 금액 그대로 유지

### 포트폴리오 계산 로직

```python
def _calculate_dca_portfolio(self, stocks_data: Dict, weights: List[float], 
                           asset_types: List[str], initial_cash: float) -> Dict:
    # 현금과 주식 부분 분리
    cash_weight = sum(w for w, at in zip(weights, asset_types) if at == 'cash')
    stock_weights = [w for w, at in zip(weights, asset_types) if at == 'stock']
    
    # 현금 부분은 초기값 그대로 유지
    cash_amount = initial_cash * cash_weight
    
    # 주식 부분만 백테스팅 수행
    # ...
```

## 사용 예시

### 현금만 있는 포트폴리오

```json
{
  "stocks": [
    {
      "symbol": "현금",
      "weight": 1.0,
      "asset_type": "cash"
    }
  ],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_cash": 10000
}
```

결과:
- 총 수익률: 0.0%
- 최종 금액: $10,000
- 일일 수익률: 모든 날짜에서 0.0%

### 혼합 포트폴리오 (현금 + 주식)

```json
{
  "stocks": [
    {
      "symbol": "현금",
      "weight": 0.5,
      "asset_type": "cash"
    },
    {
      "symbol": "AAPL",
      "weight": 0.5,
      "asset_type": "stock"
    }
  ],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_cash": 10000
}
```

결과:
- 현금 부분: $5,000 (변동 없음)
- 주식 부분: AAPL 성과에 따라 변동
- 전체 포트폴리오: 현금이 손실 완화 역할

## 프론트엔드 연동

### 현금 추가 버튼

사용자가 "현금 추가" 버튼을 클릭하면:

```javascript
const addCashAsset = () => {
  setSelectedStocks(prev => [...prev, {
    symbol: '현금',
    weight: 0,
    asset_type: 'cash'
  }]);
};
```

### API 요청 형태

```javascript
const portfolioRequest = {
  stocks: selectedStocks.map(stock => ({
    symbol: stock.asset_type === 'cash' ? '현금' : stock.symbol,
    weight: stock.weight / 100,
    asset_type: stock.asset_type || 'stock'
  })),
  // ...
};
```

## 테스트 케이스

현금 자산 처리 로직은 다음과 같이 테스트됩니다:

```python
def test_cash_only_portfolio():
    """현금만 있는 포트폴리오 테스트"""
    portfolio_request = {
        "stocks": [{"symbol": "현금", "weight": 1.0, "asset_type": "cash"}],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_cash": 10000
    }
    result = portfolio_service.run_portfolio_backtest(portfolio_request)
    
    assert result["total_return"] == 0.0
    assert result["final_value"] == 10000
    assert all(daily_return == 0.0 for daily_return in result["daily_returns"])
```

## 주의사항

1. **심볼명**: 현금 자산의 symbol은 "현금"으로 통일하여 사용자 혼동 방지
2. **가중치 합계**: 현금과 주식을 포함한 전체 가중치는 1.0이 되어야 함
3. **데이터 검증**: asset_type이 'cash'인 경우 별도 검증 로직 적용
4. **백테스트 엔진**: backtesting 라이브러리는 현금 부분 제외하고 주식 부분만 처리

## 향후 개선 방향

1. **이자율 적용**: 무위험 이자율(예: 국채 수익률) 적용 옵션
2. **인플레이션 조정**: 실질 구매력 기준 계산 옵션
3. **현금 관리**: 배당금 재투자 시 현금 풀 활용
4. **리밸런싱**: 정기적 리밸런싱 시 현금 버퍼 역할
