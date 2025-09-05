import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import OHLCChart from '../OHLCChart';
import EquityChart from '../EquityChart';
import TradesChart from '../TradesChart';
import StatsSummary from '../StatsSummary';
import StockPriceChart from '../StockPriceChart';
import { formatPercent } from '../../utils/formatters';
import { backtestApiService } from '../../services/api';
import { 
  ChartData, 
  PortfolioData, 
  StockDataItem, 
  EquityChartDataItem 
} from '../../types/backtest-results';

interface ChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ChartsSection: React.FC<ChartsSectionProps> = ({ data, isPortfolio }) => {
  const [stocksData, setStocksData] = useState<StockDataItem[]>([]);
  const [loadingStockData, setLoadingStockData] = useState(false);

  // 화폐 포맷터 함수
  const formatCurrency = (value: number): string => {
    if (value >= 1e9) {
      return `${(value / 1e9).toFixed(1)}B`;
    } else if (value >= 1e6) {
      return `${(value / 1e6).toFixed(1)}M`;
    } else if (value >= 1e3) {
      return `${(value / 1e3).toFixed(1)}K`;
    }
    return value.toLocaleString();
  };

  // 주가 데이터 가져오기
  const fetchStockData = async (symbols: string[], startDate: string, endDate: string) => {
    setLoadingStockData(true);
    const stockDataResults: StockDataItem[] = [];

    for (const symbol of symbols) {
      // 현금 자산은 제외
      if (symbol.toUpperCase() === 'CASH' || symbol === '현금') {
        continue;
      }

      try {
        const response = await backtestApiService.getStockData(symbol, startDate, endDate);
        if (response.status === 'success' && response.data.price_data.length > 0) {
          stockDataResults.push({
            symbol: symbol,
            data: response.data.price_data
          });
        }
      } catch (error) {
        console.error(`주가 데이터 가져오기 실패 (${symbol}):`, error);
      }
    }

    setStocksData(stockDataResults);
    setLoadingStockData(false);
  };

  // 포트폴리오 차트 렌더링
  const renderPortfolioCharts = () => {
    if (!isPortfolio || !('portfolio_composition' in data)) {
      return null;
    }

    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, portfolio_composition, equity_curve, daily_returns } = portfolioData;

    // 데이터 가져오기 Effect
    useEffect(() => {
      const symbols = portfolio_composition.map(item => item.symbol);
      fetchStockData(symbols, portfolio_statistics.Start, portfolio_statistics.End);
    }, [portfolio_composition, portfolio_statistics.Start, portfolio_statistics.End]);

    // equity_curve를 배열로 변환
    const equityChartData: EquityChartDataItem[] = Object.entries(equity_curve).map(([date, value]) => ({
      date,
      value: value,
      return: daily_returns[date] || 0
    }));

    const isMultipleStocks = portfolio_composition.length > 1;

