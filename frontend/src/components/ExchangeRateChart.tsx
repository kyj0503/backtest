import React, { useState, useEffect } from "react";
import { Card, Row, Col, Spinner } from "react-bootstrap";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { backtestApiService } from "../services/api";

interface ExchangeRateData {
  date: string;
  rate: number;
  volume?: number;
}

interface ExchangeRateChartProps {
  startDate: string;
  endDate: string;
  className?: string;
}

const ExchangeRateChart: React.FC<ExchangeRateChartProps> = ({ 
  startDate, 
  endDate, 
  className = "" 
}) => {
  const [exchangeData, setExchangeData] = useState<ExchangeRateData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExchangeRate = async () => {
      if (!startDate || !endDate) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await backtestApiService.getExchangeRate(startDate, endDate);
        if (response.status === 'success' && response.data.exchange_rates) {
          setExchangeData(response.data.exchange_rates);
        } else {
          setError(response.message || '환율 데이터를 가져올 수 없습니다.');
        }
      } catch (error) {
        console.error('환율 데이터 조회 실패:', error);
        setError('환율 데이터 조회에 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchExchangeRate();
  }, [startDate, endDate]);

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
  };

  // 환율 포맷팅 함수
  const formatRate = (value: number) => {
    return `₩${value.toLocaleString()}`;
  };

  if (loading) {
    return (
      <Card className={className}>
        <Card.Header>
          <h5 className="mb-0">원달러 환율 변동</h5>
        </Card.Header>
        <Card.Body className="text-center">
          <Spinner animation="border" size="sm" className="me-2" />
          <span>환율 데이터 로딩 중...</span>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <Card.Header>
          <h5 className="mb-0">원달러 환율 변동</h5>
        </Card.Header>
        <Card.Body className="text-center">
          <p className="text-danger">{error}</p>
        </Card.Body>
      </Card>
    );
  }

  if (!exchangeData || exchangeData.length === 0) {
    return (
      <Card className={className}>
        <Card.Header>
          <h5 className="mb-0">원달러 환율 변동</h5>
        </Card.Header>
        <Card.Body className="text-center">
          <p className="text-muted">표시할 환율 데이터가 없습니다.</p>
        </Card.Body>
      </Card>
    );
  }

  const minRate = Math.min(...exchangeData.map(d => d.rate));
  const maxRate = Math.max(...exchangeData.map(d => d.rate));
  const rateChange = ((exchangeData[exchangeData.length - 1]?.rate - exchangeData[0]?.rate) / exchangeData[0]?.rate * 100);

  return (
    <Card className={className}>
      <Card.Header>
        <Row className="align-items-center">
          <Col>
            <h5 className="mb-0">원달러 환율 변동</h5>
          </Col>
          <Col xs="auto">
            <small className={`badge ${rateChange >= 0 ? 'bg-danger' : 'bg-success'}`}>
              {rateChange >= 0 ? '+' : ''}{rateChange.toFixed(2)}%
            </small>
          </Col>
        </Row>
      </Card.Header>
      <Card.Body>
        {/* 환율 차트 */}
        <div style={{ width: '100%', height: '300px' }}>
          <ResponsiveContainer>
            <LineChart data={exchangeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={formatDate}
                interval="preserveStartEnd"
              />
              <YAxis 
                tickFormatter={formatRate}
                domain={[minRate * 0.995, maxRate * 1.005]}
              />
              <Tooltip 
                labelFormatter={(label: any) => `날짜: ${label}`}
                formatter={(value: number) => [formatRate(value), 'USD/KRW']}
              />
              <Line 
                type="monotone" 
                dataKey="rate" 
                stroke="#fd7e14" 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 환율 요약 정보 */}
        <Row className="mt-3">
          <Col md={4}>
            <small className="text-muted d-block">시작 환율</small>
            <strong>{formatRate(exchangeData[0]?.rate)}</strong>
          </Col>
          <Col md={4}>
            <small className="text-muted d-block">종료 환율</small>
            <strong>{formatRate(exchangeData[exchangeData.length - 1]?.rate)}</strong>
          </Col>
          <Col md={4}>
            <small className="text-muted d-block">기간 중 변동폭</small>
            <strong>{formatRate(maxRate - minRate)}</strong>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

export default ExchangeRateChart;
