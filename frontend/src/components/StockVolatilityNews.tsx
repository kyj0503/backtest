import React, { useState, useEffect } from 'react';
import { backtestApiService } from "../services/api";

interface VolatilityEvent {
  date: string;
  daily_return: number;
  close_price: number;
  volume: number;
  event_type: string;
}

interface NewsItem {
  title: string;
  description: string;
  link: string;
  pubDate: string;
  company: string;
}

interface StockVolatilityNewsProps {
  symbols: string[];
  startDate: string;
  endDate: string;
  className?: string;
}

// 티커 심볼을 한국어 기업명으로 매핑 (백엔드와 동일한 매핑 사용)
const TICKER_TO_COMPANY_NAME: { [key: string]: string } = {
  // 미국 주요 종목
  'AAPL': '애플',
  'MSFT': '마이크로소프트',
  'GOOGL': '구글',
  'GOOGLE': '구글',
  'AMZN': '아마존',
  'TSLA': '테슬라',
  'META': '메타',
  'NVDA': '엔비디아',
  'NFLX': '넷플릭스',
  'AMD': 'AMD',
  'INTC': '인텔',
  'CRM': '세일즈포스',
  'ORCL': '오라클',
  'ADBE': '어도비',
  'PYPL': '페이팔',
  'UBER': '우버',
  'SNAP': '스냅챗',
  'SPOT': '스포티파이',
  'SQ': '스퀘어',
  'ZOOM': '줌',
  'SHOP': '쇼피파이',
  'ROKU': '로쿠',
  'PINS': '핀터레스트',
  'DOCU': '도큐사인',
  'OKTA': '옥타',
  'DDOG': '데이터독',
  'SNOW': '스노우플레이크',
  'PLTR': '팔란티어',
  'RBLX': '로블록스',
  'U': '유니티',
  'COIN': '코인베이스',
  'RIVN': '리비안',
  'LCID': '루시드',
  
  // 한국 주요 종목
  '005930.KS': '삼성전자',
  '000660.KS': 'SK하이닉스',
  '035420.KS': 'NAVER',
  '207940.KS': '삼성바이오로직스',
  '006400.KS': '삼성SDI',
  '051910.KS': 'LG화학',
  '373220.KS': 'LG에너지솔루션',
  '000270.KS': '기아',
  '005380.KS': '현대차',
  '035720.KS': '카카오',
  '096770.KS': 'SK이노베이션',
  '017670.KS': 'SK텔레콤',
  '030200.KS': 'KT',
  '055550.KS': '신한지주',
  '105560.KS': 'KB금융',
  '086790.KS': '하나금융지주',
  '316140.KS': '우리금융지주',
  '028260.KS': '삼성물산',
  '010950.KS': 'S-Oil',
  '009150.KS': '삼성전기',
  '323410.KS': '카카오뱅크',
  '018260.KS': '삼성에스디에스',
  '068270.KS': '셀트리온',
  '003670.KS': '포스코퓨처엠',
  '066570.KS': 'LG전자',
  '034730.KS': 'SK',
  '015760.KS': '한국전력',
  '036570.KS': '엔씨소프트',
  '012330.KS': '현대모비스',
  '003550.KS': 'LG',
  '251270.KS': '넷마블',
  '009540.KS': 'HD한국조선해양',
  '032830.KS': '삼성생명',
  '033780.KS': 'KT&G',
  '090430.KS': '아모레퍼시픽',
  '180640.KS': '한진칼',
  '128940.KS': '한미약품',
  '047050.KS': '포스코인터내셔널'
};

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

  // 현금 자산 제외 및 유효한 심볼만 필터링
  const validSymbols = symbols.filter(symbol => 
    symbol.toUpperCase() !== 'CASH' && 
    symbol !== '현금' &&
    symbol.trim() !== ''
  );

  useEffect(() => {
    if (validSymbols.length === 0) return;
    
    const fetchVolatilityData = async () => {
      setLoading(true);
      setError(null);
      const allVolatilityData: { [key: string]: VolatilityEvent[] } = {};

      try {
        for (const symbol of validSymbols) {
          try {
            const response = await backtestApiService.getStockVolatilityNews(symbol, startDate, endDate);
            if (response.status === 'success' && response.data.volatility_events) {
              allVolatilityData[symbol] = response.data.volatility_events;
            } else {
              allVolatilityData[symbol] = [];
            }
          } catch (symbolError) {
            console.warn(`${symbol} 변동성 데이터 조회 실패:`, symbolError);
            allVolatilityData[symbol] = [];
          }
        }

        setVolatilityData(allVolatilityData);
        
        // 첫 번째 유효한 종목을 선택
        if (validSymbols.length > 0) {
          setSelectedStock(validSymbols[0]);
        }
      } catch (error) {
        console.error('변동성 데이터 조회 실패:', error);
        setError('주가 변동성 데이터를 가져올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchVolatilityData();
  }, [symbols, startDate, endDate]);

  const handleStockSelect = (symbol: string) => {
    setSelectedStock(symbol);
  };

  const getCompanyName = (ticker: string): string => {
    return TICKER_TO_COMPANY_NAME[ticker.toUpperCase()] || ticker;
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatPrice = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const fetchNewsForEvent = async (ticker: string, date: string, event: VolatilityEvent) => {
    setNewsLoading(true);
    setCurrentNewsEvent(event);
    
    try {
      // 먼저 날짜별 검색 시도
      const response = await backtestApiService.getNaverNews(ticker, date, 10);
      if (response.status === 'success' && response.data && response.data.news_list && response.data.news_list.length > 0) {
        setNewsData(response.data.news_list);
        setShowNewsModal(true);
      } else {
        // 날짜별 검색 실패 시 일반 검색 시도 (최신 뉴스)
        console.log(`특정 날짜(${date}) 뉴스 없음, 일반 뉴스 검색 시도`);
        try {
          const generalResponse = await fetch(`${getApiBaseUrl()}/api/v1/naver-news/ticker/${ticker}?display=10`);
          if (generalResponse.ok) {
            const generalData = await generalResponse.json();
            if (generalData.status === 'success' && generalData.data.news_list.length > 0) {
              setNewsData(generalData.data.news_list);
              setShowNewsModal(true);
              return;
            }
          }
        } catch (generalError) {
          console.warn('일반 뉴스 검색도 실패:', generalError);
        }
        
        // 모든 검색 실패 시 빈 배열로 설정하고 모달 표시
        setNewsData([]);
        setShowNewsModal(true);
      }
    } catch (error) {
      console.error('뉴스 조회 실패:', error);
      setNewsData([]);
      setShowNewsModal(true);
    } finally {
      setNewsLoading(false);
    }
  };

  const getApiBaseUrl = (): string => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      const protocol = window.location.protocol;
      
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return `${protocol}//backtest-be.yeonjae.kr`;
      }
    }
    return 'http://localhost:8001';
  };

  const openNaverNews = (date: string, event: VolatilityEvent) => {
    // 네이버 뉴스 API를 사용하여 뉴스 조회 (티커로 검색)
    fetchNewsForEvent(selectedStock, date, event);
  };

  if (validSymbols.length === 0) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">📰 주가 급등/급락 뉴스</h5>
        </div>
        <div className="px-6 py-4 text-center">
          <p className="text-gray-500">분석할 주식 종목이 없습니다.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">📰 주가 급등/급락 뉴스</h5>
        </div>
        <div className="px-6 py-4 text-center">
          <div className="inline-flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            <span>주가 변동성 분석 중...</span>
          </div>
        </div>
      </div>
    );
  }

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
            <div className="mb-3">
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

            {/* 선택된 종목의 변동성 이벤트 */}
            {selectedStock && selectedEvents.length > 0 && (
              <div>
                <h6 className="text-base font-medium text-gray-900 mb-3">
                  {getCompanyName(selectedStock)} ({selectedStock}) 주가 급변동일
                </h6>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {selectedEvents.map((event, index) => (
                    <div key={index} className={`bg-white border rounded-lg p-4 h-full ${
                      event.daily_return > 0 ? 'border-l-4 border-l-red-500' : 'border-l-4 border-l-green-500'
                    }`}>
                      <div className="flex justify-between items-start mb-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          event.daily_return > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                        }`}>
                          {event.event_type}
                        </span>
                        <small className="text-gray-500">{event.date}</small>
                      </div>
                      
                      <h6 className={`mb-1 font-semibold ${
                        event.daily_return > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {formatPercent(event.daily_return)}
                      </h6>
                      
                      <div className="text-sm text-gray-500 mb-3">
                        <div>종가: {formatPrice(event.close_price)}</div>
                        <div>거래량: {event.volume.toLocaleString()}</div>
                      </div>
                      
                      <button
                        className="w-full px-4 py-2 text-sm border border-blue-300 text-blue-700 rounded hover:bg-blue-50 transition-colors disabled:opacity-50"
                        disabled={newsLoading}
                        onClick={() => openNaverNews(event.date, event)}
                      >
                        {newsLoading ? (
                          <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                            뉴스 로딩 중...
                          </div>
                        ) : (
                          '🔍 해당일 뉴스 보기'
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* 뉴스 모달 */}
      {showNewsModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowNewsModal(false);
            }
          }}
        >
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] mx-4">
            <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h5 className="text-lg font-semibold text-gray-900">
                {currentNewsEvent && (
                  <>
                    {getCompanyName(selectedStock)} 뉴스 ({currentNewsEvent.date})
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      currentNewsEvent.daily_return > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {formatPercent(currentNewsEvent.daily_return)}
                    </span>
                  </>
                )}
              </h5>
              <button 
                className="text-gray-400 hover:text-gray-600"
                onClick={() => setShowNewsModal(false)}
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
                  <p className="text-gray-500 mb-4">
                    해당 날짜({currentNewsEvent?.date})의 {getCompanyName(selectedStock)} 뉴스를 찾을 수 없습니다.
                    <br />
                    <small className="text-gray-400">
                      과거 날짜의 뉴스는 네이버 API에서 제한적으로 제공됩니다.
                    </small>
                  </p>
                  <div className="flex gap-2 justify-center">
                    <button
                      className="px-4 py-2 text-sm border border-blue-300 text-blue-700 rounded hover:bg-blue-50 transition-colors"
                      onClick={() => {
                        const companyName = getCompanyName(selectedStock);
                        const date = currentNewsEvent?.date.replace(/-/g, '.');
                        const searchQuery = encodeURIComponent(`${companyName} 주가`);
                        const url = `https://search.naver.com/search.naver?where=news&query=${searchQuery}&sm=tab_opt&sort=1&photo=0&field=0&pd=3&ds=${date}&de=${date}`;
                        window.open(url, '_blank');
                      }}
                    >
                      📅 해당 날짜로 검색
                    </button>
                    <button
                      className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
                      onClick={() => {
                        const companyName = getCompanyName(selectedStock);
                        const searchQuery = encodeURIComponent(`${companyName} 주가`);
                        const url = `https://search.naver.com/search.naver?where=news&query=${searchQuery}`;
                        window.open(url, '_blank');
                      }}
                    >
                      🔍 전체 뉴스 검색
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockVolatilityNews;
