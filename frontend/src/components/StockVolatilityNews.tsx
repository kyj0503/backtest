import React, { useState, useEffect } from "react";
import { Card, Row, Col, Badge, Button, Spinner, Alert, Modal, ListGroup } from "react-bootstrap";
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

// 티커 심볼을 한국어 기업명으로 매핑
const TICKER_TO_COMPANY_NAME: { [key: string]: string } = {
  'AAPL': '애플',
  'GOOGL': '구글',
  'GOOGLE': '구글', 
  'MSFT': '마이크로소프트',
  'AMZN': '아마존',
  'TSLA': '테슬라',
  'META': '메타',
  'NVDA': '엔비디아',
  'NFLX': '넷플릭스',
  'ORCL': '오라클',
  'CRM': '세일즈포스',
  'ADBE': '어도비',
  'INTC': '인텔',
  'IBM': 'IBM',
  'CSCO': '시스코',
  'PYPL': '페이팔',
  'UBER': '우버',
  'SNOW': '스노우플레이크',
  'SQ': '스퀘어',
  'ZOOM': '줌',
  'SPOT': '스포티파이',
  'TWTR': '트위터',
  'SNAP': '스냅챗',
  'PINS': '핀터레스트',
  'SHOP': '쇼피파이',
  'ROKU': '로쿠',
  'DOCU': '도큐사인',
  'ZM': '줌',
  'PLTR': '팔란티어',
  'RBLX': '로블록스'
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
      const response = await backtestApiService.getNaverNews(ticker, date, 10);
      if (response.status === 'success' && response.data && response.data.news_list) {
        setNewsData(response.data.news_list);
      } else {
        setNewsData([]);
      }
      setShowNewsModal(true);
    } catch (error) {
      console.error('뉴스 조회 실패:', error);
      setNewsData([]);
      setShowNewsModal(true);
    } finally {
      setNewsLoading(false);
    }
  };

  const openNaverNews = (companyName: string, date: string, event: VolatilityEvent) => {
    // 네이버 뉴스 API를 사용하여 뉴스 조회
    fetchNewsForEvent(selectedStock, date, event);
  };

  if (validSymbols.length === 0) {
    return (
      <Card className={className}>
        <Card.Header>
          <h5 className="mb-0">📰 주가 급등/급락 뉴스</h5>
        </Card.Header>
        <Card.Body className="text-center">
          <p className="text-muted">분석할 주식 종목이 없습니다.</p>
        </Card.Body>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className={className}>
        <Card.Header>
          <h5 className="mb-0">📰 주가 급등/급락 뉴스</h5>
        </Card.Header>
        <Card.Body className="text-center">
          <Spinner animation="border" size="sm" className="me-2" />
          <span>주가 변동성 분석 중...</span>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <Card.Header>
          <h5 className="mb-0">📰 주가 급등/급락 뉴스</h5>
        </Card.Header>
        <Card.Body>
          <Alert variant="danger">{error}</Alert>
        </Card.Body>
      </Card>
    );
  }

  const selectedEvents = volatilityData[selectedStock] || [];
  const hasSignificantEvents = Object.values(volatilityData).some(events => events.length > 0);

  return (
    <Card className={className}>
      <Card.Header>
        <h5 className="mb-0">📰 주가 급등/급락 뉴스 (5% 이상 변동일)</h5>
      </Card.Header>
      <Card.Body>
        {!hasSignificantEvents ? (
          <div className="text-center">
            <p className="text-muted">해당 기간 중 5% 이상 급등/급락한 날이 없습니다.</p>
          </div>
        ) : (
          <>
            {/* 종목 선택 버튼들 */}
            <Row className="mb-3">
              <Col>
                <div className="d-flex flex-wrap gap-2">
                  {validSymbols.map(symbol => {
                    const eventCount = volatilityData[symbol]?.length || 0;
                    return (
                      <Button
                        key={symbol}
                        variant={selectedStock === symbol ? "primary" : "outline-primary"}
                        size="sm"
                        onClick={() => handleStockSelect(symbol)}
                        disabled={eventCount === 0}
                      >
                        {symbol} 
                        {eventCount > 0 && (
                          <Badge bg="secondary" className="ms-1">{eventCount}</Badge>
                        )}
                      </Button>
                    );
                  })}
                </div>
              </Col>
            </Row>

            {/* 선택된 종목의 변동성 이벤트 */}
            {selectedStock && selectedEvents.length > 0 && (
              <div>
                <h6 className="mb-3">
                  {getCompanyName(selectedStock)} ({selectedStock}) 주가 급변동일
                </h6>
                <Row>
                  {selectedEvents.map((event, index) => (
                    <Col md={6} lg={4} key={index} className="mb-3">
                      <Card className="h-100 border-start border-4" 
                            style={{ borderStartColor: event.daily_return > 0 ? '#dc3545' : '#198754' }}>
                        <Card.Body className="p-3">
                          <div className="d-flex justify-content-between align-items-start mb-2">
                            <Badge 
                              bg={event.daily_return > 0 ? "danger" : "success"}
                              className="mb-1"
                            >
                              {event.event_type}
                            </Badge>
                            <small className="text-muted">{event.date}</small>
                          </div>
                          
                          <h6 className={`mb-1 ${event.daily_return > 0 ? 'text-danger' : 'text-success'}`}>
                            {formatPercent(event.daily_return)}
                          </h6>
                          
                          <div className="small text-muted mb-2">
                            <div>종가: {formatPrice(event.close_price)}</div>
                            <div>거래량: {event.volume.toLocaleString()}</div>
                          </div>
                          
                          <Button
                            variant="outline-primary"
                            size="sm"
                            className="w-100"
                            disabled={newsLoading}
                            onClick={() => openNaverNews(getCompanyName(selectedStock), event.date, event)}
                          >
                            {newsLoading ? (
                              <>
                                <Spinner size="sm" className="me-2" />
                                뉴스 로딩 중...
                              </>
                            ) : (
                              '🔍 해당일 뉴스 보기'
                            )}
                          </Button>
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>
            )}
          </>
        )}
      </Card.Body>

      {/* 뉴스 모달 */}
      {showNewsModal && (
        <div 
          className="modal fade show" 
          style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowNewsModal(false);
            }
          }}
        >
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {currentNewsEvent && (
                    <>
                      {getCompanyName(selectedStock)} 뉴스 ({currentNewsEvent.date})
                      <Badge 
                        bg={currentNewsEvent.daily_return > 0 ? "danger" : "success"}
                        className="ms-2"
                      >
                        {formatPercent(currentNewsEvent.daily_return)}
                      </Badge>
                    </>
                  )}
                </h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowNewsModal(false)}
                ></button>
              </div>
              <div className="modal-body" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {newsLoading ? (
                  <div className="text-center">
                    <Spinner animation="border" />
                    <p className="mt-2">뉴스를 불러오는 중...</p>
                  </div>
                ) : newsData.length > 0 ? (
                  <div className="list-group list-group-flush">
                    {newsData.map((news, index) => (
                      <div key={index} className="list-group-item border-0 px-0">
                        <h6 
                          className="mb-1" 
                          dangerouslySetInnerHTML={{ __html: news.title }}
                        />
                        <p 
                          className="mb-1 text-muted small" 
                          dangerouslySetInnerHTML={{ __html: news.description }}
                        />
                        <div className="d-flex justify-content-between align-items-center">
                          <small className="text-muted">{news.pubDate}</small>
                          <a 
                            href={news.link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="btn btn-outline-primary btn-sm"
                          >
                            원문 보기
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center">
                    <p className="text-muted mb-3">
                      해당 날짜({currentNewsEvent?.date})의 {getCompanyName(selectedStock)} 뉴스를 찾을 수 없습니다.
                    </p>
                    <Button
                      variant="outline-primary"
                      onClick={() => {
                        const companyName = getCompanyName(selectedStock);
                        const date = currentNewsEvent?.date.replace(/-/g, '.');
                        const searchQuery = encodeURIComponent(`${companyName} 주가`);
                        const url = `https://search.naver.com/search.naver?where=news&query=${searchQuery}&sm=tab_opt&sort=1&photo=0&field=0&pd=3&ds=${date}&de=${date}`;
                        window.open(url, '_blank');
                      }}
                    >
                      네이버에서 직접 검색하기
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

export default StockVolatilityNews;
