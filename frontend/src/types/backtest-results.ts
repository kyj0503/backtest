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
}

export interface ChartData {
  ticker?: string;
  strategy?: string;
  start_date?: string;
  end_date?: string;
  ohlc_data?: any[];
  equity_data?: any[];
  trade_markers?: any[];
  indicators?: any[];
  summary_stats?: any;
}

export interface PortfolioData {
  portfolio_statistics: PortfolioStatistics;
  individual_returns: Record<string, IndividualReturn>;
  portfolio_composition: Stock[];
  equity_curve: Record<string, number>;
  daily_returns: Record<string, number>;
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
