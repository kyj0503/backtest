// API 타입 정의 - 통합 및 확장

// 공통 응답 인터페이스
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 페이지네이션 응답
export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 에러 응답
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// 포트폴리오 구성 요소
export interface PortfolioStock {
  symbol: string;
  amount: number;
  investment_type?: 'lump_sum' | 'dca';
  dca_periods?: number;
  asset_type?: 'stock' | 'cash';
}

// 백테스트 요청 (단일/포트폴리오 통합)
export interface BacktestRequest {
  portfolio: PortfolioStock[];
  start_date: string;
  end_date: string;
  strategy: string;
  strategy_params?: Record<string, any>;
  commission?: number;
  rebalance_frequency?: string;
}

// 백테스트 결과 통계
export interface BacktestStats {
  total_return_pct: number;
  total_trades: number;
  win_rate_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  profit_factor: number;
  volatility_pct?: number;
  alpha?: number;
  beta?: number;
  calmar_ratio?: number;
  sortino_ratio?: number;
  var_95?: number;
  cvar_95?: number;
  // 벤치마크 관련 (선택적)
  benchmark_ticker?: string;
  benchmark_total_return_pct?: number;
  alpha_vs_benchmark_pct?: number;
}

// 포트폴리오 통계 (포트폴리오 백테스트용)
export interface PortfolioStats {
  total_return: number;
  annual_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  calmar_ratio: number;
  alpha: number;
  beta: number;
  var_95: number;
  cvar_95: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
}

// 차트 데이터 포인트
export interface ChartDataPoint {
  timestamp: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// 포트폴리오 차트 데이터 (필드명이 다름)
export interface PortfolioChartDataPoint {
  timestamp: string;
  date: string;
  price: number;
  cumulative_return: number;
  daily_return: number;
  volatility: number;
}

export interface EquityPoint {
  timestamp: string;
  date: string;
  equity: number;
  return_pct: number;
  drawdown_pct: number;
}

export interface TradeMarker {
  timestamp: string;
  date: string;
  price: number;
  type: 'entry' | 'exit';
  side: 'buy' | 'sell';
  size: number;
  pnl_pct?: number;
}

export interface IndicatorData {
  name: string;
  type: string;
  color: string;
  data: Array<{
    timestamp: string;
    date: string;
    value: number;
  }>;
}

// 단일 종목 백테스트 응답
export interface ChartDataResponse {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string;
  ohlc_data: ChartDataPoint[];
  equity_data: EquityPoint[];
  trade_markers: TradeMarker[];
  indicators: IndicatorData[];
  summary_stats: BacktestStats;
}

// 포트폴리오 백테스트 응답
export interface PortfolioBacktestResponse {
  portfolio_composition: Array<{
    symbol: string;
    weight: number;
    amount: number;
    asset_type: string;
  }>;
  chart_data: PortfolioChartDataPoint[];
  stats: PortfolioStats;
  start_date: string;
  end_date: string;
  strategy: string;
  sp500_benchmark?: Array<{ date: string; close: number; volume: number }>;
  nasdaq_benchmark?: Array<{ date: string; close: number; volume: number }>;
}

// 전략 관련 타입
export interface Strategy {
  name: string;
  description: string;
  parameters: StrategyParameter[];
  category: string;
}

export interface StrategyParameter {
  name: string;
  type: 'int' | 'float' | 'str' | 'bool' | 'select';
  default: any;
  description: string;
  min?: number;
  max?: number;
  options?: string[];
  required?: boolean;
}

// 뉴스 관련 타입
export interface NewsItem {
  title: string;
  link: string;
  description: string;
  pubDate: string;
  originallink?: string;
}

export interface NewsResponse {
  lastBuildDate: string;
  total: number;
  start: number;
  display: number;
  items: NewsItem[];
}

// 변동성 데이터 타입
export interface VolatilityData {
  symbol: string;
  period: string;
  volatility: number;
  price_change: number;
  volume_change: number;
  last_updated: string;
}

// 환율 데이터 타입
export interface ExchangeRateData {
  date: string;
  usd_krw: number;
  change_rate: number;
  trend: 'up' | 'down' | 'stable';
}

// 시스템 정보 타입
export interface SystemInfo {
  version: string;
  environment: string;
  last_updated: string;
  database_status: 'connected' | 'disconnected';
  api_status: 'healthy' | 'degraded' | 'down';
}

// HTTP 메서드 타입
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// 통합 백테스트 응답 (새로운 /execute 엔드포인트용)
export interface UnifiedBacktestResponse {
  status: 'success' | 'error';
  backtest_type: 'single_stock' | 'portfolio';
  data: ChartDataResponse | PortfolioBacktestResponse;
  message?: string;
}

// 통합 백테스트 결과 (프론트엔드 처리용)
export interface UnifiedBacktestResult extends Partial<ChartDataResponse>, Partial<PortfolioBacktestResponse> {
  backtest_type?: 'single_stock' | 'portfolio';
  api_version?: 'unified' | 'legacy';
}

// API 엔드포인트 타입
export type ApiEndpoint = 
  | '/api/v1/backtest'  // 통합 백테스트 엔드포인트
  | '/api/v1/strategies'
  | '/api/v1/naver-news/search'
  | '/api/v1/yfinance/exchange-rate'
  | '/api/v1/system/info'
  | '/api/v1/optimize/run'; 
