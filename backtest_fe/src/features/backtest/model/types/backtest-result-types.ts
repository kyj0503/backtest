// 백테스트 결과 관련 타입 정의

export interface Stock {
  symbol: string;
  weight: number;
}

export interface IndividualReturn {
  weight: number;
  return: number;
  start_price: number;
  end_price: number;
}

export interface OhlcPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  [key: string]: unknown;
}

export interface EquityPoint {
  date: string;
  value?: number;
  return_pct: number;
  drawdown_pct: number;
  [key: string]: unknown;
}

export interface TradeMarker {
  date: string;
  type: 'entry' | 'exit';
  price?: number;
  quantity?: number;
  side?: 'buy' | 'sell';
  pnl_pct?: number;
}

export type IndicatorPoint = Record<string, unknown>;

export interface ExchangeRatePoint {
  date: string;
  rate: number;
}

export interface BenchmarkPoint {
  date: string;
  close: number;
  volume?: number;
}

export interface PortfolioStatistics {
  Start: string;
  End: string;
  Duration: string;
  Initial_Value: number;
  Final_Value: number;
  Peak_Value: number;
  Total_Return: number;
  Annual_Return: number;
  Annual_Volatility: number;
  Sharpe_Ratio: number;
  Max_Drawdown: number;
  Avg_Drawdown: number;
  Max_Consecutive_Gains: number;
  Max_Consecutive_Losses: number;
  Total_Trading_Days: number;
  Positive_Days: number;
  Negative_Days: number;
  Win_Rate: number;
  Profit_Factor: number;
}

export interface ChartData {
  ticker?: string;
  strategy?: string;
  start_date?: string;
  end_date?: string;
  ohlc_data?: OhlcPoint[];
  equity_data?: EquityPoint[];
  trade_markers?: TradeMarker[];
  indicators?: IndicatorPoint[];
  summary_stats?: Record<string, unknown>;
  exchange_rates?: ExchangeRatePoint[];
  sp500_benchmark?: BenchmarkPoint[];
  nasdaq_benchmark?: BenchmarkPoint[];
}

export interface VolatilityEvent {
  date: string;
  daily_return: number;
  close_price: number;
  volume: number;
  event_type: '급등' | '급락';
}

export interface NewsItem {
  title: string;
  link: string;
  description: string;
  pubDate: string;
  originallink?: string;
}

export interface RebalanceTrade {
  symbol: string;
  action: 'buy' | 'sell' | 'increase' | 'decrease';
  shares: number;
  price: number;
  amount?: number; // 현금 거래 시 사용
}

export interface RebalanceEvent {
  date: string;
  trades: RebalanceTrade[];
  weights_before: Record<string, number>;
  weights_after: Record<string, number>;
  commission_cost?: number;
}

export interface WeightHistoryPoint {
  date: string;
  [symbol: string]: number | string; // symbol별 비중 + date
}

export interface TickerInfo {
  symbol: string;
  currency: string;
  company_name: string;
  exchange: string;
}

export interface TradeLog {
  EntryTime: string;
  ExitTime?: string;
  EntryPrice: number;
  ExitPrice?: number;
  Size: number;
  PnL?: number;
  ReturnPct?: number;
  Duration?: string;
}

export interface StrategyStats {
  trade_log?: TradeLog[];
  total_trades?: number;
  win_rate_pct?: number;
  profit_factor?: number;
  sharpe_ratio?: number;
  max_drawdown_pct?: number;
  final_equity?: number;
  [key: string]: any;
}

export interface PortfolioData {
  portfolio_statistics: PortfolioStatistics;
  individual_returns: Record<string, IndividualReturn>;
  portfolio_composition: Stock[];
  equity_curve: Record<string, number>;
  daily_returns: Record<string, number>;

  // 리밸런싱 데이터
  rebalance_history?: RebalanceEvent[];
  weight_history?: WeightHistoryPoint[];

  // 전략 상세 정보 (개별 종목의 거래 내역 포함)
  strategy_details?: Record<string, StrategyStats>;

  // 통합 응답 데이터 (별도 API 호출 불필요)
  ticker_info?: Record<string, TickerInfo>;
  stock_data?: Record<string, Array<{ date: string; price: number; volume: number }>>;
  exchange_rates?: ExchangeRatePoint[];
  volatility_events?: Record<string, VolatilityEvent[]>;
  latest_news?: Record<string, NewsItem[]>;
  sp500_benchmark?: BenchmarkPoint[];
  nasdaq_benchmark?: BenchmarkPoint[];
  
  // 경고 메시지 (상장일 등)
  warnings?: string[];
}

export interface BacktestResultsProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

export interface StockDataItem {
  symbol: string;
  data: Array<{
    date: string;
    price: number;
    volume?: number;
  }>;
}

export interface EquityChartDataItem {
  date: string;
  value: number;
  return: number;
}
