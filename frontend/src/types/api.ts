// API 타입 정의

// 포트폴리오 구성 요소
export interface PortfolioStock {
  symbol: string;
  amount: number;
  investment_type?: 'lump_sum' | 'dca';
  dca_periods?: number;
  asset_type?: 'stock' | 'cash';
}

// 통합 백테스트 요청
export interface UnifiedBacktestRequest {
  portfolio: PortfolioStock[];
  start_date: string;
  end_date: string;
  strategy: string;
  strategy_params?: Record<string, any>;
  commission?: number;
  rebalance_frequency?: string;
}

export interface ChartDataPoint {
  timestamp: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
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

export interface ChartDataResponse {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string;
  ohlc_data: ChartDataPoint[];
  equity_data: EquityPoint[];
  trade_markers: TradeMarker[];
  indicators: IndicatorData[];
  summary_stats: {
    total_return_pct: number;
    total_trades: number;
    win_rate_pct: number;
    max_drawdown_pct: number;
    sharpe_ratio: number;
    profit_factor: number;
  };
} 