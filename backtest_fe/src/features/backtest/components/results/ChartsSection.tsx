import React, { Suspense, memo, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts';
import {
  LazyOHLCChart,
  LazyEquityChart,
  LazyTradesChart,
  LazyStatsSummary,
  LazyStockPriceChart,
} from '../lazy/LazyChartComponents';
import ChartLoading from '@/shared/components/ChartLoading';
import { ChartData, PortfolioData, EquityPoint, TradeMarker, OhlcPoint } from '../../model/backtest-result-types';
import { Grid3X3, Grid, Loader2 } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import TradeSignalsChart from '../TradeSignalsChart';
import VolatilityEventsSection from './VolatilityEventsSection';
import LatestNewsSection from './LatestNewsSection';
import BenchmarkIndexChart from './BenchmarkIndexChart';
import BenchmarkReturnsChart from './BenchmarkReturnsChart';
import RebalanceHistoryTable from './RebalanceHistoryTable';
import WeightHistoryChart from './WeightHistoryChart';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';

interface ChartsSectionProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ResultBlock: React.FC<{
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}> = ({ title, description, actions, children }) => (
  <div className={CARD_STYLES.base}>
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div className={SPACING.itemCompact}>
        <h3 className={HEADING_STYLES.h3}>{title}</h3>
        {description ? <p className={TEXT_STYLES.caption}>{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
    <div className="mt-4">{children}</div>
  </div>
);

const ChartsSection: React.FC<ChartsSectionProps> = memo(({ data, isPortfolio }) => {
  // 차트 레이아웃 모드 상태 (true: 2열, false: 1열)
  const [isCompactView, setIsCompactView] = useState(true);
  
  const portfolioData = useMemo<PortfolioData | null>(
    () => (isPortfolio && 'portfolio_composition' in data ? (data as PortfolioData) : null),
    [data, isPortfolio],
  );

  const chartData = useMemo<ChartData | null>(
    () => (!isPortfolio ? (data as ChartData) : null),
    [data, isPortfolio],
  );

  // 종목 메타데이터 (currency 포함)
  const tickerInfo = useMemo(() => {
    return portfolioData?.ticker_info || (data as any).ticker_info || {};
  }, [portfolioData, data]);

  // 통합 응답에서 주가 데이터 추출
  const stocksData = useMemo(() => {
    if (portfolioData?.stock_data) {
      return Object.entries(portfolioData.stock_data).map(([symbol, data]) => ({
        symbol,
        data,
      }));
    }
    if (chartData?.ticker && (data as any).stock_data) {
      const stockData = (data as any).stock_data[chartData.ticker];
      if (stockData) {
        return [{ symbol: chartData.ticker, data: stockData }];
      }
    }
    return [];
  }, [portfolioData, chartData, data]);

  // strategy_details에서 trade_log 추출 (symbol별)
  const tradeLogs = useMemo(() => {
    console.log('🔍 [ChartsSection] portfolioData:', portfolioData);
    console.log('🔍 [ChartsSection] strategy_details:', portfolioData?.strategy_details);

    const logs: Record<string, any[]> = {};
    if (portfolioData?.strategy_details) {
      Object.entries(portfolioData.strategy_details).forEach(([symbol, stats]) => {
        console.log('🔍 [ChartsSection] Processing symbol:', symbol, 'stats:', stats);
        if (stats.trade_log && Array.isArray(stats.trade_log)) {
          // 원본 심볼로 매핑 (예: "AAPL#0" → "AAPL")
          const cleanSymbol = symbol.split('#')[0];
          logs[cleanSymbol] = stats.trade_log;
          console.log('✅ [ChartsSection] Added trade_log for', cleanSymbol, ':', stats.trade_log.length, 'trades');
        } else {
          console.log('⚠️ [ChartsSection] No trade_log for', symbol);
        }
      });
    } else {
      console.log('⚠️ [ChartsSection] No strategy_details in portfolioData');
    }
    console.log('📊 [ChartsSection] Final tradeLogs:', logs);
    return logs;
  }, [portfolioData]);

  const loadingStockData = false; // 통합 응답이므로 별도 로딩 없음

  const formatCurrency = useMemo(
    () => (value: number): string => {
      if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
      if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
      if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
      return value.toLocaleString();
    },
    [],
  );

  const portfolioEquityData = useMemo<EquityPoint[]>(() => {
    if (!portfolioData) return [];
    return Object.entries(portfolioData.equity_curve).map(([date, value]) => ({
      date,
      value,
      return_pct: Number(portfolioData.daily_returns[date] ?? 0),
      drawdown_pct: 0,
    }));
  }, [portfolioData]);

  const singleEquityData = useMemo<EquityPoint[]>(() => {
    if (!chartData?.equity_data) return [];
    return chartData.equity_data.map(point => ({
      date: point.date,
      value: point.value,
      return_pct: Number(point.return_pct ?? (point as Record<string, unknown>).return ?? 0),
      drawdown_pct: Number(point.drawdown_pct ?? (point as Record<string, unknown>).drawdown ?? 0),
    }));
  }, [chartData?.equity_data]);

  const singleTrades = useMemo<TradeMarker[]>(() => {
    if (!chartData?.trade_markers) return [];
    return chartData.trade_markers.map(marker => ({
      ...marker,
      type: marker.type === 'entry' ? 'entry' : 'exit',
    }));
  }, [chartData?.trade_markers]);

  const singleOhlcData = useMemo<OhlcPoint[]>(() => {
    if (!chartData?.ohlc_data) return [];
    return chartData.ohlc_data.map(point => ({
      ...point,
      volume: Number(point.volume ?? 0),
    }));
  }, [chartData?.ohlc_data]);

  const statsPayload = useMemo<Record<string, unknown>>(() => {
    if (portfolioData) {
      return { ...portfolioData.portfolio_statistics } as Record<string, unknown>;
    }
    return chartData?.summary_stats ?? {};
  }, [portfolioData, chartData?.summary_stats]);

  // 벤치마크 데이터
  const sp500Benchmark = useMemo<any[]>(() => {
    const chartBenchmark = (data as ChartData).sp500_benchmark;
    const portfolioBenchmark = (data as PortfolioData).sp500_benchmark;
    const result = chartBenchmark ?? portfolioBenchmark ?? [];
    console.log('S&P 500 Benchmark data:', result.length, 'items');
    return result;
  }, [data]);

  const nasdaqBenchmark = useMemo<any[]>(() => {
    const chartBenchmark = (data as ChartData).nasdaq_benchmark;
    const portfolioBenchmark = (data as PortfolioData).nasdaq_benchmark;
    const result = chartBenchmark ?? portfolioBenchmark ?? [];
    console.log('NASDAQ Benchmark data:', result.length, 'items');
    return result;
  }, [data]);

  const withBenchmarkReturn = (points: any[]) =>
    points?.map((point, index) => {
      if (index === 0) {
        return { ...point, return_pct: 0 };
      }
      const prev = points[index - 1];
      const returnPct = ((point.close - prev.close) / prev.close) * 100;
      return { ...point, return_pct: returnPct };
    }) ?? [];



  const renderPortfolioCharts = (): React.ReactNode[] | null => {
    if (!portfolioData) return null;
    const { portfolio_composition } = portfolioData;
    const isMultipleStocks = portfolio_composition.length > 1;

    const cards: React.ReactNode[] = [
      (
        <ResultBlock
          title="누적 자산 가치"
          description="기간 동안 누적 자산 가치 변화를 확인하세요 (리밸런싱 시점 표시)"
          key="portfolio-equity"
        >
          <ResponsiveContainer width="100%" height={360}>
            <AreaChart data={portfolioEquityData}>
              <defs>
                <linearGradient id="portfolioValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value: string) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis tickFormatter={(value: number) => formatCurrency(value)} />
              <Tooltip
                formatter={(value: number) => [formatCurrency(value), isMultipleStocks ? '포트폴리오 가치' : '자산 가치']}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              {/* 리밸런싱 마커 */}
              {portfolioData?.rebalance_history?.map((event, idx) => (
                <ReferenceLine
                  key={idx}
                  x={event.date}
                  stroke="#f97316"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  label={{
                    value: '⚖️',
                    position: 'top',
                    fontSize: 16,
                  }}
                />
              ))}
              <Area type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} fill="url(#portfolioValue)" />
            </AreaChart>
          </ResponsiveContainer>
        </ResultBlock>
      ),
      (
        <ResultBlock
          title="일일 수익률"
          description="일별 수익률 변동을 살펴보며 변동성을 파악하세요"
          key="portfolio-daily"
        >
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={portfolioEquityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value: string) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis tickFormatter={(value: number) => `${value.toFixed(1)}%`} />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
                labelFormatter={(label: string) => `날짜: ${label}`}
              />
              <Line type="monotone" dataKey="return_pct" stroke="#f97316" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ResultBlock>
      ),
      (
        <ResultBlock
          title="개별 자산 주가"
          description="포트폴리오 구성 자산들의 가격 흐름"
          key="portfolio-prices"
        >
          {loadingStockData ? (
            <div className="flex flex-col items-center gap-3 py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">자산 데이터를 불러오는 중입니다...</p>
            </div>
          ) : stocksData.length > 0 ? (
            <Suspense fallback={<ChartLoading height={360} />}>
              <LazyStockPriceChart stocksData={stocksData} tickerInfo={tickerInfo} tradeLogs={tradeLogs} />
            </Suspense>
          ) : (
            <p className="text-sm text-muted-foreground">표시할 자산 데이터가 없습니다.</p>
          )}
        </ResultBlock>
      ),
    ];

    return cards;
  };

  const renderSingleStockCharts = (): React.ReactNode[] | null => {
    if (!chartData) return null;
    const cards: React.ReactNode[] = [
      (
        <ResultBlock title="OHLC 차트" description="가격 변동과 거래 시그널을 확인하세요" key="single-ohlc">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyOHLCChart
              data={singleOhlcData as any}
              indicators={(chartData.indicators ?? []) as any}
              trades={singleTrades as any}
            />
          </Suspense>
        </ResultBlock>
      ),
      (
        <ResultBlock title="수익률 & 드로우다운 차트" description="전략의 누적 수익률과 드로우다운을 확인하세요" key="single-equity">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyEquityChart data={singleEquityData as any} />
          </Suspense>
        </ResultBlock>
      ),
      (
        <ResultBlock
          title="개별 주가"
          description="백테스트 기간 동안의 주가 흐름"
          key="single-prices"
        >
          {loadingStockData ? (
            <div className="flex flex-col items-center gap-3 py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">자산 데이터를 불러오는 중입니다...</p>
            </div>
          ) : stocksData.length > 0 ? (
            <Suspense fallback={<ChartLoading height={360} />}>
              <LazyStockPriceChart stocksData={stocksData} tickerInfo={tickerInfo} tradeLogs={tradeLogs} />
            </Suspense>
          ) : (
            <p className="text-sm text-muted-foreground">표시할 주가 데이터가 없습니다.</p>
          )}
        </ResultBlock>
      ),
    ];

    if (singleTrades.length > 0 && chartData.strategy !== 'buy_hold_strategy') {
      cards.push(
        <ResultBlock title="거래 내역" description="전략이 실행한 체결 신호" key="single-trades">
          <Suspense fallback={<ChartLoading height={360} />}>
            <LazyTradesChart trades={singleTrades as any} showCard={false} />
          </Suspense>
        </ResultBlock>,
      );
      
      // 매매신호 그래프 추가
      cards.push(
        <ResultBlock title="매매신호 그래프" description="시간순 매수/매도 신호를 가격과 함께 확인하세요" key="trade-signals">
          <Suspense fallback={<ChartLoading height={400} />}>
            <TradeSignalsChart trades={singleTrades} />
          </Suspense>
        </ResultBlock>,
      );
    }

    return cards;
  };

  // 모든 차트를 하나의 배열로 통합
  const renderAllCharts = (): React.ReactNode[] => {
    const allCharts: React.ReactNode[] = [];
    
    // 1. 기본 차트 추가 (OHLC, 누적 수익률, 개별 주가, 거래 내역)
    const baseCharts = portfolioData ? renderPortfolioCharts() : renderSingleStockCharts();
    if (baseCharts) {
      allCharts.push(...baseCharts);
    }

    // 2. 지수 벤치마크 차트 (S&P 500 + NASDAQ)
    if (sp500Benchmark.length > 0 || nasdaqBenchmark.length > 0) {
      // 포트폴리오 또는 단일 종목 equity 데이터 선택
      const equityDataForBenchmark = isPortfolio ? portfolioEquityData : singleEquityData;

      allCharts.push(
        <BenchmarkIndexChart
          sp500Data={sp500Benchmark}
          nasdaqData={nasdaqBenchmark}
          portfolioEquityData={equityDataForBenchmark}
          key="benchmark-index"
        />
      );
    }

    // 3. 일일 수익률 벤치마크 차트 (S&P 500 + NASDAQ)
    if (sp500Benchmark.length > 0 || nasdaqBenchmark.length > 0) {
      allCharts.push(
        <BenchmarkReturnsChart
          sp500Data={withBenchmarkReturn(sp500Benchmark)}
          nasdaqData={withBenchmarkReturn(nasdaqBenchmark)}
          key="benchmark-returns"
        />
      );
    }

    // 3. 환율 차트 (통합 응답 데이터 사용)
    const exchangeRates = portfolioData?.exchange_rates || (data as any).exchange_rates;
    const exchangeStats = (data as any).exchange_stats;
    if (exchangeRates && exchangeRates.length > 0) {
      const minRate = Math.min(...exchangeRates.map((d: any) => d.rate));
      const maxRate = Math.max(...exchangeRates.map((d: any) => d.rate));
      
      allCharts.push(
        <ResultBlock
          title="환율 추이"
          description="동일 기간의 원/달러 환율 변동"
          key="exchange-rate"
        >
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={exchangeRates}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: any) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis 
                  domain={[minRate - 50, maxRate + 50]}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: number) => `₩${value.toFixed(0)}`}
                />
                <Tooltip 
                  formatter={(value: number) => [`₩${value.toFixed(2)}`, '환율']}
                  labelFormatter={(label: string) => `날짜: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="#10b981" 
                  strokeWidth={2} 
                  dot={false} 
                />
              </LineChart>
            </ResponsiveContainer>

            {/* 환율 주요 지점 정보 */}
            {exchangeStats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/30 rounded-lg">
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">시작점</div>
                  <div className="text-sm font-semibold text-foreground">
                    ₩{exchangeStats.start_point?.rate?.toFixed(2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.start_point?.date ? new Date(exchangeStats.start_point.date).toLocaleDateString('ko-KR') : ''}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">종료점</div>
                  <div className="text-sm font-semibold text-foreground">
                    ₩{exchangeStats.end_point?.rate?.toFixed(2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.end_point?.date ? new Date(exchangeStats.end_point.date).toLocaleDateString('ko-KR') : ''}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">최고점</div>
                  <div className="text-sm font-semibold text-green-600">
                    ₩{exchangeStats.high_point?.rate?.toFixed(2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.high_point?.date ? new Date(exchangeStats.high_point.date).toLocaleDateString('ko-KR') : ''}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">최저점</div>
                  <div className="text-sm font-semibold text-red-600">
                    ₩{exchangeStats.low_point?.rate?.toFixed(2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.low_point?.date ? new Date(exchangeStats.low_point.date).toLocaleDateString('ko-KR') : ''}
                  </div>
                </div>
              </div>
            )}
          </div>
        </ResultBlock>
      );
    }

    // 4. 급등락 이벤트
    const volatilityEvents = portfolioData?.volatility_events || (data as any).volatility_events || {};
    const hasVolatilityEvents = Object.keys(volatilityEvents).some(
      symbol => volatilityEvents[symbol] && volatilityEvents[symbol].length > 0
    );
    if (hasVolatilityEvents) {
      allCharts.push(
        <VolatilityEventsSection
          volatilityEvents={volatilityEvents}
          tickerInfo={tickerInfo}
          key="volatility-events"
        />
      );
    }

    // 5. 최신 뉴스
    const latestNews = portfolioData?.latest_news || (data as any).latest_news || {};
    const hasNews = Object.keys(latestNews).some(
      symbol => latestNews[symbol] && latestNews[symbol].length > 0
    );
    if (hasNews) {
      allCharts.push(
        <LatestNewsSection
          latestNews={latestNews}
          key="latest-news"
        />
      );
    }

    // 6. 리밸런싱 히스토리 테이블
    if (portfolioData?.rebalance_history && portfolioData.rebalance_history.length > 0) {
      allCharts.push(
        <ResultBlock
          title="리밸런싱 히스토리"
          description="포트폴리오 리밸런싱 이벤트 상세 내역"
          key="rebalance-history"
        >
          <RebalanceHistoryTable
            rebalanceHistory={portfolioData.rebalance_history}
            tickerInfo={tickerInfo}
          />
        </ResultBlock>
      );
    }

    // 7. 포트폴리오 비중 변화 차트 (종목이 2개 이상일 때만 표시)
    if (portfolioData?.weight_history && portfolioData.weight_history.length > 0 && portfolioData.portfolio_composition.length > 1) {
      allCharts.push(
        <ResultBlock
          title="포트폴리오 비중 변화"
          description="시간에 따른 각 자산(주식 + 현금)의 비중 변화 (스택 영역 차트)"
          key="weight-history"
        >
          <WeightHistoryChart
            weightHistory={portfolioData.weight_history}
            portfolioComposition={portfolioData.portfolio_composition}
            rebalanceHistory={portfolioData.rebalance_history}
          />
        </ResultBlock>
      );
    }

    return allCharts;
  };

  const allChartCards = renderAllCharts();

  return (
    <div className="space-y-6">
      {/* 1. 성과 지표 */}
      <Suspense fallback={<ChartLoading height={260} />}>
        <LazyStatsSummary stats={statsPayload} />
      </Suspense>

      {/* 2. 분석 차트 */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-foreground">분석 차트</h3>
          <p className="text-sm text-muted-foreground">
            백테스트 결과를 다양한 차트로 분석하세요
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsCompactView(!isCompactView)}
          className="flex items-center gap-2"
        >
          {isCompactView ? (
            <>
              <Grid className="w-4 h-4" />
              넓게 보기
            </>
          ) : (
            <>
              <Grid3X3 className="w-4 h-4" />
              컴팩트 보기
            </>
          )}
        </Button>
      </div>

      {/* 모든 분석 차트 (OHLC, 수익률, 주가, 거래내역, 벤치마크, 환율, 급등락, 뉴스) */}
      <div className={`grid gap-6 ${isCompactView ? 'md:grid-cols-2' : 'md:grid-cols-1'}`}>
        {allChartCards.map((card, index) => (
          <div key={index} className="flex flex-col">
            {card}
          </div>
        ))}
      </div>
    </div>
  );
});

ChartsSection.displayName = 'ChartsSection';

export default ChartsSection;
