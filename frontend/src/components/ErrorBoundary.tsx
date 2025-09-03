import { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Button, Container, Row, Col } from 'react-bootstrap';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
}

/**
 * React Error Boundary 컴포넌트
 * 
 * React 컴포넌트 트리에서 발생하는 JavaScript 오류를 포착하고
 * 사용자에게 친화적인 오류 메시지를 표시합니다.
 * 
 * 사용법:
 * ```tsx
 * <ErrorBoundary>
 *   <SomeComponent />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      errorId: this.generateErrorId()
    };
  }

  private generateErrorId(): string {
    return Math.random().toString(36).substr(2, 8);
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // 다음 렌더링에서 폴백 UI가 보이도록 상태를 업데이트합니다.
    return {
      hasError: true,
      error,
      errorId: Math.random().toString(36).substr(2, 8)
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 에러 로깅 서비스에 에러를 기록할 수 있습니다.
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
      errorId: this.generateErrorId()
    });

    // 실제 운영 환경에서는 Sentry, LogRocket 등의 서비스로 전송
    if (import.meta.env.PROD) {
      // 예시: 에러 리포팅 서비스로 전송
      // errorReportingService.captureException(error, {
      //   extra: errorInfo,
      //   tags: { errorId: this.state.errorId }
      // });
    }
  }

  private handleReload = (): void => {
    window.location.reload();
  };

  private handleRestart = (): void => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: this.generateErrorId()
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 커스텀 폴백 UI가 제공된 경우 사용
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 기본 에러 UI
      return (
        <Container className="mt-5">
          <Row className="justify-content-center">
            <Col md={8}>
              <Alert variant="danger">
                <Alert.Heading>
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  오류가 발생했습니다
                </Alert.Heading>
                <p>
                  예상치 못한 오류로 인해 애플리케이션이 정상적으로 동작하지 않습니다.
                  페이지를 새로고침하거나 다시 시도해주세요.
                </p>
                
                {import.meta.env.DEV && this.state.error && (
                  <details className="mt-3">
                    <summary className="text-muted">개발자 정보 (클릭하여 펼치기)</summary>
                    <div className="mt-2 p-3 bg-light rounded">
                      <h6>오류 메시지:</h6>
                      <code className="text-danger">{this.state.error.message}</code>
                      
                      <h6 className="mt-3">스택 트레이스:</h6>
                      <pre className="text-muted small">
                        {this.state.error.stack}
                      </pre>
                      
                      {this.state.errorInfo && (
                        <>
                          <h6 className="mt-3">컴포넌트 스택:</h6>
                          <pre className="text-muted small">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </>
                      )}
                    </div>
                  </details>
                )}
                
                <hr />
                <div className="d-flex gap-2">
                  <Button variant="outline-danger" onClick={this.handleRestart}>
                    다시 시도
                  </Button>
                  <Button variant="danger" onClick={this.handleReload}>
                    페이지 새로고침
                  </Button>
                </div>
                
                <div className="mt-3 text-muted small">
                  오류 ID: {this.state.errorId}
                </div>
              </Alert>
            </Col>
          </Row>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
