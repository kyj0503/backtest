import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import UnifiedBacktestForm from './components/UnifiedBacktestForm';
import UnifiedBacktestResults from './components/UnifiedBacktestResults';
import { useBacktest } from './hooks/useBacktest';

function App() {
  const { results, loading, error, isPortfolio, runBacktest, clearError } = useBacktest();

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
