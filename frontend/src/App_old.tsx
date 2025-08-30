import { useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Card, Button, Spinner, Alert, Nav } from 'react-bootstrap';
import { ChartDataResponse } from './types/api';

// components
import BacktestForm from './components/BacktestForm';
import PortfolioForm from './components/PortfolioForm';
import PortfolioResults from './components/PortfolioResults';
import OHLCChart from './components/OHLCChart';
import EquityChart from './components/EquityChart';
import TradesChart from './components/TradesChart';
import StatsSummary from './components/StatsSummary';

// API 호출 함수
const fetchChartData = async (params: {
  ticker: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
  strategy: string;
  strategy_params?: any;
}): Promise<ChartDataResponse> => {
  const response = await fetch('http://localhost:8001/api/v1/backtest/chart-data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// 메인 App 컴포넌트
function App() {
  const [activeTab, setActiveTab] = useState('stock');
  
  // 개별 종목 백테스트 상태
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [backtestParams, setBacktestParams] = useState({
    ticker: 'AAPL',
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    initial_cash: 10000,
    strategy: 'buy_and_hold',
    strategy_params: {} as any
  });

  // 포트폴리오 백테스트 상태
  const [portfolioResults, setPortfolioResults] = useState<any>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);

  const runBacktest = async (params = backtestParams) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchChartData(params);
      setChartData(data);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  const handlePortfolioSubmit = async (data: any) => {
    setPortfolioLoading(true);
    setPortfolioError(null);
    setPortfolioResults(null);

    try {
      const response = await fetch('http://localhost:8001/api/v1/backtest/portfolio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      // API 응답이 { status: 'success', data: {...} } 형태인 경우 data 추출
      if (result.status === 'success' && result.data) {
        setPortfolioResults(result.data);
      } else {
        setPortfolioResults(result);
      }
    } catch (err) {
      setPortfolioError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setPortfolioLoading(false);
    }
  };

  useEffect(() => { 
    if (activeTab === 'stock') {
      runBacktest(); 
    }
  }, [activeTab]);

  if (error && activeTab === 'stock') {
    return (
      <Container className="mt-4">
        <Alert variant="danger">
          <Alert.Heading>오류 발생</Alert.Heading>
          <p>{error}</p>
          <Button variant="outline-danger" onClick={() => setError(null)}>다시 시도</Button>
        </Alert>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4" style={{ backgroundColor: '#f8f9fa' }}>
      <Row className="mb-4">
        <Col>
          <div className="text-center">
            <h1 className="display-4 fw-bold text-primary mb-3">🔬 백테스팅 분석 도구</h1>
            <p className="lead text-muted">과거 데이터로 투자 전략의 성과를 분석해보세요</p>
          </div>
        </Col>
      </Row>

      {/* 탭 네비게이션 */}
      <Card className="mb-4 shadow">
        <Card.Header className="bg-dark text-white">
          <Nav variant="tabs" defaultActiveKey="stock" className="border-0">
            <Nav.Item>
              <Nav.Link 
                eventKey="stock" 
                onClick={() => setActiveTab('stock')}
                active={activeTab === 'stock'}
                className={activeTab === 'stock' ? 'text-primary bg-white' : 'text-white'}
              >
                📈 개별 종목 백테스트
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link 
                eventKey="portfolio" 
                onClick={() => setActiveTab('portfolio')}
                active={activeTab === 'portfolio'}
                className={activeTab === 'portfolio' ? 'text-primary bg-white' : 'text-white'}
              >
                📊 포트폴리오 백테스트
              </Nav.Link>
            </Nav.Item>
          </Nav>
        </Card.Header>
        
        <Card.Body>
          {activeTab === 'stock' && (
            <>
              <h5 className="mb-3">⚙️ 백테스트 설정</h5>
              <BacktestForm 
                backtestParams={backtestParams} 
                setBacktestParams={setBacktestParams} 
                runBacktest={runBacktest} 
                loading={loading} 
              />
            </>
          )}
          
          {activeTab === 'portfolio' && (
            <>
              <h5 className="mb-3">⚙️ 포트폴리오 설정</h5>
              <PortfolioForm onSubmit={handlePortfolioSubmit} isLoading={portfolioLoading} />
            </>
          )}
        </Card.Body>
      </Card>

      {/* 개별 종목 백테스트 결과 */}
      {activeTab === 'stock' && (
        <>
          {loading && (
            <div className="text-center my-5">
              <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
              <h4 className="mt-3">백테스트 실행 중...</h4>
              <p className="text-muted">{backtestParams.ticker} 데이터를 분석하고 있습니다</p>
            </div>
          )}

          {chartData && !loading && (
            <>
              <Card className="mb-4 bg-light">
                <Card.Body className="text-center">
                  <h2 className="text-primary mb-2">📊 {chartData.ticker} - {chartData.strategy} 백테스트 결과</h2>
                  <p className="text-muted mb-0">{chartData.start_date} ~ {chartData.end_date} | 초기 투자금: ${backtestParams.initial_cash.toLocaleString()}</p>
                </Card.Body>
              </Card>

              <StatsSummary stats={chartData.summary_stats || {}} />

              <Row>
                <Col lg={12}>
                  <OHLCChart 
                    data={chartData.ohlc_data || []} 
                    indicators={chartData.indicators || []} 
                    trades={chartData.trade_markers || []} 
                  />
                </Col>
                <Col lg={12}>
                  <EquityChart data={chartData.equity_data || []} />
                </Col>
                {chartData.trade_markers && chartData.trade_markers.length > 0 && (
                  <Col lg={12}><TradesChart trades={chartData.trade_markers} /></Col>
                )}
              </Row>
            </>
          )}

          {!chartData && !loading && !error && (
            <div className="text-center my-5">
              <div style={{ fontSize: '4rem' }}>📈</div>
              <h3 className="mt-3">백테스팅을 시작하세요</h3>
              <p className="text-muted">위의 폼에서 티커와 기간을 설정한 후 백테스트를 실행해보세요.</p>
            </div>
          )}
        </>
      )}

      {/* 포트폴리오 백테스트 결과 */}
      {activeTab === 'portfolio' && (
        <>
          {portfolioLoading && (
            <div className="text-center my-5">
              <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
              <h4 className="mt-3">포트폴리오 백테스트 실행 중...</h4>
              <p className="text-muted">포트폴리오 성과를 분석하고 있습니다</p>
            </div>
          )}

          {portfolioError && (
            <Alert variant="danger">
              <strong>오류:</strong> {portfolioError}
            </Alert>
          )}

          {portfolioResults && !portfolioLoading && (
            <>
              <Card className="mb-4 bg-light">
                <Card.Body className="text-center">
                  <h2 className="text-primary mb-2">📊 포트폴리오 백테스트 결과</h2>
                  <p className="text-muted mb-0">{portfolioResults.start_date} ~ {portfolioResults.end_date} | 초기 투자금: ${portfolioResults.initial_cash?.toLocaleString()}</p>
                </Card.Body>
              </Card>

              <PortfolioResults result={portfolioResults} />
            </>
          )}

          {!portfolioResults && !portfolioLoading && !portfolioError && (
            <div className="text-center my-5">
              <div style={{ fontSize: '4rem' }}>📊</div>
              <h3 className="mt-3">포트폴리오 백테스팅을 시작하세요</h3>
              <p className="text-muted">위의 폼에서 종목들과 비중을 설정한 후 백테스트를 실행해보세요.</p>
            </div>
          )}
        </>
      )}
    </Container>
  );
}

export default App;