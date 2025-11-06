/**
 * 리밸런싱 히스토리 테이블 컴포넌트
 *
 * **통화 표시 정책:**
 * - 리밸런싱은 백테스트 연산의 결과물이므로 **USD로 통일 표시**
 * - 포트폴리오 전체가 USD 기준으로 계산되므로 일관성 유지
 * - 수수료, 거래 가격, 거래 금액 모두 USD
 */
import React, { useState } from 'react';
import { RebalanceEvent, TickerInfo } from '../../model/types/backtest-result-types';
import { ChevronDown, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { CARD_STYLES, TEXT_STYLES, HEADING_STYLES, SPACING } from '@/shared/styles/design-tokens';
import { formatPriceWithCurrency } from '@/shared/lib/utils/numberUtils';

interface RebalanceHistoryTableProps {
  rebalanceHistory: RebalanceEvent[];
  tickerInfo?: { [symbol: string]: TickerInfo };
}

const RebalanceHistoryTable: React.FC<RebalanceHistoryTableProps> = ({ rebalanceHistory, tickerInfo = {} }) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  if (!rebalanceHistory || rebalanceHistory.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>리밸런싱 이벤트가 없습니다.</p>
        <p className="text-sm mt-2">리밸런싱이 비활성화되어 있거나 아직 발생하지 않았습니다.</p>
      </div>
    );
  }

  return (
    <div className={SPACING.item}>
      <div className={TEXT_STYLES.caption + ' mb-4'}>
        총 {rebalanceHistory.length}회의 리밸런싱이 발생했습니다
      </div>

      <div className={SPACING.itemCompact}>
        {rebalanceHistory.map((event, index) => {
          const isExpanded = expandedRows.has(index);

          return (
            <div
              key={index}
              className={CARD_STYLES.nested + ' overflow-hidden hover:border-border transition-colors'}
            >
              {/* Header */}
              <button
                onClick={() => toggleRow(index)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                  <span className="font-semibold text-foreground">
                    {new Date(event.date).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {event.trades.length}개 종목 거래
                  </span>
                </div>
                {event.commission_cost !== undefined && (
                  <span className="text-sm text-muted-foreground">
                    수수료: ${event.commission_cost.toFixed(2)}
                  </span>
                )}
              </button>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-4 border-t border-border/30">
                  {/* 거래 내역 */}
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-2 mt-3">거래 내역</h4>
                    <div className="space-y-1">
                      {event.trades.map((trade, tradeIdx) => (
                        <div
                          key={tradeIdx}
                          className={`flex items-center justify-between p-2 rounded ${
                            trade.action === 'buy' || trade.action === 'decrease'
                              ? 'bg-emerald-500/10'
                              : 'bg-red-500/10'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {trade.action === 'buy' || trade.action === 'decrease' ? (
                              <TrendingUp className="w-4 h-4 text-emerald-600" />
                            ) : (
                              <TrendingDown className="w-4 h-4 text-red-600" />
                            )}
                            <span className="font-medium">{trade.symbol}</span>
                            <span
                              className={`text-sm ${
                                trade.action === 'buy' || trade.action === 'decrease'
                                  ? 'text-emerald-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {trade.action === 'buy'
                                ? '매수'
                                : trade.action === 'sell'
                                ? '매도'
                                : trade.action === 'increase'
                                ? '증가'
                                : '감소'}
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm">
                              {trade.shares !== undefined
                                ? `${trade.shares.toFixed(2)}주 @ ${formatPriceWithCurrency(trade.price, 'USD')}`
                                : formatPriceWithCurrency(trade.amount || 0, 'USD')}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {trade.shares !== undefined
                                ? formatPriceWithCurrency(trade.shares * trade.price, 'USD')
                                : '현금'}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 비중 변화 */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-2">리밸런싱 전</h4>
                      <div className="space-y-1">
                        {Object.entries(event.weights_before).map(([symbol, weight]) => (
                          <div key={symbol} className="flex justify-between text-sm">
                            <span className="text-muted-foreground">{symbol}</span>
                            <span className="font-medium">{(weight * 100).toFixed(2)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-2">리밸런싱 후</h4>
                      <div className="space-y-1">
                        {Object.entries(event.weights_after).map(([symbol, weight]) => (
                          <div key={symbol} className="flex justify-between text-sm">
                            <span className="text-muted-foreground">{symbol}</span>
                            <span className="font-medium">{(weight * 100).toFixed(2)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RebalanceHistoryTable;
