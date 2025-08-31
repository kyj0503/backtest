import { useState, useEffect } from 'react';
import { Container, Row, Col, Badge, Spinner } from 'react-bootstrap';
import { backtestApiService } from '../services/api';

interface ServerInfo {
  version: string;
  git: {
    commit: string;
    branch: string;
  };
  start_time: string;
  start_time_kst: string;
  current_time: string;
  current_time_kst: string;
  timezone: {
    server: string;
    display: string;
  };
  uptime_seconds: number;
  uptime_human: string;
  environment: string;
  python_version: string;
  platform: string;
  hostname: string;
}

const ServerStatusFooter = () => {
  const [backendInfo, setBackendInfo] = useState<ServerInfo | null>(null);
  const [frontendStartTime] = useState<Date>(new Date());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 프론트엔드 버전 정보
  const frontendVersion = "1.0.0";

  const fetchServerInfo = async () => {
    try {
      setLoading(true);
      const info = await backtestApiService.getServerInfo();
      setBackendInfo(info);
      setError(null);
    } catch (err) {
      setError('서버 정보를 가져올 수 없습니다');
      console.error('Failed to fetch server info:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServerInfo();
    
    // 60초마다 업타임 업데이트
    const interval = setInterval(fetchServerInfo, 60000);
    
    return () => clearInterval(interval);
  }, []);

  // KST 시간대로 포맷팅하는 함수
  const formatKSTTime = (dateInput: Date | string): string => {
    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
    return date.toLocaleString('ko-KR', {
      timeZone: 'Asia/Seoul',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}일 ${hours}시간`;
    } else if (hours > 0) {
      return `${hours}시간 ${minutes}분`;
    } else {
      return `${minutes}분`;
    }
  };

  const getFrontendUptime = (): string => {
    const now = new Date();
    const uptimeMs = now.getTime() - frontendStartTime.getTime();
    const uptimeSeconds = Math.floor(uptimeMs / 1000);
    return formatUptime(uptimeSeconds);
  };

  const getEnvironmentColor = (env: string): string => {
    switch (env.toLowerCase()) {
      case 'production':
        return 'success';
      case 'development':
        return 'warning';
      case 'staging':
        return 'info';
      default:
        return 'secondary';
    }
  };

  return (
    <footer className="bg-light border-top mt-5 py-4">
      <Container>
        <Row className="align-items-center">
          <Col md={6}>
            <div className="d-flex align-items-center">
              <h6 className="mb-0 me-3 text-muted">
                <i className="bi bi-info-circle me-1"></i>
                시스템 정보
              </h6>
              {loading && !backendInfo && (
                <Spinner animation="border" size="sm" className="me-2" />
              )}
            </div>
          </Col>
          <Col md={6} className="text-md-end">
            <small className="text-muted">
              마지막 업데이트: {formatKSTTime(new Date())}
            </small>
          </Col>
        </Row>
        
        <hr className="my-3" />
        
        <Row>
          {/* 프론트엔드 정보 */}
          <Col md={6} className="mb-3 mb-md-0">
            <div className="d-flex align-items-start">
              <div className="me-3">
                <i className="bi bi-display text-primary" style={{ fontSize: '1.5rem' }}></i>
              </div>
              <div className="flex-grow-1">
                <div className="d-flex align-items-center mb-1">
                  <h6 className="mb-0 me-2">Frontend</h6>
                  <Badge bg="primary" className="me-2">v{frontendVersion}</Badge>
                  <Badge bg="info">React + Vite</Badge>
                </div>
                <div className="text-muted small">
                  <div>업타임: {getFrontendUptime()}</div>
                  <div>시작: {formatKSTTime(frontendStartTime)} (KST)</div>
                </div>
              </div>
            </div>
          </Col>

          {/* 백엔드 정보 */}
          <Col md={6}>
            <div className="d-flex align-items-start">
              <div className="me-3">
                <i className="bi bi-server text-success" style={{ fontSize: '1.5rem' }}></i>
              </div>
              <div className="flex-grow-1">
                {error ? (
                  <div className="text-danger">
                    <h6 className="mb-1">Backend (연결 실패)</h6>
                    <small>{error}</small>
                  </div>
                ) : backendInfo ? (
                  <>
                    <div className="d-flex align-items-center mb-1">
                      <h6 className="mb-0 me-2">Backend</h6>
                      <Badge bg="success" className="me-2">v{backendInfo.version}</Badge>
                      <Badge bg={getEnvironmentColor(backendInfo.environment)}>
                        {backendInfo.environment}
                      </Badge>
                    </div>
                    <div className="text-muted small">
                      <div>업타임: {formatUptime(backendInfo.uptime_seconds)}</div>
                      <div>시작: {formatKSTTime(backendInfo.start_time_kst)} (KST)</div>
                      <div>Python: {backendInfo.python_version}</div>
                      {backendInfo.git.commit !== 'unknown' && (
                        <div>
                          <i className="bi bi-git me-1"></i>
                          {backendInfo.git.branch}@{backendInfo.git.commit}
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-muted">
                    <h6 className="mb-1">Backend</h6>
                    <small>로딩 중...</small>
                  </div>
                )}
              </div>
            </div>
          </Col>
        </Row>
        
        <hr className="my-3" />
        
        <Row>
          <Col className="text-center">
            <small className="text-muted">
              © 2024 백테스팅 플랫폼 | 
              <a href="#" className="text-decoration-none ms-1 me-1">API 문서</a> | 
              <a href="#" className="text-decoration-none ms-1 me-1">GitHub</a> | 
              <a href="#" className="text-decoration-none ms-1">문의</a>
            </small>
          </Col>
        </Row>
      </Container>
    </footer>
  );
};

export default ServerStatusFooter;
