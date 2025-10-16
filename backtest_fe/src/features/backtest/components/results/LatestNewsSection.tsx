/**
 * 최신 뉴스 섹션 컴포넌트
 * 
 * **역할**:
 * - 최신 뉴스만 별도 박스로 표시
 * - 여러 종목일 경우 종목 선택 버튼으로 전환
 * 
 * **UI 구조**:
 * - 종목 선택 버튼 (여러 종목일 때만 표시)
 * - 내용 영역: 선택된 종목의 최신 뉴스 리스트
 */
import React, { useState, useMemo } from 'react';
import { Button } from '@/shared/ui/button';

interface NewsItem {
  title: string;
  description: string;
  link: string;
  pubDate: string;
}

interface LatestNewsSectionProps {
  latestNews: { [symbol: string]: NewsItem[] };
}

const LatestNewsSection: React.FC<LatestNewsSectionProps> = ({
  latestNews,
}) => {
  // 뉴스가 있는 종목 목록
  const allSymbols = useMemo(() => {
    const symbols = Object.keys(latestNews || {}).filter(
      s => latestNews[s] && latestNews[s].length > 0
    );
    return symbols.sort();
  }, [latestNews]);

  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => allSymbols[0] || '');

  // 선택된 종목의 데이터
  const currentNews = latestNews?.[selectedSymbol] || [];

  // 데이터가 없으면 렌더링하지 않음
  if (allSymbols.length === 0) return null;

  return (
    <div className="space-y-3 rounded-2xl border border-border/40 bg-card/30 p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">최신 뉴스</h3>
          <p className="text-sm text-muted-foreground">
            백테스트 기간과 관련된 최신 뉴스
          </p>
        </div>
      </div>

      {/* 종목 선택 버튼 (여러 종목일 때만 표시) */}
      {allSymbols.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {allSymbols.map(symbol => {
            const newsCount = latestNews?.[symbol]?.length || 0;

            return (
              <Button
                key={symbol}
                variant={selectedSymbol === symbol ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedSymbol(symbol)}
                className="flex items-center gap-2"
              >
                {symbol}
                {newsCount > 0 && (
                  <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                    {newsCount}
                  </span>
                )}
              </Button>
            );
          })}
        </div>
      )}

      {/* 최신 뉴스 내용 */}
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
    </div>
  );
};

export default LatestNewsSection;
