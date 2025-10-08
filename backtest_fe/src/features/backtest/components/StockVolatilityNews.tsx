import React from 'react';
import VolatilityTable from './volatility/VolatilityTable';
import NewsModal from './volatility/NewsModal';
import { useVolatilityNews } from '../hooks/useVolatilityNews';
import { StockVolatilityNewsProps } from '../model/volatility-news-types';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';

const StockVolatilityNews: React.FC<StockVolatilityNewsProps> = ({ 
  symbols, 
  startDate, 
  endDate, 
  className = "" 
}) => {
  const {
    volatilityData,
    selectedStock,
    newsData,
    showNewsModal,
    currentNewsEvent,
    loading,
    newsLoading,
    error,
    actions: {
      setSelectedStock,
      openNewsModal,
      closeNewsModal
    }
  } = useVolatilityNews({ symbols, startDate, endDate, canViewNews: true });

  // 현금이 아닌 유효한 심볼만 필터링
  const validSymbols = symbols.filter(symbol => 
    symbol.toUpperCase() !== 'CASH' && symbol !== '현금'
  );

  // 로딩 중일 때
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">📰 주가 급등/급락 뉴스</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <div className="inline-flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
            변동성 데이터를 불러오는 중...
          </div>
        </CardContent>
      </Card>
    );
  }

  // 에러가 있을 때
  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">📰 주가 급등/급락 뉴스</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-destructive">{error}</div>
        </CardContent>
      </Card>
    );
  }

  const selectedEvents = volatilityData[selectedStock] || [];
  const hasSignificantEvents = Object.values(volatilityData).some(events => events.length > 0);

  return (
    <>
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">📰 주가 급등/급락 뉴스 (5% 이상 변동일)</CardTitle>
        </CardHeader>
        <CardContent>
          {!hasSignificantEvents ? (
            <div className="text-center">
              <p className="text-muted-foreground">해당 기간 중 5% 이상 급등/급락한 날이 없습니다.</p>
            </div>
          ) : (
            <>
              {/* 종목 선택 버튼들 */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                  {validSymbols.map((symbol, idx) => {
                    const eventCount = volatilityData[symbol]?.length || 0;
                    return (
                      <button
                        key={`${symbol}_${idx}`}
                        className={`px-3 py-1 text-sm rounded transition-colors ${
                          selectedStock === symbol
                            ? 'bg-blue-600 text-white'
                            : 'border border-blue-300 text-blue-700 hover:bg-blue-50'
                        } ${eventCount === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={() => setSelectedStock(symbol)}
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
                onNewsClick={openNewsModal}
                newsDisabled={false}
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* 뉴스 모달 */}
      <NewsModal
        isVisible={showNewsModal}
        onClose={closeNewsModal}
        selectedStock={selectedStock}
        currentEvent={currentNewsEvent}
        newsData={newsData}
        newsLoading={newsLoading}
      />
    </>
  );
};

export default StockVolatilityNews;
