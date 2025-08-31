import React from 'react';
import { Row, Col, Card, Badge, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { formatPercent, getStatVariant } from '../utils/formatters';

const StatsSummary: React.FC<{ stats: any }> = ({ stats }) => {
  if (!stats) return null;

  const statItems: Array<{
    label: string;
    value: string;
    variant: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'light' | 'dark';
    description: string;
  }> = [
    { 
      label: '총 수익률', 
      value: formatPercent(stats.total_return_pct), 
      variant: getStatVariant(stats.total_return_pct, 'return') as any, 
      description: '투자 원금 대비 총 수익률' 
    },
    { 
      label: '총 거래수', 
      value: stats.total_trades.toString(), 
      variant: 'primary', 
      description: '전체 기간 동안 체결된 거래수' 
    },
    { 
      label: '승률', 
      value: formatPercent(stats.win_rate_pct), 
      variant: getStatVariant(stats.win_rate_pct, 'winRate') as any, 
      description: '전체 거래 중 이익 비율' 
    },
    { 
      label: '최대 손실', 
      value: formatPercent(stats.max_drawdown_pct), 
      variant: getStatVariant(stats.max_drawdown_pct, 'drawdown') as any, 
      description: '최대 Drawdown' 
    },
    { 
      label: '샤프', 
      value: stats.sharpe_ratio.toFixed(3), 
      variant: getStatVariant(stats.sharpe_ratio, 'sharpe') as any, 
      description: '리스크 대비 성과 지표' 
    },
    { 
      label: 'Profit Factor', 
      value: stats.profit_factor.toFixed(2), 
      variant: (stats.profit_factor >= 1.5 ? 'success' : stats.profit_factor >= 1 ? 'warning' : 'danger') as any, 
      description: '이익/손실 비율' 
    }
  ];

  return (
    <div className="mb-4">
      <h4 className="mb-3">📈 백테스트 성과</h4>
      <Row>
        {statItems.map((item, index) => (
          <Col md={6} lg={4} key={index} className="mb-3">
            <OverlayTrigger placement="top" overlay={<Tooltip>{item.description}</Tooltip>}>
              <Card className="h-100 shadow-sm border-0">
                <Card.Body className="text-center">
                  <Card.Title className="fs-6 text-muted">{item.label}</Card.Title>
                  <Badge bg={item.variant} className="fs-5 px-3 py-2">{item.value}</Badge>
                </Card.Body>
              </Card>
            </OverlayTrigger>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default StatsSummary;