    return (
      <>
        {/* 백테스트 성과 통계 */}
        <StatsSummary stats={{
          total_return_pct: portfolio_statistics.Total_Return,
          total_trades: portfolio_statistics.Total_Trading_Days,
          win_rate_pct: portfolio_statistics.Win_Rate,
          max_drawdown_pct: portfolio_statistics.Max_Drawdown,
          sharpe_ratio: portfolio_statistics.Sharpe_Ratio,
          profit_factor: portfolio_statistics.Total_Return > 0 ? 
            (portfolio_statistics.Total_Return / Math.abs(portfolio_statistics.Max_Drawdown || 1)) : 1.0
        }} />

        {/* 포트폴리오 백테스트 결과 차트 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h5 className="text-lg font-semibold">📈 백테스트 수익률 곡선</h5>
          </div>
          <div className="p-6">
            <EquityChart data={equityChartData} />
          </div>
        </div>

        {/* 개별 종목 주가 차트 */}
        {loadingStockData ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">개별 종목 주가 데이터를 가져오는 중...</p>
          </div>
        ) : stocksData.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h5 className="text-lg font-semibold">
                개별 종목 주가 변동 ({stocksData.length}개 종목)
              </h5>
            </div>
            <div className="p-6">
              <StockPriceChart stocksData={stocksData} />
            </div>
          </div>
        )}

        {/* 주요 성과 지표 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-xl font-semibold">{isMultipleStocks ? '포트폴리오' : '종목'} 성과 요약</h4>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <h6 className="text-sm font-medium text-gray-600 mb-2">총 수익률</h6>
                <h4 className={`text-2xl font-bold ${(portfolio_statistics.Total_Return || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(portfolio_statistics.Total_Return)}
                </h4>
              </div>
              <div className="text-center">
                <h6 className="text-sm font-medium text-gray-600 mb-2">연간 수익률</h6>
                <h5 className={`text-xl font-semibold ${(portfolio_statistics.Annual_Return || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(portfolio_statistics.Annual_Return)}
                </h5>
              </div>
              <div className="text-center">
                <h6 className="text-sm font-medium text-gray-600 mb-2">샤프 비율</h6>
                <h5 className="text-xl font-semibold text-gray-800">{portfolio_statistics.Sharpe_Ratio ? portfolio_statistics.Sharpe_Ratio.toFixed(2) : 'N/A'}</h5>
              </div>
              <div className="text-center">
                <h6 className="text-sm font-medium text-gray-600 mb-2">최대 낙폭</h6>
                <h5 className="text-xl font-semibold text-red-600">{formatPercent(portfolio_statistics.Max_Drawdown)}</h5>
              </div>
            </div>

            {/* 추가 통계 정보 */}
            {portfolio_statistics && (
              <div className="mt-8">
                <h5 className="text-lg font-semibold mb-4">상세 통계</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">투자 기간</span>
                      <span className="text-sm font-medium text-gray-900">{portfolio_statistics.Duration}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">초기 자산</span>
                      <span className="text-sm font-medium text-gray-900">{formatCurrency(portfolio_statistics.Initial_Value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">최종 자산</span>
                      <span className="text-sm font-medium text-gray-900">{formatCurrency(portfolio_statistics.Final_Value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">최고 자산</span>
                      <span className="text-sm font-medium text-gray-900">{formatCurrency(portfolio_statistics.Peak_Value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">연간 변동성</span>
                      <span className="text-sm font-medium text-gray-900">{formatPercent(portfolio_statistics.Annual_Volatility)}</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">최대 연속 상승</span>
                      <span className="text-sm font-medium text-green-600">{portfolio_statistics.Max_Consecutive_Gains || 0}일</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">최대 연속 하락</span>
                      <span className="text-sm font-medium text-red-600">{portfolio_statistics.Max_Consecutive_Losses || 0}일</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">총 거래일</span>
                      <span className="text-sm font-medium text-gray-900">{portfolio_statistics.Total_Trading_Days || 0}일</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">평균 낙폭</span>
                      <span className="text-sm font-medium text-gray-900">{formatPercent(portfolio_statistics.Avg_Drawdown)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">상승일/하락일</span>
                      <span className="text-sm font-medium">
                        <span className="text-green-600">{portfolio_statistics.Positive_Days || 0}</span>
                        {' / '}
                        <span className="text-red-600">{portfolio_statistics.Negative_Days || 0}</span>
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">승률</span>
                      <span className="text-sm font-medium text-gray-900">{formatPercent(portfolio_statistics.Win_Rate)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 자산 곡선 차트 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h5 className="text-lg font-semibold">자산 곡선</h5>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={equityChartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: any) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: number) => formatCurrency(value)}
                />
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), isMultipleStocks ? '포트폴리오 가치' : '자산 가치']}
                  labelFormatter={(label: any) => `날짜: ${label}`}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#8884d8" 
                  fillOpacity={1} 
                  fill="url(#colorValue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 일일 수익률 차트 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h5 className="text-lg font-semibold">일일 수익률 분포</h5>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={equityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: any) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Tooltip 
                  formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
                  labelFormatter={(label: any) => `날짜: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="return" 
                  stroke="#ff7300" 
                  strokeWidth={1}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </>
    );
  };

  // 단일 종목 차트 렌더링
  const renderSingleStockCharts = () => {
    const chartData = data as ChartData;
    
    return (
      <>
        <StatsSummary stats={chartData.summary_stats || {}} />

        {/* 백테스트 결과 차트 (단일 종목) */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h5 className="text-lg font-semibold">📈 백테스트 결과</h5>
          </div>
          <div className="p-6">
            <OHLCChart 
              data={chartData.ohlc_data || []} 
              indicators={chartData.indicators || []} 
              trades={chartData.trade_markers || []} 
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h5 className="text-lg font-semibold">📊 수익률 곡선</h5>
          </div>
          <div className="p-6">
            <EquityChart data={chartData.equity_data || []} />
          </div>
        </div>

        {/* 개별 주가 차트 (단일 종목) */}
        {chartData.ticker && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h5 className="text-lg font-semibold">📊 개별 주가 변동</h5>
            </div>
            <div className="p-6">
              <StockPriceChart 
                stocksData={[{
                  symbol: chartData.ticker,
                  data: chartData.ohlc_data?.map(item => ({
                    date: item.date,
                    price: item.close,
                    volume: item.volume
                  })) || []
                }]} 
              />
            </div>
          </div>
        )}

        {/* 거래 내역 차트 (단일 종목) */}
        {chartData.trade_markers && chartData.trade_markers.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h5 className="text-lg font-semibold">📋 거래 내역</h5>
            </div>
            <div className="p-6">
              <TradesChart trades={chartData.trade_markers} />
            </div>
          </div>
        )}
      </>
    );
  };

  return (
    <>
      {isPortfolio ? renderPortfolioCharts() : renderSingleStockCharts()}
    </>
  );
};

export default ChartsSection;
