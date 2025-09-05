import React from 'react';
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

  const getVariantClasses = (variant: string) => {
    switch (variant) {
      case 'primary': return 'bg-blue-600 text-white';
      case 'success': return 'bg-green-600 text-white';
      case 'danger': return 'bg-red-600 text-white';
      case 'warning': return 'bg-yellow-600 text-white';
      case 'info': return 'bg-cyan-600 text-white';
      case 'secondary': return 'bg-gray-600 text-white';
      default: return 'bg-blue-600 text-white';
    }
  };

  return (
    <div className="mb-8">
      <h4 className="text-xl font-semibold mb-6">📈 백테스트 성과</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statItems.map((item, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center hover:shadow-md transition-shadow"
            title={item.description}
          >
            <h5 className="text-sm font-medium text-gray-600 mb-3">{item.label}</h5>
            <span className={`inline-block px-4 py-2 rounded-lg text-lg font-semibold ${getVariantClasses(item.variant)}`}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatsSummary;
