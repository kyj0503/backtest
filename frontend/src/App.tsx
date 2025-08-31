import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import UnifiedBacktestForm from './components/UnifiedBacktestForm';
import UnifiedBacktestResults from './components/UnifiedBacktestResults';
import ErrorBoundary from './components/ErrorBoundary';
import ServerStatus from './components/ServerStatus';
import { useBacktest } from './hooks/useBacktest';

function App() {
  const { results, loading, error, errorType, errorId, isPortfolio, runBacktest, clearError } = useBacktest();

  return (
    <ErrorBoundary>
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
                    onSubmit={runBacktest} 
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
              <Alert variant="danger" dismissible onClose={clearError}>
                <div className="d-flex align-items-start">
                  <div className="flex-grow-1">
                    <Alert.Heading className="h6 mb-2">
                      <i className="bi bi-exclamation-triangle-fill me-2"></i>
                      {errorType === 'network' ? '네트워크 오류' :
                       errorType === 'data_not_found' ? '데이터 없음' :
                       errorType === 'validation' ? '입력값 오류' :
                       errorType === 'rate_limit' ? '요청 제한 초과' :
                       '오류가 발생했습니다'}
                    </Alert.Heading>
                    <p className="mb-1">{error}</p>
                    {errorId && (
                      <small className="text-muted">오류 ID: {errorId}</small>
                    )}
                  </div>
                </div>
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
              <>
                <div className="text-center my-5">
                  <div style={{ fontSize: '4rem' }}>📊</div>
                  <h3 className="mt-3">백테스팅을 시작하세요</h3>
                  <p className="text-muted">
                    단일 종목 또는 포트폴리오를 선택하고 투자 전략을 설정한 후 백테스트를 실행해보세요.
                  </p>
                </div>

                {/* 기능 소개 섹션 */}
                <Row className="my-5">
                  <Col md={4} className="mb-4">
                    <div className="text-center">
                      <div className="bg-primary bg-opacity-10 rounded-circle mx-auto mb-3 d-flex align-items-center justify-content-center" 
                           style={{ width: '80px', height: '80px' }}>
                        <i className="bi bi-graph-up text-primary" style={{ fontSize: '2rem' }}></i>
                      </div>
                      <h5>다양한 전략</h5>
                      <p className="text-muted small">
                        Buy & Hold, SMA Crossover, RSI, Bollinger Bands, MACD 등 
                        검증된 투자 전략을 제공합니다.
                      </p>
                    </div>
                  </Col>
                  <Col md={4} className="mb-4">
                    <div className="text-center">
                      <div className="bg-success bg-opacity-10 rounded-circle mx-auto mb-3 d-flex align-items-center justify-content-center" 
                           style={{ width: '80px', height: '80px' }}>
                        <i className="bi bi-pie-chart text-success" style={{ fontSize: '2rem' }}></i>
                      </div>
                      <h5>포트폴리오 분석</h5>
                      <p className="text-muted small">
                        여러 종목으로 구성된 포트폴리오의 성과를 분석하고 
                        리밸런싱 전략을 테스트할 수 있습니다.
                      </p>
                    </div>
                  </Col>
                  <Col md={4} className="mb-4">
                    <div className="text-center">
                      <div className="bg-info bg-opacity-10 rounded-circle mx-auto mb-3 d-flex align-items-center justify-content-center" 
                           style={{ width: '80px', height: '80px' }}>
                        <i className="bi bi-bar-chart text-info" style={{ fontSize: '2rem' }}></i>
                      </div>
                      <h5>실시간 시각화</h5>
                      <p className="text-muted small">
                        인터랙티브 차트로 백테스트 결과를 직관적으로 
                        확인하고 분석할 수 있습니다.
                      </p>
                    </div>
                  </Col>
                </Row>

                {/* 지원 기능 */}
                <div className="bg-light rounded p-4 my-5">
                  <h4 className="text-center mb-4">💡 주요 기능</h4>
                  <Row>
                    <Col md={6}>
                      <ul className="list-unstyled">
                        <li className="mb-2">
                          <i className="bi bi-check-circle-fill text-success me-2"></i>
                          실시간 주가 데이터 (Yahoo Finance)
                        </li>
                        <li className="mb-2">
                          <i className="bi bi-check-circle-fill text-success me-2"></i>
                          커스터마이징 가능한 전략 파라미터
                        </li>
                        <li className="mb-2">
                          <i className="bi bi-check-circle-fill text-success me-2"></i>
                          상세한 성과 지표 (샤프 비율, 최대 낙폭 등)
                        </li>
                      </ul>
                    </Col>
                    <Col md={6}>
                      <ul className="list-unstyled">
                        <li className="mb-2">
                          <i className="bi bi-check-circle-fill text-success me-2"></i>
                          거래 기록 및 진입/청산 포인트 표시
                        </li>
                        <li className="mb-2">
                          <i className="bi bi-check-circle-fill text-success me-2"></i>
                          포트폴리오 리밸런싱 시뮬레이션
                        </li>
                        <li className="mb-2">
                          <i className="bi bi-check-circle-fill text-success me-2"></i>
                          다양한 차트 타입 (캔들스틱, 라인, 거래량)
                        </li>
                      </ul>
                    </Col>
                  </Row>
                </div>

                {/* 사용법 안내 */}
                <div className="my-5">
                  <h4 className="text-center mb-4">🚀 사용법</h4>
                  <Row>
                    <Col lg={8} className="mx-auto">
                      <div className="d-flex align-items-start mb-3">
                        <div className="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" 
                             style={{ width: '30px', height: '30px', fontSize: '0.9rem' }}>
                          1
                        </div>
                        <div>
                          <h6>종목 또는 포트폴리오 선택</h6>
                          <p className="text-muted small mb-0">단일 종목 백테스트 또는 여러 종목으로 구성된 포트폴리오를 선택하세요.</p>
                        </div>
                      </div>
                      <div className="d-flex align-items-start mb-3">
                        <div className="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" 
                             style={{ width: '30px', height: '30px', fontSize: '0.9rem' }}>
                          2
                        </div>
                        <div>
                          <h6>기간 및 전략 설정</h6>
                          <p className="text-muted small mb-0">백테스트 기간을 설정하고 원하는 투자 전략과 파라미터를 선택하세요.</p>
                        </div>
                      </div>
                      <div className="d-flex align-items-start mb-3">
                        <div className="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" 
                             style={{ width: '30px', height: '30px', fontSize: '0.9rem' }}>
                          3
                        </div>
                        <div>
                          <h6>백테스트 실행 및 결과 분석</h6>
                          <p className="text-muted small mb-0">백테스트를 실행하고 차트와 통계를 통해 결과를 분석하세요.</p>
                        </div>
                      </div>
                    </Col>
                  </Row>
                </div>
              </>
            )}
          </Col>
        </Row>
      </Container>
      
      {/* 서버 상태 정보 - 푸터 */}
      <ServerStatus />
    </div>
    </ErrorBoundary>
  );
}

export default App;