import { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import UnifiedBacktestForm from './components/UnifiedBacktestForm';
import UnifiedBacktestResults from './components/UnifiedBacktestResults';
import { UnifiedBacktestRequest } from './types/api';

function App() {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPortfolio, setIsPortfolio] = useState(false);

  const handleSubmit = async (request: UnifiedBacktestRequest) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setIsPortfolio(request.portfolio.length > 1);

    // 환경에 따른 API Base URL 설정
    const getApiBaseUrl = () => {
      if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        // 프로덕션 환경 (도메인 사용)
        if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
          return `${protocol}//backtest-be.yeonjae.kr`;
        }
      }
      // 개발 환경
      return 'http://localhost:8001';
    };

    const apiBaseUrl = getApiBaseUrl();

    try {
      let response;
      
      if (request.portfolio.length === 1) {
        // 단일 종목 - 기존 chart-data API 사용
        const singleStockRequest = {
          ticker: request.portfolio[0].symbol,
          start_date: request.start_date,
          end_date: request.end_date,
          initial_cash: request.portfolio[0].amount,
          strategy: request.strategy,
          strategy_params: request.strategy_params || {}
        };

        response = await fetch(`${apiBaseUrl}/api/v1/backtest/chart-data`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(singleStockRequest),
        });
      } else {
        // 포트폴리오 - 포트폴리오 API 사용 (백엔드 스키마에 맞춰 요청 구성)
        const portfolioRequest = {
          portfolio: request.portfolio,
          start_date: request.start_date,
          end_date: request.end_date,
          commission: request.commission || 0.002,  // 사용자 설정 또는 기본 수수료
          rebalance_frequency: request.rebalance_frequency || 'monthly',  // 사용자 설정 또는 기본 리밸런싱
          strategy: request.strategy,
          strategy_params: request.strategy_params || {}
        };
        
        response = await fetch(`${apiBaseUrl}/api/v1/backtest/portfolio`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(portfolioRequest),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // 포트폴리오 API 응답 처리
      if (request.portfolio.length > 1 && result.status === 'success' && result.data) {
        setResults(result.data);
      } else {
        setResults(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <Container fluid className="py-4">
        <Row className="justify-content-center">
          <Col xl={10}>
            {/* 헤더 */}
            <div className="text-center mb-5">
              <h1 className="display-4 fw-bold text-primary mb-3">
                📈 백테스팅 플랫폼
              </h1>
              <p className="lead text-muted">
                단일 종목부터 포트폴리오까지, 다양한 투자 전략을 검증해보세요
              </p>
            </div>

            {/* 백테스트 폼 */}
            <Row className="mb-5">
              <Col>
                <UnifiedBacktestForm 
                  onSubmit={handleSubmit} 
                  loading={loading} 
                />
              </Col>
            </Row>

            {/* 로딩 상태 */}
            {loading && (
              <div className="text-center my-5">
                <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
                <h4 className="mt-3">백테스트 실행 중...</h4>
                <p className="text-muted">데이터를 분석하고 있습니다</p>
              </div>
            )}

            {/* 에러 메시지 */}
            {error && (
              <Alert variant="danger">
                <strong>오류:</strong> {error}
              </Alert>
            )}

            {/* 결과 표시 */}
            {results && !loading && (
              <Row>
                <Col>
                  <UnifiedBacktestResults 
                    data={results} 
                    isPortfolio={isPortfolio} 
                  />
                </Col>
              </Row>
            )}

            {/* 초기 상태 메시지 */}
            {!results && !loading && !error && (
              <div className="text-center my-5">
                <div style={{ fontSize: '4rem' }}>📊</div>
                <h3 className="mt-3">백테스팅을 시작하세요</h3>
                <p className="text-muted">
                  단일 종목 또는 포트폴리오를 선택하고 투자 전략을 설정한 후 백테스트를 실행해보세요.
                </p>
              </div>
            )}
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default App;