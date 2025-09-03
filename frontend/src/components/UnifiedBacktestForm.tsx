import React, { useState, useEffect } from 'react';
import { Form, Row, Col, Button, Table, Card, Container, Alert } from 'react-bootstrap';
import { UnifiedBacktestRequest } from '../types/api';
import { PREDEFINED_STOCKS, STRATEGY_CONFIGS, ASSET_TYPES, AssetType } from '../constants/strategies';

interface Stock {
  symbol: string;
  amount: number;
  investmentType: 'lump_sum' | 'dca';
  dcaPeriods?: number;
  assetType?: AssetType; // 자산 타입 추가
}

interface UnifiedBacktestFormProps {
  onSubmit: (request: UnifiedBacktestRequest) => Promise<void>;
  loading?: boolean;
}

const UnifiedBacktestForm: React.FC<UnifiedBacktestFormProps> = ({ onSubmit, loading = false }) => {
  const [portfolio, setPortfolio] = useState<Stock[]>([{ 
    symbol: '', 
    amount: 10000, 
    investmentType: 'lump_sum',
    dcaPeriods: 12 
  }]);
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [selectedStrategy, setSelectedStrategy] = useState('buy_and_hold');
  const [strategyParams, setStrategyParams] = useState<Record<string, any>>({});
  const [rebalanceFrequency, setRebalanceFrequency] = useState('monthly');
  const [commission, setCommission] = useState(0.2); // 퍼센트 형태로 변경 (0.2%)
  const [errors, setErrors] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 전략 변경 시 기본값 설정
  useEffect(() => {
    const config = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (config && config.parameters) {
      const defaultParams: Record<string, any> = {};
      Object.entries(config.parameters).forEach(([key, param]) => {
        defaultParams[key] = (param as any).default;
      });
      setStrategyParams(defaultParams);
    } else {
      setStrategyParams({});
    }
  }, [selectedStrategy]);

  const validatePortfolio = (): string[] => {
    const validationErrors: string[] = [];

    if (portfolio.length === 0) {
      validationErrors.push('포트폴리오는 최소 1개 종목을 포함해야 합니다.');
      return validationErrors;
    }

    if (portfolio.length > 10) {
      validationErrors.push('포트폴리오는 최대 10개 종목까지 포함할 수 있습니다.');
    }

    // 빈 심볼 검사 (CUSTOM 선택 후 미입력 제외)
    const emptySymbols = portfolio.filter(stock => !stock.symbol.trim() || stock.symbol === 'CUSTOM');
    if (emptySymbols.length > 0) {
      validationErrors.push('모든 종목 심볼을 입력해주세요.');
    }

    // 투자 금액 검사
    const invalidAmounts = portfolio.filter(stock => stock.amount <= 0);
    if (invalidAmounts.length > 0) {
      validationErrors.push('모든 투자 금액은 0보다 커야 합니다.');
    }

    // DCA 기간 검사
    const invalidDCA = portfolio.filter(stock => 
      stock.investmentType === 'dca' && (!stock.dcaPeriods || stock.dcaPeriods < 1 || stock.dcaPeriods > 60)
    );
    if (invalidDCA.length > 0) {
      validationErrors.push('DCA 기간은 1개월 이상 60개월 이하여야 합니다.');
    }

    return validationErrors;
  };

  const addStock = () => {
    setPortfolio([...portfolio, { 
      symbol: '', 
      amount: 10000, 
      investmentType: 'lump_sum',
      dcaPeriods: 12,
      assetType: ASSET_TYPES.STOCK
    }]);
  };

  const addCash = () => {
    setPortfolio([...portfolio, { 
      symbol: 'CASH', 
      amount: 10000, 
      investmentType: 'lump_sum',
      dcaPeriods: 12,
      assetType: ASSET_TYPES.CASH
    }]);
  };

  const removeStock = (index: number) => {
    const newPortfolio = portfolio.filter((_, i) => i !== index);
    setPortfolio(newPortfolio);
  };

  const updateStock = (index: number, field: keyof Stock, value: string | number) => {
    const newPortfolio = [...portfolio];
    if (field === 'symbol') {
      newPortfolio[index].symbol = (value as string).toUpperCase();
    } else if (field === 'investmentType') {
      newPortfolio[index].investmentType = value as 'lump_sum' | 'dca';
    } else {
      newPortfolio[index][field] = Number(value);
    }
    setPortfolio(newPortfolio);
  };

  const updateStrategyParam = (key: string, value: any) => {
    setStrategyParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const generateStrategyParams = () => {
    const config = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (!config || !config.parameters) return {};

    const params: Record<string, any> = {};
    Object.entries(config.parameters).forEach(([key, paramConfig]) => {
      const value = strategyParams[key];
      if (value !== undefined) {
        params[key] = (paramConfig as any).type === 'int' ? parseInt(value) : value;
      }
    });
    return params;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);

    const validationErrors = validatePortfolio();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      setIsLoading(false);
      return;
    }

    try {
      // 포트폴리오 데이터 준비 (백엔드 API 스키마에 맞춤)
      const portfolioData = portfolio.map(stock => ({
        symbol: stock.symbol.toUpperCase(),
        amount: stock.amount,
        investment_type: stock.investmentType,
        dca_periods: stock.dcaPeriods || 12
      }));

      const params = generateStrategyParams();
      console.log('Portfolio data being sent:', portfolioData);
      console.log('Strategy params being sent:', params);

      await onSubmit({
        portfolio: portfolioData,
        start_date: startDate,
        end_date: endDate,
        strategy: selectedStrategy || 'buy_and_hold',
        strategy_params: params,
        commission: commission / 100, // 퍼센트를 소수점으로 변환 (0.2 -> 0.002)
        rebalance_frequency: rebalanceFrequency
      });
    } catch (error) {
      console.error('백테스트 실행 중 오류:', error);
      const errorMessage = error instanceof Error ? error.message : '백테스트 실행 중 오류가 발생했습니다.';
      setErrors([errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderStrategyParams = () => {
    const config = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (!config || !config.parameters) return null;

    return (
      <Row className="mb-4">
        <Col>
          <h5>전략 파라미터</h5>
          <Row>
            {Object.entries(config.parameters).map(([key, paramConfig]) => {
              const param = paramConfig as any;
              return (
                <Col md={6} key={key}>
                  <Form.Group className="mb-3">
                    <Form.Label>
                      {key === 'short_window' ? '단기 이동평균 기간' :
                       key === 'long_window' ? '장기 이동평균 기간' :
                       key === 'rsi_period' ? 'RSI 기간' :
                       key === 'rsi_oversold' ? 'RSI 과매도 기준' :
                       key === 'rsi_overbought' ? 'RSI 과매수 기준' : key}
                    </Form.Label>
                    <Form.Control
                      type="number"
                      value={strategyParams[key] || param.default}
                      onChange={(e) => updateStrategyParam(key, e.target.value)}
                      min={param.min}
                      max={param.max}
                    />
                    <Form.Text className="text-muted">
                      기본값: {param.default}, 범위: {param.min} - {param.max}
                    </Form.Text>
                  </Form.Group>
                </Col>
              );
            })}
          </Row>
        </Col>
      </Row>
    );
  };

  const getTotalAmount = () => {
    return portfolio.reduce((sum, stock) => sum + stock.amount, 0);
  };

  return (
    <Container>
      <Card>
        <Card.Header>
          <h4>🏦 포트폴리오 백테스트</h4>
          <p className="mb-0 text-muted">
            종목/자산별 투자 금액과 방식을 설정하여 포트폴리오 백테스트를 실행합니다.
          </p>
        </Card.Header>
        <Card.Body>
          {errors.length > 0 && (
            <Alert variant="danger">
              <Alert.Heading>⚠️ 입력 오류</Alert.Heading>
              <ul className="mb-0">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </Alert>
          )}

          <Form onSubmit={handleSubmit}>
            {/* 포트폴리오 구성 */}
            <Row className="mb-4">
              <Col>
                <h5>포트폴리오 구성</h5>
                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th>종목/자산</th>
                      <th>투자 금액 ($)</th>
                      <th>투자 방식</th>
                      <th>비중 (%)</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.map((stock, index) => (
                      <tr key={index}>
                        <td>
                          <div>
                            <Form.Select
                              value={stock.symbol || 'CUSTOM'}
                              onChange={(e) => {
                                const selectedValue = e.target.value;
                                if (selectedValue === 'CUSTOM') {
                                  updateStock(index, 'symbol', '');
                                } else {
                                  updateStock(index, 'symbol', selectedValue);
                                }
                              }}
                              className="mb-2"
                            >
                              {PREDEFINED_STOCKS.map(option => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </Form.Select>
                            {(stock.symbol === '' || !PREDEFINED_STOCKS.find(opt => opt.value === stock.symbol)) && (
                              <Form.Control
                                type="text"
                                value={stock.symbol}
                                onChange={(e) => updateStock(index, 'symbol', e.target.value)}
                                placeholder="종목 심볼 입력 (예: AAPL)"
                                maxLength={10}
                              />
                            )}
                          </div>
                        </td>
                        <td>
                          <Form.Control
                            type="number"
                            value={stock.amount}
                            onChange={(e) => updateStock(index, 'amount', e.target.value)}
                            min="100"
                            step="100"
                          />
                        </td>
                        <td>
                          <div>
                            <Form.Select
                              value={stock.investmentType}
                              onChange={(e) => updateStock(index, 'investmentType', e.target.value)}
                              className="mb-2"
                            >
                              <option value="lump_sum">일시불 투자</option>
                              <option value="dca">분할 매수 (DCA)</option>
                            </Form.Select>
                            {stock.investmentType === 'dca' && (
                              <Form.Control
                                type="number"
                                value={stock.dcaPeriods || 12}
                                onChange={(e) => updateStock(index, 'dcaPeriods', e.target.value)}
                                min="1"
                                max="60"
                                placeholder="개월 수"
                              />
                            )}
                          </div>
                          {stock.investmentType === 'dca' && stock.dcaPeriods && (
                            <small className="text-muted">
                              월 ${Math.round(stock.amount / stock.dcaPeriods)}씩 {stock.dcaPeriods}개월
                            </small>
                          )}
                        </td>
                        <td>
                          {((stock.amount / getTotalAmount()) * 100).toFixed(1)}%
                        </td>
                        <td>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => removeStock(index)}
                            disabled={portfolio.length <= 1}
                          >
                            삭제
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="table-info">
                      <th>합계</th>
                      <th>${getTotalAmount().toLocaleString()}</th>
                      <th>-</th>
                      <th>100.0%</th>
                      <th></th>
                    </tr>
                  </tfoot>
                </Table>

                <div className="d-flex gap-2 mb-3">
                  <Button variant="outline-primary" onClick={addStock} disabled={portfolio.length >= 10}>
                    + 종목 추가
                  </Button>
                  <Button 
                    variant="outline-success" 
                    onClick={addCash}
                    disabled={portfolio.length >= 10}
                    title="현금을 포트폴리오에 추가 (무위험 자산)"
                  >
                    💰 현금 추가
                  </Button>
                </div>
              </Col>
            </Row>

            {/* 백테스트 설정 */}
            <Row className="mb-4">
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>시작 날짜</Form.Label>
                  <Form.Control
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>종료 날짜</Form.Label>
                  <Form.Control
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>

            <Row className="mb-4">
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>투자 전략</Form.Label>
                  <Form.Select
                    value={selectedStrategy}
                    onChange={(e) => setSelectedStrategy(e.target.value)}
                  >
                    <option value="buy_and_hold">매수 후 보유</option>
                    <option value="sma_crossover">단순이동평균 교차</option>
                    <option value="rsi_strategy">RSI 전략</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>리밸런싱 주기</Form.Label>
                  <Form.Select
                    value={rebalanceFrequency}
                    onChange={(e) => setRebalanceFrequency(e.target.value)}
                  >
                    <option value="never">리밸런싱 안함</option>
                    <option value="monthly">매월</option>
                    <option value="quarterly">분기별</option>
                    <option value="yearly">연간</option>
                  </Form.Select>
                  <Form.Text className="text-muted">
                    포트폴리오 비중을 다시 맞추는 주기
                  </Form.Text>
                </Form.Group>
              </Col>
            </Row>

            <Row className="mb-4">
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>거래 수수료 (%)</Form.Label>
                  <Form.Control
                    type="number"
                    value={commission}
                    onChange={(e) => setCommission(Number(e.target.value))}
                    min="0"
                    max="5"
                    step="0.01"
                  />
                  <Form.Text className="text-muted">
                    예: 0.2 (0.2% 수수료)
                  </Form.Text>
                </Form.Group>
              </Col>
            </Row>

            {/* 전략 파라미터 */}
            {renderStrategyParams()}

            {/* 실행 버튼 */}
            <Row>
              <Col>
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  disabled={loading || isLoading}
                  className="w-100"
                >
                  {loading || isLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      포트폴리오 백테스트 실행 중...
                    </>
                  ) : (
                    '📈 포트폴리오 백테스트 실행'
                  )}
                </Button>
              </Col>
            </Row>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default UnifiedBacktestForm;
