import React from 'react';
import { NewsItem, VolatilityEvent, getCompanyName, formatPercent } from '../../types/volatility-news';

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
  if (!isVisible) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] mx-4">
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h5 className="text-lg font-semibold text-gray-900">
            {currentEvent && (
              <>
                {getCompanyName(selectedStock)} 뉴스 ({currentEvent.date})
                <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  currentEvent.daily_return > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                }`}>
                  {formatPercent(currentEvent.daily_return)}
                </span>
              </>
            )}
          </h5>
          <button 
            className="text-gray-400 hover:text-gray-600"
            onClick={onClose}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {newsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p>뉴스를 불러오는 중...</p>
            </div>
          ) : newsData.length > 0 ? (
            <div>
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <small className="text-blue-700">
                  💡 최신 관련 뉴스를 표시합니다 (특정 날짜 뉴스 검색 제한으로 인해)
                </small>
              </div>
              <div className="space-y-4">
                {newsData.map((news, index) => (
                  <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0">
                    <h6 
                      className="font-medium text-gray-900 mb-2" 
                      dangerouslySetInnerHTML={{ __html: news.title }}
                    />
                    <p 
                      className="text-gray-600 text-sm mb-2" 
                      dangerouslySetInnerHTML={{ __html: news.description }}
                    />
                    <div className="flex justify-between items-center">
                      <small className="text-gray-500">{news.pubDate}</small>
                      <a 
                        href={news.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="px-3 py-1 text-sm border border-blue-300 text-blue-700 rounded hover:bg-blue-50 transition-colors"
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
              <p className="text-gray-500">해당 기간의 뉴스를 찾을 수 없습니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewsModal;
