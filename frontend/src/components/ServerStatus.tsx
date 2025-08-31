import { useState, useEffect } from 'react';
import { Container, Row, Col, Badge, Spinner } from 'react-bootstrap';
import { backtestApiService } from '../services/api';

interface ServerInfo {
  version: string;
  git: {
    commit: string;
    branch: string;
    commit_full: string;
  };
  docker: {
    build_number: string;
    image_tag: string;
    image_name: string;
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 프론트엔드 버전 정보 - 빌드 시점에 주입됨 또는 환경변수에서 가져옴
  const frontendVersion = __APP_VERSION__ || "1.0.0-dev";
  const buildTime = __BUILD_TIME__;
  const gitCommit = __GIT_COMMIT__ || import.meta.env.VITE_GIT_COMMIT || "unknown";
  const gitBranch = __GIT_BRANCH__ || import.meta.env.VITE_GIT_BRANCH || "unknown";
  const buildNumber = __BUILD_NUMBER__ || import.meta.env.VITE_BUILD_NUMBER || "unknown";

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
                  <Badge bg="primary">v{frontendVersion}</Badge>
                </div>
                <div className="text-muted small">
                  {buildNumber !== 'unknown' && buildNumber !== 'dev-local' && (
                    <div>
                      <i className="bi bi-box me-1"></i>
                      Build #{buildNumber}
                    </div>
                  )}
                  {gitCommit !== 'unknown' && gitCommit !== 'dev-local' && gitCommit.length > 4 && (
                    <div>
                      <i className="bi bi-git me-1"></i>
                      {gitBranch}@{gitCommit.substring(0, 8)}
                    </div>
                  )}
                  <div>현재: {formatKSTTime(new Date())} (KST)</div>
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
                      <Badge bg="success">v{backendInfo.version}</Badge>
                    </div>
                    <div className="text-muted small">
                      <div>업타임: {formatUptime(backendInfo.uptime_seconds)}</div>
                      <div>시작: {formatKSTTime(backendInfo.start_time_kst)} (KST)</div>
                      <div>Python: {backendInfo.python_version}</div>
                      {backendInfo.docker.build_number !== 'unknown' && (
                        <div>
                          <i className="bi bi-box me-1"></i>
                          Build #{backendInfo.docker.build_number}
                        </div>
                      )}
                      {backendInfo.git.commit !== 'unknown' && backendInfo.git.commit !== 'dev-loca' && backendInfo.git.commit.length > 4 && (
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
