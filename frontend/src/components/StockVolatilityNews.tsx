import React, { useState, useEffect } from 'react';
import { backtestApiService } from "../services/api";
import VolatilityTable from './volatility/VolatilityTable';
import NewsModal from './volatility/NewsModal';
import { 
  VolatilityEvent, 
  NewsItem, 
  StockVolatilityNewsProps,
  getCompanyName,
  getApiBaseUrl 
} from '../types/volatility-news';

const StockVolatilityNews: React.FC<StockVolatilityNewsProps> = ({ 
  symbols, 
  startDate, 
  endDate, 
  className = "" 
}) => {
  const [volatilityData, setVolatilityData] = useState<{ [key: string]: VolatilityEvent[] }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [showNewsModal, setShowNewsModal] = useState(false);
  const [newsData, setNewsData] = useState<NewsItem[]>([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [currentNewsEvent, setCurrentNewsEvent] = useState<VolatilityEvent | null>(null);

  // 현금이 아닌 유효한 심볼만 필터링
  const validSymbols = symbols.filter(symbol => 
    symbol.toUpperCase() !== 'CASH' && symbol !== '현금'
  );

  useEffect(() => {
    if (validSymbols.length > 0) {
      fetchVolatilityData();
      setSelectedStock(validSymbols[0]);
    }
  }, [validSymbols, startDate, endDate]);

  const fetchVolatilityData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const results: { [key: string]: VolatilityEvent[] } = {};
      
      for (const symbol of validSymbols) {
        try {
          const response = await backtestApiService.getStockVolatilityNews(symbol, startDate, endDate);
          if (response.status === 'success' && response.data.volatility_events) {
            results[symbol] = response.data.volatility_events;
          } else {
            results[symbol] = [];
          }
        } catch (symbolError) {
          console.warn(`Failed to fetch volatility data for ${symbol}:`, symbolError);
          results[symbol] = [];
        }
      }
      
      setVolatilityData(results);
    } catch (err) {
      console.error('변동성 데이터 가져오기 실패:', err);
      setError('변동성 데이터를 가져오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleStockSelect = (symbol: string) => {
    setSelectedStock(symbol);
  };

  const openNaverNews = async (date: string, event: VolatilityEvent) => {
    setCurrentNewsEvent(event);
    setShowNewsModal(true);
    setNewsLoading(true);
    
    try {
      const companyName = getCompanyName(selectedStock);
      const baseUrl = getApiBaseUrl();
      const apiUrl = `${baseUrl}/api/v1/naver-news/search?query=${encodeURIComponent(companyName)}&start_date=${date}&end_date=${date}`;
      
      const response = await fetch(apiUrl);
      const data = await response.json();
      
      if (data.status === 'success' && data.data && data.data.items) {
        setNewsData(data.data.items);
      } else {
        setNewsData([]);
      }
    } catch (err) {
      console.error('뉴스 데이터 가져오기 실패:', err);
      setNewsData([]);
    } finally {
      setNewsLoading(false);
    }
  };

  // 로딩 중일 때
  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">📰 주가 급등/급락 뉴스</h5>
        </div>
        <div className="px-6 py-4 text-center">
          <div className="inline-flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            변동성 데이터를 불러오는 중...
          </div>
        </div>
      </div>
    );
  }

  // 에러가 있을 때
  if (error) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">📰 주가 급등/급락 뉴스</h5>
        </div>
        <div className="px-6 py-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>
        </div>
      </div>
    );
  }

  const selectedEvents = volatilityData[selectedStock] || [];
  const hasSignificantEvents = Object.values(volatilityData).some(events => events.length > 0);

  return (
    <>
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">📰 주가 급등/급락 뉴스 (5% 이상 변동일)</h5>
        </div>
        <div className="px-6 py-4">
          {!hasSignificantEvents ? (
            <div className="text-center">
              <p className="text-gray-500">해당 기간 중 5% 이상 급등/급락한 날이 없습니다.</p>
            </div>
          ) : (
            <>
              {/* 종목 선택 버튼들 */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                  {validSymbols.map(symbol => {
                    const eventCount = volatilityData[symbol]?.length || 0;
                    return (
                      <button
                        key={symbol}
                        className={`px-3 py-1 text-sm rounded transition-colors ${
                          selectedStock === symbol
                            ? 'bg-blue-600 text-white'
                            : 'border border-blue-300 text-blue-700 hover:bg-blue-50'
                        } ${eventCount === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={() => handleStockSelect(symbol)}
                        disabled={eventCount === 0}
                      >
                        {symbol}
                        {eventCount > 0 && (
                          <span className="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {eventCount}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 변동성 테이블 */}
              <VolatilityTable 
                selectedStock={selectedStock}
                events={selectedEvents}
                onNewsClick={openNaverNews}
              />
            </>
          )}
        </div>
      </div>

      {/* 뉴스 모달 */}
      <NewsModal
        isVisible={showNewsModal}
        onClose={() => setShowNewsModal(false)}
        selectedStock={selectedStock}
        currentEvent={currentNewsEvent}
        newsData={newsData}
        newsLoading={newsLoading}
      />
    </>
  );
};

export default StockVolatilityNews;
