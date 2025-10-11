/**
 * 통합 정보 섹션 컴포넌트
 * 
 * **역할**:
 * - 급등락 이벤트와 최신 뉴스를 하나의 박스로 통합 표시
 * - 여러 종목일 경우 종목 선택 버튼으로 전환
 * - 같은 기능(급등락/뉴스)끼리 탭으로 구분
 * 
 * **UI 구조**:
 * - 종목 선택 버튼 (여러 종목일 때만 표시)
 * - 탭: "급등락 이벤트" / "최신 뉴스"
 * - 내용 영역: 선택된 종목 + 탭에 따라 표시
 * 
 * **사용 사례**:
 * - 단일 종목 백테스트: 종목 버튼 없음, 탭만 표시
 * - 다중 종목 백테스트: 종목 버튼 + 탭 표시
 */
import React, { useState, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import { Button } from '@/shared/ui/button';

interface VolatilityEvent {
  date: string;
  daily_return: number;
  close_price: number;
  event_type: string;
}

interface NewsItem {
  title: string;
  description: string;
  link: string;
  pubDate: string;
}

interface UnifiedInfoSectionProps {
  volatilityEvents: { [symbol: string]: VolatilityEvent[] };
  latestNews: { [symbol: string]: NewsItem[] };
}

const UnifiedInfoSection: React.FC<UnifiedInfoSectionProps> = ({
  volatilityEvents,
  latestNews,
}) => {
  // 모든 종목 목록 (급등락 또는 뉴스가 있는 종목)
  const allSymbols = useMemo(() => {
    const symbols = new Set<string>();
    Object.keys(volatilityEvents || {}).forEach(s => symbols.add(s));
    Object.keys(latestNews || {}).forEach(s => symbols.add(s));
    return Array.from(symbols).sort();
  }, [volatilityEvents, latestNews]);

  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => allSymbols[0] || '');

  // 선택된 종목의 데이터
  const currentVolatilityEvents = volatilityEvents?.[selectedSymbol] || [];
  const currentNews = latestNews?.[selectedSymbol] || [];

  // 데이터가 없으면 렌더링하지 않음
  if (allSymbols.length === 0) return null;

  return (
    <div className="border border-border rounded-lg p-6 bg-card">
      {/* 종목 선택 버튼 (여러 종목일 때만 표시) */}
      {allSymbols.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {allSymbols.map(symbol => {
            const volatilityCount = volatilityEvents?.[symbol]?.length || 0;
            const newsCount = latestNews?.[symbol]?.length || 0;
            const hasData = volatilityCount > 0 || newsCount > 0;

            return (
              <Button
                key={symbol}
                variant={selectedSymbol === symbol ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedSymbol(symbol)}
                disabled={!hasData}
                className="flex items-center gap-2"
              >
                {symbol}
                {hasData && (
                  <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                    {volatilityCount + newsCount}
                  </span>
                )}
              </Button>
            );
          })}
        </div>
      )}

      {/* 급등락/뉴스 탭 */}
      <Tabs defaultValue="volatility" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="volatility">
            급등락 이벤트
            {currentVolatilityEvents.length > 0 && (
              <span className="ml-2 text-xs">({currentVolatilityEvents.length})</span>
            )}
          </TabsTrigger>
          <TabsTrigger value="news">
            최신 뉴스
            {currentNews.length > 0 && (
              <span className="ml-2 text-xs">({currentNews.length})</span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* 급등락 이벤트 탭 내용 */}
        <TabsContent value="volatility" className="mt-4">
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
        </TabsContent>

        {/* 최신 뉴스 탭 내용 */}
        <TabsContent value="news" className="mt-4">
          {currentNews.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {selectedSymbol}의 최신 뉴스가 없습니다.
            </div>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {currentNews.map((newsItem, idx) => (
                <a
                  key={idx}
                  href={newsItem.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-2 rounded hover:bg-muted/50 transition-colors border-b border-border/40 last:border-0"
                >
                  <div
                    className="text-sm font-medium text-primary hover:underline"
                    dangerouslySetInnerHTML={{ __html: newsItem.title }}
                  />
                  <div
                    className="text-xs text-muted-foreground mt-1"
                    dangerouslySetInnerHTML={{ __html: newsItem.description }}
                  />
                  <div className="text-xs text-muted-foreground mt-1">
                    {newsItem.pubDate}
                  </div>
                </a>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UnifiedInfoSection;
