import React from 'react';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import UnifiedBacktestForm from '../components/UnifiedBacktestForm';
import UnifiedBacktestResults from '../components/UnifiedBacktestResults';
import { useBacktest } from '../hooks/useBacktest';

const BacktestPage: React.FC = () => {
  const { results, loading, error, errorType, errorId, isPortfolio, runBacktest, clearError } = useBacktest();

  return (
    <Container fluid className="py-4">
      <Row className="justify-content-center">
        <Col xl={10}>
          {/* 페이지 헤더 */}
          <div className="text-center mb-4">
            <h2 className="fw-bold text-primary mb-2">
              📊 백테스트 실행
            </h2>
            <p className="text-muted">
              투자 전략을 설정하고 백테스트를 실행해보세요
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

          {/* 초기 상태 안내 */}
          {!results && !loading && !error && (
            <div className="text-center my-5">
              <div style={{ fontSize: '3rem' }}>🎯</div>
              <h4 className="mt-3">백테스트 설정을 완료하고 실행 버튼을 눌러주세요</h4>
              <p className="text-muted">
                포트폴리오 구성, 투자 전략, 백테스트 기간을 설정한 후<br />
                <strong>'백테스트 실행'</strong> 버튼을 클릭하면 결과를 확인할 수 있습니다.
              </p>
            </div>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default BacktestPage;
