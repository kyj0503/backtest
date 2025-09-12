import React from 'react';
import { formatPercent, getStatVariant } from '../utils/formatters';
import FinancialTermTooltip from './common/FinancialTermTooltip';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';

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
      value: formatPercent(stats.total_return_pct || stats.Total_Return || 0), 
      variant: getStatVariant(stats.total_return_pct || stats.Total_Return || 0, 'return') as any, 
      description: '투자 원금 대비 총 수익률' 
    },
    { 
      label: '총 거래수', 
      value: (stats.total_trades || stats.Total_Trading_Days || 0).toString(), 
      variant: 'primary', 
      description: '전체 기간 동안 체결된 거래수' 
    },
    { 
      label: '승률', 
      value: formatPercent(stats.win_rate_pct || stats.Win_Rate || 0), 
      variant: getStatVariant(stats.win_rate_pct || stats.Win_Rate || 0, 'winRate') as any, 
      description: '전체 거래 중 이익 비율' 
    },
    { 
      label: '최대 손실', 
      value: formatPercent(stats.max_drawdown_pct || stats.Max_Drawdown || 0), 
      variant: getStatVariant(stats.max_drawdown_pct || stats.Max_Drawdown || 0, 'drawdown') as any, 
      description: '최대 Drawdown' 
    },
    { 
      label: '샤프', 
      value: (stats.sharpe_ratio || stats.Sharpe_Ratio || 0).toFixed(3), 
      variant: getStatVariant(stats.sharpe_ratio || stats.Sharpe_Ratio || 0, 'sharpe') as any, 
      description: '리스크 대비 성과 지표' 
    },
    { 
      label: 'Profit Factor', 
      value: (stats.profit_factor || 1.0).toFixed(2), 
      variant: ((stats.profit_factor || 1.0) >= 1.5 ? 'success' : (stats.profit_factor || 1.0) >= 1 ? 'warning' : 'danger') as any, 
      description: '이익/손실 비율' 
    }
  ];

  // 벤치마크 통계가 있는 경우 추가 카드 구성
  if (typeof stats.benchmark_total_return_pct === 'number') {
    const label = stats.benchmark_ticker
      ? `벤치마크(${String(stats.benchmark_ticker).toUpperCase()}) 수익률`
      : '벤치마크 수익률';
    statItems.push({
      label,
      value: formatPercent(stats.benchmark_total_return_pct || 0),
      variant: getStatVariant(stats.benchmark_total_return_pct || 0, 'return') as any,
      description: '지정한 벤치마크의 총 수익률'
    });
  }

  if (typeof stats.alpha_vs_benchmark_pct === 'number') {
    statItems.push({
      label: '알파(벤치마크 대비)',
      value: formatPercent(stats.alpha_vs_benchmark_pct || 0),
      variant: getStatVariant(stats.alpha_vs_benchmark_pct || 0, 'return') as any,
      description: '벤치마크 대비 초과수익률'
    });
  }



  return (
    <div className="mb-8">
      <h4 className="text-xl font-semibold mb-6">백테스트 성과</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statItems.map((item, index) => (
          <Card key={index} className="text-center hover:shadow-md transition-shadow" title={item.description}>
            <CardContent className="p-6">
              <h5 className="text-sm font-medium text-muted-foreground mb-3">
                <FinancialTermTooltip term={item.label}>
                  {item.label}
                </FinancialTermTooltip>
              </h5>
              <Badge variant={item.variant === 'success' ? 'default' : item.variant === 'danger' ? 'destructive' : 'secondary'} className="text-lg font-semibold px-4 py-2">
                {item.value}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default StatsSummary;
