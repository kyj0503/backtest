import React from 'react';
import { VolatilityEvent, formatPercent, getCompanyName } from '../../model/types/volatility-news-types';
import { formatPriceWithCurrency } from '@/shared/lib/utils/numberUtils';
import { TickerInfo } from '../../model/types/backtest-result-types';

interface VolatilityTableProps {
  selectedStock: string;
  events: VolatilityEvent[];
  onNewsClick: (date: string, event: VolatilityEvent) => void;
  newsDisabled?: boolean;
  tickerInfo?: { [symbol: string]: TickerInfo };
}

const VolatilityTable: React.FC<VolatilityTableProps> = ({ selectedStock, events, onNewsClick, newsDisabled = false, tickerInfo = {} }) => {
  if (events.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">{getCompanyName(selectedStock)}의 해당 기간 중 5% 이상 급등/급락한 날이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">날짜</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">변동률</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">종가</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">거래량</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">뉴스</th>
          </tr>
        </thead>
        <tbody className="bg-background divide-y divide-border">
          {events.map((event, index) => (
            <tr key={index} className="hover:bg-muted/50">
              <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                {new Date(event.date).toLocaleDateString('ko-KR')}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span className={`font-medium ${
                  event.daily_return >= 0 ? 'text-green-600' : 'text-destructive'
                }`}>
                  {formatPercent(event.daily_return)}
                </span>
                <span className={`ml-1 text-xs px-2 py-1 rounded ${
                  event.event_type === '급등' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-destructive/10 text-destructive'
                }`}>
                  {event.event_type}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                {formatPriceWithCurrency(event.close_price, tickerInfo[selectedStock]?.currency || 'USD')}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                {event.volume.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <button
                  onClick={() => onNewsClick(event.date, event)}
                  disabled={newsDisabled}
                  className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded transition-colors focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-primary ${
                    newsDisabled
                      ? 'cursor-not-allowed bg-muted text-muted-foreground'
                      : 'text-primary bg-accent hover:bg-accent/80'
                  }`}
                >
                  📰 뉴스 보기
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default VolatilityTable;
