import React from 'react';
import { Container, Row, Col, Card, Table, Badge } from 'react-bootstrap';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import OHLCChart from './OHLCChart';
import EquityChart from './EquityChart';
import TradesChart from './TradesChart';
import StatsSummary from './StatsSummary';
import { formatPercent } from '../utils/formatters';

interface Stock {
  symbol: string;
  weight: number;
}

interface IndividualReturn {
  weight: number;
  return: number;
  start_price: number;
  end_price: number;
}

interface PortfolioStatistics {
  Start: string;
  End: string;
  Duration: string;
  Initial_Value: number;
  Final_Value: number;
  Peak_Value: number;
  Total_Return: number;
  Annual_Return: number;
  Annual_Volatility: number;
  Sharpe_Ratio: number;
  Max_Drawdown: number;
  Avg_Drawdown: number;
  Max_Consecutive_Gains: number;
  Max_Consecutive_Losses: number;
  Total_Trading_Days: number;
  Positive_Days: number;
  Negative_Days: number;
  Win_Rate: number;
}

interface ChartData {
  ticker?: string;
  strategy?: string;
  ohlc_data?: any[];
  equity_data?: any[];
  trade_markers?: any[];
  indicators?: any[];
  summary_stats?: any;
}

interface PortfolioData {
  portfolio_statistics: PortfolioStatistics;
  individual_returns: Record<string, IndividualReturn>;
  portfolio_composition: Stock[];
  equity_curve: Record<string, number>;
  daily_returns: Record<string, number>;
}

interface UnifiedBacktestResultsProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const UnifiedBacktestResults: React.FC<UnifiedBacktestResultsProps> = ({ data, isPortfolio }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (!data) {
    return (
      <Container>
        <div className="text-center my-5">
          <div style={{ fontSize: '3rem' }}>⚠️</div>
          <h4 className="mt-3">결과 데이터가 없습니다</h4>
          <p className="text-muted">백테스트를 다시 실행해주세요.</p>
        </div>
      </Container>
    );
  }

  // 포트폴리오 결과 렌더링
  if (isPortfolio) {
    const portfolioData = data as PortfolioData;
    const { portfolio_statistics, individual_returns, portfolio_composition, equity_curve, daily_returns } = portfolioData;

    if (!portfolio_statistics || !individual_returns || !portfolio_composition || !equity_curve || !daily_returns) {
      return (
        <Container>
          <div className="text-center my-5">
            <div style={{ fontSize: '3rem' }}>⚠️</div>
            <h4 className="mt-3">결과 데이터가 불완전합니다</h4>
            <p className="text-muted">포트폴리오 백테스트를 다시 실행해주세요.</p>
          </div>
        </Container>
      );
    }

    const equityChartData = Object.entries(equity_curve || {}).map(([date, value]) => ({
      date,
      value: value,
      return: daily_returns[date] || 0
    }));

    const isMultipleStocks = portfolio_composition.length > 1;

    return (
      <Container>
        {/* 헤더 */}
        <Card className="mb-4 bg-light">
          <Card.Body>
            <h2 className="text-primary mb-2">
              {isMultipleStocks ? '📈 포트폴리오 백테스트 결과' : '📊 단일 종목 백테스트 결과'}
            </h2>
            <p className="text-muted mb-0">
              {portfolio_composition.map(item => item.symbol).join(', ')} | 
              {portfolio_statistics.Start} ~ {portfolio_statistics.End}
            </p>
          </Card.Body>
        </Card>

        {/* 주요 성과 지표 */}
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h4>{isMultipleStocks ? '포트폴리오' : '종목'} 성과 요약</h4>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={3}>
                    <div className="text-center">
                      <h6>총 수익률</h6>
                      <h4 className={(portfolio_statistics.Total_Return || 0) >= 0 ? 'text-success' : 'text-danger'}>
                        {formatPercent(portfolio_statistics.Total_Return)}
                      </h4>
                    </div>
                  </Col>
                  <Col md={3}>
                    <div className="text-center">
                      <h6>연간 수익률</h6>
                      <h5 className={(portfolio_statistics.Annual_Return || 0) >= 0 ? 'text-success' : 'text-danger'}>
                        {formatPercent(portfolio_statistics.Annual_Return)}
                      </h5>
                    </div>
                  </Col>
                  <Col md={3}>
                    <div className="text-center">
                      <h6>샤프 비율</h6>
                      <h5>{portfolio_statistics.Sharpe_Ratio ? portfolio_statistics.Sharpe_Ratio.toFixed(2) : 'N/A'}</h5>
                    </div>
                  </Col>
                  <Col md={3}>
                    <div className="text-center">
                      <h6>최대 낙폭</h6>
                      <h5 className="text-danger">
                        {formatPercent(portfolio_statistics.Max_Drawdown)}
                      </h5>
                    </div>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* 포트폴리오 구성 및 개별 수익률 */}
        <Row className="mb-4">
          <Col md={isMultipleStocks ? 6 : 12}>
            <Card>
              <Card.Header>
                <h5>{isMultipleStocks ? '포트폴리오 구성' : '종목 정보'}</h5>
              </Card.Header>
              <Card.Body>
                <Table striped bordered hover>
                  <thead>
                    <tr>
                      <th>종목</th>
                      {isMultipleStocks && <th>비중</th>}
                      <th>개별 수익률</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio_composition.map((item) => {
                      const individualReturn = individual_returns[item.symbol];
                      return (
                        <tr key={item.symbol}>
                          <td>
                            <Badge bg="primary">{item.symbol}</Badge>
                          </td>
                          {isMultipleStocks && (
                            <td>{formatPercent(item.weight * 100)}</td>
                          )}
                          <td className={individualReturn?.return >= 0 ? 'text-success' : 'text-danger'}>
                            {individualReturn ? formatPercent(individualReturn.return) : 'N/A'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>
          {isMultipleStocks && (
            <Col md={6}>
              <Card>
                <Card.Header>
                  <h5>상세 통계</h5>
                </Card.Header>
                <Card.Body>
                  <Table size="sm">
                    <tbody>
                      <tr>
                        <td>백테스트 기간</td>
                        <td>{portfolio_statistics.Start} ~ {portfolio_statistics.End}</td>
                      </tr>
                      <tr>
                        <td>초기 자본금</td>
                        <td>{formatCurrency(portfolio_statistics.Initial_Value)}</td>
                      </tr>
                      <tr>
                        <td>최종 자본금</td>
                        <td>{formatCurrency(portfolio_statistics.Final_Value)}</td>
                      </tr>
                      <tr>
                        <td>최고 자본금</td>
                        <td>{formatCurrency(portfolio_statistics.Peak_Value)}</td>
                      </tr>
                      <tr>
                        <td>연간 변동성</td>
                        <td>{formatPercent(portfolio_statistics.Annual_Volatility)}</td>
                      </tr>
                      <tr>
                        <td>평균 낙폭</td>
                        <td>{formatPercent(portfolio_statistics.Avg_Drawdown)}</td>
                      </tr>
                      <tr>
                        <td>상승일/하락일</td>
                        <td>
                          <span className="text-success">{portfolio_statistics.Positive_Days || 0}</span>
                          {' / '}
                          <span className="text-danger">{portfolio_statistics.Negative_Days || 0}</span>
                        </td>
                      </tr>
                      <tr>
                        <td>승률</td>
                        <td>{formatPercent(portfolio_statistics.Win_Rate)}</td>
                      </tr>
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          )}
        </Row>

        {/* 자산 곡선 차트 */}
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h5>자산 곡선</h5>
              </Card.Header>
              <Card.Body>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={equityChartData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                      }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => formatCurrency(value)}
                    />
                    <Tooltip 
                      formatter={(value: number) => [formatCurrency(value), isMultipleStocks ? '포트폴리오 가치' : '자산 가치']}
                      labelFormatter={(label) => `날짜: ${label}`}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#8884d8" 
                      fillOpacity={1} 
                      fill="url(#colorValue)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* 일일 수익률 차트 */}
        <Row>
          <Col>
            <Card>
              <Card.Header>
                <h5>일일 수익률 분포</h5>
              </Card.Header>
              <Card.Body>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={equityChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                      }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `${value.toFixed(1)}%`}
                    />
                    <Tooltip 
                      formatter={(value: number) => [`${value.toFixed(2)}%`, '일일 수익률']}
                      labelFormatter={(label) => `날짜: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="return" 
                      stroke="#ff7300" 
                      strokeWidth={1}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    );
  }

  // 단일 종목 결과 렌더링 (기존 차트 컴포넌트 사용)
  const chartData = data as ChartData;
  
  return (
    <Container>
      {/* 헤더 */}
      <Card className="mb-4 bg-light">
        <Card.Body>
          <h2 className="text-primary mb-2">📊 {chartData.ticker} - {chartData.strategy} 백테스트 결과</h2>
          <p className="text-muted mb-0">상세한 차트 분석과 거래 내역을 확인하세요</p>
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
    </Container>
  );
};

export default UnifiedBacktestResults;
