/**
 * 타입 정의 통합 export
 * 모든 타입 정의를 한 곳에서 import할 수 있도록 통합
 *
 * Note: 중복 방지를 위해 각 모듈에서 특정 타입만 선택적으로 export
 */

// API 관련 타입 (중복 제외)
export type {
  StrategyParamValue,
  ApiResponse,
  PaginatedResponse,
  ApiError,
  PortfolioStock,
  BacktestRequest,
  BacktestStats,
  PortfolioStats,
  ChartDataPoint,
  PortfolioChartDataPoint,
  IndicatorData,
  ChartDataResponse,
  PortfolioBacktestResponse,
  Strategy,
  StrategyParameter,
  NewsResponse,
  VolatilityData,
  ExchangeRateData,
  SystemInfo,
  HttpMethod,
  UnifiedBacktestResponse,
  UnifiedBacktestResult,
  ApiEndpoint
} from './api-types';

// 폼 관련 타입
export type {
  Stock,
  PortfolioInputMode,
  BacktestFormState,
  BacktestFormAction
} from './backtest-form-types';

export { initialBacktestFormState } from './backtest-form-types';

// 결과 관련 타입 (우선순위 타입들 - EquityPoint, TradeMarker, NewsItem 등)
export type {
  IndividualReturn,
  OhlcPoint,
  EquityPoint,
  TradeMarker,
  IndicatorPoint,
  ExchangeRatePoint,
  BenchmarkPoint,
  PortfolioStatistics,
  ChartData,
  NewsItem,
  RebalanceTrade,
  RebalanceEvent,
  WeightHistoryPoint,
  TickerInfo,
  TradeLog,
  StrategyStats,
  PortfolioData,
  BacktestResultsProps,
  StockDataItem,
  EquityChartDataItem
} from './backtest-result-types';

// 급등락 관련 타입
export type {
  VolatilityEvent,
  StockVolatilityNewsProps
} from './volatility-news-types';

export { TICKER_TO_COMPANY_NAME, getCompanyName } from './volatility-news-types';
