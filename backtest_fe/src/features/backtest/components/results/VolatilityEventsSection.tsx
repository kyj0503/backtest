/**
 * 급등락 이벤트 섹션 컴포넌트
 * 
 * **역할**:
 * - 급등락 이벤트만 별도 박스로 표시
 * - 여러 종목일 경우 종목 선택 버튼으로 전환
 * 
 * **UI 구조**:
 * - 종목 선택 버튼 (여러 종목일 때만 표시)
 * - 내용 영역: 선택된 종목의 급등락 이벤트 리스트
 */
import React, { useState, useMemo } from 'react';
import { Button } from '@/shared/ui/button';
import { getStockDisplayName } from '../../model/strategyConfig';
import StockSymbolSelector from './StockSymbolSelector';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';
import { formatPriceWithCurrency } from '@/shared/lib/utils/numberUtils';
import { TickerInfo } from '../../model/types/backtest-result-types';

interface VolatilityEvent {
  date: string;
  daily_return: number;
  close_price: number;
  event_type: string;
}

interface VolatilityEventsSectionProps {
  volatilityEvents: { [symbol: string]: VolatilityEvent[] };
  tickerInfo?: { [symbol: string]: TickerInfo };
}

const VolatilityEventsSection: React.FC<VolatilityEventsSectionProps> = ({
  volatilityEvents,
  tickerInfo = {},
}) => {
  // 급등락 이벤트가 있는 종목 목록
  const allSymbols = useMemo(() => {
    const symbols = Object.keys(volatilityEvents || {}).filter(
      s => volatilityEvents[s] && volatilityEvents[s].length > 0
    );
    return symbols.sort();
  }, [volatilityEvents]);

  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => allSymbols[0] || '');

  // 선택된 종목의 데이터
  const currentVolatilityEvents = volatilityEvents?.[selectedSymbol] || [];

  // 데이터가 없으면 렌더링하지 않음
  if (allSymbols.length === 0) return null;

  // 구글 검색 함수
  const searchGoogleNews = (symbol: string, dateString: string) => {
    // 날짜를 한국어 형식으로 변환 (YYYY-MM-DD -> YYYY년 M월 D일)
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const koreanDate = `${year}년 ${month}월 ${day}일`;

    // 구글 검색 쿼리 생성 (표시 이름 사용)
    const displayName = getStockDisplayName(symbol);
    const query = `${displayName} ${koreanDate} 뉴스`;
    const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;

    // 새 탭에서 열기
    window.open(googleUrl, '_blank');
  };

  return (
    <div className={CARD_STYLES.base}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className={SPACING.itemCompact}>
          <h3 className={HEADING_STYLES.h3}>급등락 이벤트</h3>
          <p className={TEXT_STYLES.caption}>
            백테스트 기간 동안 발생한 급등락 이벤트
          </p>
        </div>
      </div>

      {/* 종목 선택 버튼 (여러 종목일 때만 표시) */}
      <StockSymbolSelector
        symbols={allSymbols}
        selectedSymbol={selectedSymbol}
        onSelectSymbol={setSelectedSymbol}
        className="mb-4"
      />

      {/* 급등락 이벤트 내용 */}
      {currentVolatilityEvents.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          {getStockDisplayName(selectedSymbol)}의 급등락 이벤트가 없습니다.
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {currentVolatilityEvents.slice(0, 10).map((event, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between border-b border-border/40 pb-2 last:border-0"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded ${
                    event.event_type === '급등'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-100'
                      : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-100'
                  }`}
                >
                  {event.event_type}
                </span>
                <span className="text-sm text-muted-foreground">{event.date}</span>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`text-sm font-semibold ${
                    event.daily_return > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {event.daily_return > 0 ? '+' : ''}
                  {event.daily_return.toFixed(2)}%
                </span>
                <span className="text-sm text-muted-foreground">
                  {formatPriceWithCurrency(
                    event.close_price,
                    tickerInfo[selectedSymbol]?.currency || 'USD'
                  )}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => searchGoogleNews(selectedSymbol, event.date)}
                  className="text-xs h-7 px-2"
                >
                  뉴스 확인
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default VolatilityEventsSection;
