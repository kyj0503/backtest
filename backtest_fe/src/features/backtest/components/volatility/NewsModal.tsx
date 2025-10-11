import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog';
import { ScrollArea } from '@/shared/ui/scroll-area';
import { NewsItem, VolatilityEvent, getCompanyName, formatPercent } from '../../model/volatility-news-types';

interface NewsModalProps {
  isVisible: boolean;
  onClose: () => void;
  selectedStock: string;
  currentEvent: VolatilityEvent | null;
  newsData: NewsItem[];
  newsLoading: boolean;
}

const NewsModal: React.FC<NewsModalProps> = ({
  isVisible,
  onClose,
  selectedStock,
  currentEvent,
  newsData,
  newsLoading
}) => {
  const modalTitle = currentEvent ?
    `${getCompanyName(selectedStock)} 뉴스 (${currentEvent.date})` :
    '';

  return (
    <Dialog open={isVisible} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>
            {modalTitle}
            {currentEvent && (
              <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                currentEvent.daily_return > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
              }`}>
                {formatPercent(currentEvent.daily_return)}
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            {currentEvent ? `${currentEvent.date} 변동성 관련 뉴스` : '뉴스 정보'}
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-96">
          {newsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p>뉴스를 불러오는 중...</p>
            </div>
          ) : newsData.length > 0 ? (
            <div>
              <div className="mb-4 p-3 bg-muted rounded-lg">
                <small className="text-muted-foreground">
                  최신 관련 뉴스를 표시합니다 (특정 날짜 뉴스 검색 제한으로 인해)
                </small>
              </div>
              <div className="space-y-4 pr-4">
                {newsData.map((news, index) => (
                  <div key={index} className="border-b border-border pb-4 last:border-b-0">
                    <h6
                      className="font-medium mb-2"
                      dangerouslySetInnerHTML={{ __html: news.title }}
                    />
                    <p
                      className="text-muted-foreground text-sm mb-2"
                      dangerouslySetInnerHTML={{ __html: news.description }}
                    />
                    <div className="flex justify-between items-center">
                      <small className="text-muted-foreground">{news.pubDate}</small>
                      <a
                        href={news.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 text-sm border border-primary/30 text-primary rounded hover:bg-primary/10 transition-colors"
                      >
                        원문 보기
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">해당 기간의 뉴스를 찾을 수 없습니다.</p>
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default NewsModal;
