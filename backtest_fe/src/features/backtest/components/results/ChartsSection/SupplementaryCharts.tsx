/**
 * 부가 정보 차트 컴포넌트
 * 환율, 급등락 이벤트, 최신 뉴스, 리밸런싱 히스토리, 포트폴리오 비중 변화
 */

import React, { memo, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { ResultBlock } from '../../shared';
import VolatilityEventsSection from '../VolatilityEventsSection';
import LatestNewsSection from '../LatestNewsSection';
import RebalanceHistoryTable from '../RebalanceHistoryTable';
import WeightHistoryChart from '../WeightHistoryChart';
import { formatDateShort, formatKRW } from '../../../utils';

interface SupplementaryChartsProps {
  // 환율 데이터
  exchangeRates: any[];
  exchangeStats: any;

  // 급등락/뉴스 데이터
  volatilityEvents: Record<string, any[]>;
  latestNews: Record<string, any[]>;
  hasVolatilityEvents: boolean;
  hasNews: boolean;
  tickerInfo: Record<string, any>;

  // 리밸런싱 데이터 (포트폴리오만)
  rebalanceHistory: any[];
  weightHistory: any[];
  portfolioComposition?: any[];
}

export const SupplementaryCharts: React.FC<SupplementaryChartsProps> = memo(({
  exchangeRates,
  exchangeStats,
  volatilityEvents,
  latestNews,
  hasVolatilityEvents,
  hasNews,
  tickerInfo,
  rebalanceHistory,
  weightHistory,
  portfolioComposition,
}) => {
  const hasExchangeRates = exchangeRates && exchangeRates.length > 0;
  const hasRebalanceHistory = rebalanceHistory && rebalanceHistory.length > 0;
  const hasWeightHistory =
    weightHistory &&
    weightHistory.length > 0 &&
    portfolioComposition &&
    portfolioComposition.length > 1;

  // 환율 Y축 domain 계산 메모이제이션 (매 렌더링마다 재계산 방지)
  const exchangeRateDomain = useMemo(() => {
    if (!hasExchangeRates) return [0, 100];
    const rates = exchangeRates.map((d: any) => d.rate);
    return [Math.min(...rates), Math.max(...rates)];
  }, [exchangeRates, hasExchangeRates]);

  return (
    <>
      {/* 환율 차트 */}
      {hasExchangeRates && (
        <ResultBlock title="환율 추이" description="동일 기간의 원/달러 환율 변동">
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={exchangeRates}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={formatDateShort} />
                <YAxis
                  domain={exchangeRateDomain}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: number) => formatKRW(value)}
                />
                <Tooltip
                  formatter={(value: number) => [formatKRW(value, 2), '환율']}
                  labelFormatter={(label: string) => `날짜: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="#10b981" 
                  strokeWidth={2} 
                  dot={false} 
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>

            {/* 환율 주요 지점 정보 */}
            {exchangeStats && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-muted/30 rounded-lg">
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">시작점</div>
                  <div className="text-sm font-semibold text-foreground">
                    {formatKRW(exchangeStats.start_point?.rate, 2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.start_point?.date
                      ? new Date(exchangeStats.start_point.date).toLocaleDateString('ko-KR')
                      : ''}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">종료점</div>
                  <div className="text-sm font-semibold text-foreground">
                    {formatKRW(exchangeStats.end_point?.rate, 2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.end_point?.date
                      ? new Date(exchangeStats.end_point.date).toLocaleDateString('ko-KR')
                      : ''}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">최고점</div>
                  <div className="text-sm font-semibold text-green-600">
                    {formatKRW(exchangeStats.high_point?.rate, 2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.high_point?.date
                      ? new Date(exchangeStats.high_point.date).toLocaleDateString('ko-KR')
                      : ''}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground mb-1">최저점</div>
                  <div className="text-sm font-semibold text-red-600">
                    {formatKRW(exchangeStats.low_point?.rate, 2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {exchangeStats.low_point?.date
                      ? new Date(exchangeStats.low_point.date).toLocaleDateString('ko-KR')
                      : ''}
                  </div>
                </div>
              </div>
            )}
          </div>
        </ResultBlock>
      )}

      {/* 급등락 이벤트 */}
      {hasVolatilityEvents && (
        <VolatilityEventsSection volatilityEvents={volatilityEvents} tickerInfo={tickerInfo} />
      )}

      {/* 최신 뉴스 */}
      {hasNews && <LatestNewsSection latestNews={latestNews} />}

      {/* 리밸런싱 히스토리 테이블 */}
      {hasRebalanceHistory && (
        <ResultBlock title="리밸런싱 히스토리" description="포트폴리오 리밸런싱 이벤트 상세 내역">
          <RebalanceHistoryTable rebalanceHistory={rebalanceHistory} />
        </ResultBlock>
      )}

      {/* 포트폴리오 비중 변화 차트 */}
      {hasWeightHistory && (
        <ResultBlock
          title="포트폴리오 비중 변화"
          description="시간에 따른 각 자산(주식 + 현금)의 비중 변화 (스택 영역 차트)"
        >
          <WeightHistoryChart
            weightHistory={weightHistory}
            portfolioComposition={portfolioComposition!}
            rebalanceHistory={rebalanceHistory}
          />
        </ResultBlock>
      )}
    </>
  );
});

SupplementaryCharts.displayName = 'SupplementaryCharts';
