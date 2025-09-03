import React, { useState } from "react";
import { Card, Button, Badge, Row, Col } from "react-bootstrap";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface StockData {
  symbol: string;
  data: Array<{
    date: string;
    price: number;
    volume?: number;
  }>;
}

interface StockPriceChartProps {
  stocksData: StockData[];
  className?: string;
}

const StockPriceChart: React.FC<StockPriceChartProps> = ({ stocksData, className = "" }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handlePrevious = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === 0 ? stocksData.length - 1 : prevIndex - 1
    );
  };

  const handleNext = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === stocksData.length - 1 ? 0 : prevIndex + 1
    );
  };

  if (!stocksData || stocksData.length === 0) {
    return (
      <Card className={className}>
        <Card.Body className="text-center">
          <p className="text-muted">표시할 주가 데이터가 없습니다.</p>
        </Card.Body>
      </Card>
    );
  }

  const currentStock = stocksData[currentIndex];

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
  };

  // 가격 포맷팅 함수
  const formatPrice = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className={className}>
      {/* 헤더: 종목명과 네비게이션 */}
      <Row className="mb-3 align-items-center">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-1">{currentStock.symbol}</h5>
              <Badge bg="secondary">
                {currentIndex + 1} / {stocksData.length}
              </Badge>
            </div>
            <div>
              <Button 
                variant="outline-primary" 
                size="sm" 
                onClick={handlePrevious}
                disabled={stocksData.length <= 1}
                className="me-2"
              >
                ← 이전
              </Button>
              <Button 
                variant="outline-primary" 
                size="sm" 
                onClick={handleNext}
                disabled={stocksData.length <= 1}
              >
                다음 →
              </Button>
            </div>
          </div>
        </Col>
      </Row>

      {/* 차트 */}
      <div style={{ width: '100%', height: '400px' }}>
        <ResponsiveContainer>
          <LineChart data={currentStock.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatDate}
              tick={{ fontSize: 12 }}
              interval={Math.max(1, Math.floor(currentStock.data.length / 8))}
            />
            <YAxis 
              tickFormatter={formatPrice}
              domain={['dataMin - 5', 'dataMax + 5']}
            />
            <Tooltip 
              labelFormatter={(label: any) => `날짜: ${label}`}
              formatter={(value: number) => [formatPrice(value), '주가']}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 차트 하단 정보 */}
      <Row className="mt-3">
        <Col md={6}>
          <small className="text-muted">
            시작: {currentStock.data[0]?.date} | 
            종료: {currentStock.data[currentStock.data.length - 1]?.date}
          </small>
        </Col>
        <Col md={6} className="text-end">
          <small className="text-muted">
            데이터 포인트: {currentStock.data.length}개
          </small>
        </Col>
      </Row>
    </div>
  );
};

export default StockPriceChart;
