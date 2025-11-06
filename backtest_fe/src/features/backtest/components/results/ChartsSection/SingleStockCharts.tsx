/**
 * 단일 종목 차트 컴포넌트
 * OHLC, 수익률&드로우다운, 개별 주가, 거래 내역, 매매신호 차트
 */

import React, { Suspense } from 'react';
import { Loader2 } from 'lucide-react';
import {
  LazyOHLCChart,
  LazyEquityChart,
  LazyTradesChart,
  LazyStockPriceChart,
} from '../../lazy/LazyChartComponents';
import ChartLoading from '@/shared/components/ChartLoading';
import { ResultBlock } from '../../shared';
import TradeSignalsChart from '../../TradeSignalsChart';
import { ChartData, EquityPoint, TradeMarker, OhlcPoint } from '../../../model/types';

interface SingleStockChartsProps {
  chartData: ChartData;
  singleEquityData: EquityPoint[];
  singleTrades: TradeMarker[];
  singleOhlcData: OhlcPoint[];
  stocksData: Array<{ symbol: string; data: any[] }>;
  tickerInfo: Record<string, any>;
  tradeLogs: Record<string, any[]>;
  loadingStockData?: boolean;
}

export const SingleStockCharts: React.FC<SingleStockChartsProps> = ({
  chartData,
  singleEquityData,
  singleTrades,
  singleOhlcData,
  stocksData,
  tickerInfo,
  tradeLogs,
  loadingStockData = false,
}) => {
  const showTradeCharts = singleTrades.length > 0 && chartData.strategy !== 'buy_hold_strategy';

  return (
    <>
      {/* OHLC 차트 */}
      <ResultBlock title="OHLC 차트" description="가격 변동과 거래 시그널을 확인하세요">
        <Suspense fallback={<ChartLoading height={360} />}>
          <LazyOHLCChart
            data={singleOhlcData as any}
            indicators={(chartData.indicators ?? []) as any}
            trades={singleTrades as any}
          />
        </Suspense>
      </ResultBlock>

      {/* 수익률 & 드로우다운 차트 */}
      <ResultBlock title="수익률 & 드로우다운 차트" description="전략의 누적 수익률과 드로우다운을 확인하세요">
        <Suspense fallback={<ChartLoading height={360} />}>
          <LazyEquityChart data={singleEquityData as any} />
        </Suspense>
      </ResultBlock>

      {/* 개별 주가 */}
      <ResultBlock title="개별 주가" description="백테스트 기간 동안의 주가 흐름">
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

      {/* 거래 내역 및 매매신호 (Buy & Hold가 아닌 경우에만) */}
      {showTradeCharts && (
        <>
          <ResultBlock title="거래 내역" description="전략이 실행한 체결 신호">
            <Suspense fallback={<ChartLoading height={360} />}>
              <LazyTradesChart trades={singleTrades as any} showCard={false} />
            </Suspense>
          </ResultBlock>

          <ResultBlock title="매매신호 그래프" description="시간순 매수/매도 신호를 가격과 함께 확인하세요">
            <Suspense fallback={<ChartLoading height={400} />}>
              <TradeSignalsChart trades={singleTrades} />
            </Suspense>
          </ResultBlock>
        </>
      )}
    </>
  );
};
