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

interface VolatilityEvent {
  date: string;
  daily_return: number;
  close_price: number;
  event_type: string;
}

interface VolatilityEventsSectionProps {
  volatilityEvents: { [symbol: string]: VolatilityEvent[] };
}

const VolatilityEventsSection: React.FC<VolatilityEventsSectionProps> = ({
  volatilityEvents,
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

  return (
    <div className="space-y-3 rounded-2xl border border-border/40 bg-card/30 p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">급등락 이벤트</h3>
          <p className="text-sm text-muted-foreground">
            백테스트 기간 동안 발생한 급등락 이벤트
          </p>
        </div>
      </div>

      {/* 종목 선택 버튼 (여러 종목일 때만 표시) */}
      {allSymbols.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {allSymbols.map(symbol => {
            const eventCount = volatilityEvents?.[symbol]?.length || 0;

            return (
              <Button
                key={symbol}
                variant={selectedSymbol === symbol ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedSymbol(symbol)}
                className="flex items-center gap-2"
              >
                {symbol}
                {eventCount > 0 && (
                  <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                    {eventCount}
                  </span>
                )}
              </Button>
            );
          })}
        </div>
      )}

      {/* 급등락 이벤트 내용 */}
      {currentVolatilityEvents.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          {selectedSymbol}의 급등락 이벤트가 없습니다.
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
                  ${event.close_price.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default VolatilityEventsSection;
