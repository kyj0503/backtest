import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import OHLCChart from './OHLCChart';
import EquityChart from './EquityChart';
import TradesChart from './TradesChart';
import StatsSummary from './StatsSummary';
import StockPriceChart from './StockPriceChart';
import ExchangeRateChart from './ExchangeRateChart';
import StockVolatilityNews from './StockVolatilityNews';
import { formatPercent } from '../utils/formatters';
import { backtestApiService } from '../services/api';

interface Stock {
  symbol: string;
  weight: number;
}

interface IndividualReturn {
  weight: number;
  return: number;
  start_price: number;
  end_price: number;
}

interface PortfolioStatistics {
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

interface ChartData {
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

interface PortfolioData {
  portfolio_statistics: PortfolioStatistics;
  individual_returns: Record<string, IndividualReturn>;
  portfolio_composition: Stock[];
  equity_curve: Record<string, number>;
  daily_returns: Record<string, number>;
}

interface UnifiedBacktestResultsProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const UnifiedBacktestResults: React.FC<UnifiedBacktestResultsProps> = ({ data, isPortfolio }) => {
  const [stocksData, setStocksData] = useState<Array<{
    symbol: string;
    data: Array<{
      date: string;
      price: number;
      volume?: number;
    }>;
  }>>([]);
  const [loadingStockData, setLoadingStockData] = useState(false);

  // 주가 데이터 가져오기
  const fetchStockData = async (symbols: string[], startDate: string, endDate: string) => {
    setLoadingStockData(true);
    const stockDataResults = [];

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
        console.warn(`Failed to fetch stock data for ${symbol}:`, error);
      }
    }

    setStocksData(stockDataResults);
    setLoadingStockData(false);
  };

  // 포트폴리오 백테스트 결과가 있을 때 주가 데이터 가져오기
  useEffect(() => {
    if (isPortfolio && 'portfolio_composition' in data && 'portfolio_statistics' in data) {
      const portfolioData = data as PortfolioData;
      // 심볼에서 인덱스 제거 (예: AAPL_0 -> AAPL)
      const symbols = portfolioData.portfolio_composition.map((item: any) => {
        const symbol = item.symbol;
        // _숫자 패턴 제거
        return symbol.replace(/_\d+$/, '');
      });
      // 중복 제거
      const uniqueSymbols = [...new Set(symbols)];
      
      const startDate = portfolioData.portfolio_statistics.Start;
      const endDate = portfolioData.portfolio_statistics.End;
      
      if (uniqueSymbols.length > 0 && startDate && endDate) {
        fetchStockData(uniqueSymbols, startDate, endDate);
      }
    }
  }, [isPortfolio, data]);
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (!data) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center py-16">
          <div className="text-6xl mb-6">⚠️</div>
          <h4 className="text-xl font-semibold mb-3">결과 데이터가 없습니다</h4>
          <p className="text-gray-600">백테스트를 다시 실행해주세요.</p>
        </div>
      </div>
    );
  }

  // 포트폴리오 결과 렌더링
  if (isPortfolio) {
    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, individual_returns, portfolio_composition, equity_curve, daily_returns } = portfolioData;

    if (!portfolio_statistics || !individual_returns || !portfolio_composition || !equity_curve || !daily_returns) {
      return (
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-16">
            <div className="text-6xl mb-6">⚠️</div>
            <h4 className="text-xl font-semibold mb-3">결과 데이터가 불완전합니다</h4>
            <p className="text-gray-600">포트폴리오 백테스트를 다시 실행해주세요.</p>
          </div>
        </div>
      );
    }

    const equityChartData = Object.entries(equity_curve || {}).map(([date, value]) => ({
      date,
      value: value,
      return: daily_returns[date] || 0
    }));

    const isMultipleStocks = portfolio_composition.length > 1;

    return (
      <div className="max-w-6xl mx-auto space-y-8">
        {/* 헤더 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-blue-600 mb-2">
            {isMultipleStocks ? '📈 포트폴리오 백테스트 결과' : '📊 단일 종목 백테스트 결과'}
          </h2>
          <p className="text-gray-600">
            {portfolio_composition.map(item => item.symbol).join(', ')} | 
            {portfolio_statistics.Start} ~ {portfolio_statistics.End}
          </p>
        </div>

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

        {/* 원달러 환율 차트 */}
        {'portfolio_statistics' in data && (
          <ExchangeRateChart 
            startDate={(data as PortfolioData).portfolio_statistics.Start}
            endDate={(data as PortfolioData).portfolio_statistics.End}
            className="mb-8"
          />
        )}

        {/* 주가 급등/급락 뉴스 */}
        {'portfolio_composition' in data && (
          <StockVolatilityNews
            symbols={(data as PortfolioData).portfolio_composition.map(item => item.symbol)}
            startDate={(data as PortfolioData).portfolio_statistics.Start}
            endDate={(data as PortfolioData).portfolio_statistics.End}
            className="mb-8"
          />
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
                <h5 className="text-xl font-semibold text-red-600">
                  {formatPercent(portfolio_statistics.Max_Drawdown)}
                </h5>
              </div>
            </div>
          </div>
        </div>

        {/* 포트폴리오 구성 및 개별 수익률 */}
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h5 className="text-lg font-semibold">{isMultipleStocks ? '포트폴리오 구성' : '종목 정보'}</h5>
            </div>
            <div className="p-6">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">종목</th>
                      {isMultipleStocks && <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">비중</th>}
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">개별 수익률</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {portfolio_composition.map((item) => {
                      const individualReturn = individual_returns[item.symbol];
                      return (
                        <tr key={item.symbol}>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {item.symbol}
                            </span>
                          </td>
                          {isMultipleStocks && (
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{formatPercent(item.weight * 100)}</td>
                          )}
                          <td className={`px-4 py-4 whitespace-nowrap text-sm font-medium ${individualReturn?.return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {individualReturn ? formatPercent(individualReturn.return) : 'N/A'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          {isMultipleStocks && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h5 className="text-lg font-semibold">상세 통계</h5>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">백테스트 기간</span>
                    <span className="text-sm font-medium text-gray-900">{portfolio_statistics.Start} ~ {portfolio_statistics.End}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">초기 자본금</span>
                    <span className="text-sm font-medium text-gray-900">{formatCurrency(portfolio_statistics.Initial_Value)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">최종 자본금</span>
                    <span className="text-sm font-medium text-gray-900">{formatCurrency(portfolio_statistics.Final_Value)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">최고 자본금</span>
                    <span className="text-sm font-medium text-gray-900">{formatCurrency(portfolio_statistics.Peak_Value)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">연간 변동성</span>
                    <span className="text-sm font-medium text-gray-900">{formatPercent(portfolio_statistics.Annual_Volatility)}</span>
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
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), isMultipleStocks ? '포트폴리오 가치' : '자산 가치']}
                  labelFormatter={(label) => `날짜: ${label}`}
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
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${value.toFixed(1)}%`}
                />
                <Tooltip 
                  formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
                  labelFormatter={(label) => `날짜: ${label}`}
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
      </div>
    );
  }

  // 단일 종목 결과 렌더링 (기존 차트 컴포넌트 사용)
  const chartData = data as ChartData;
  
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* 헤더 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-2">📊 {chartData.ticker} - {chartData.strategy} 백테스트 결과</h2>
        <p className="text-gray-600">상세한 차트 분석과 거래 내역을 확인하세요</p>
      </div>

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

      {/* 원달러 환율 차트 (단일 종목) */}
      {chartData.start_date && chartData.end_date && (
        <ExchangeRateChart 
          startDate={chartData.start_date}
          endDate={chartData.end_date}
          className="mb-8"
        />
      )}

      {/* 주가 급등/급락 뉴스 (단일 종목) */}
      {chartData.ticker && chartData.start_date && chartData.end_date && (
        <StockVolatilityNews
          symbols={[chartData.ticker]}
          startDate={chartData.start_date}
          endDate={chartData.end_date}
          className="mb-8"
        />
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
    </div>
  );
};

export default UnifiedBacktestResults;
