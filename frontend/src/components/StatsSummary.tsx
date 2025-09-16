import React from 'react';
import { formatPercent, getStatVariant } from '../utils/formatters';
import FinancialTermTooltip from './common/FinancialTermTooltip';
import { Card, CardContent } from './ui/card';
import { cn } from '../lib/utils';

type StatTone = 'positive' | 'negative' | 'neutral';

interface StatItem {
  label: string;
  value: string;
  tone: StatTone;
  description: string;
}

const toneClassMap: Record<StatTone, string> = {
  positive: 'text-emerald-600 bg-emerald-500/10 border-emerald-500/30',
  negative: 'text-destructive bg-destructive/10 border-destructive/30',
  neutral: 'text-foreground bg-muted/40 border-border/60',
};

const StatsSummary: React.FC<{ stats: Record<string, unknown> | null | undefined }> = ({ stats }) => {
  if (!stats) return null;

  const numberValue = (value: unknown, fallback = 0): number => {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      return Number.isFinite(parsed) ? parsed : fallback;
    }
    return fallback;
  };

  const mapVariantToTone = (variant: string): StatTone => {
    switch (variant) {
      case 'success':
        return 'positive';
      case 'danger':
        return 'negative';
      default:
        return 'neutral';
    }
  };

  const statItems: StatItem[] = [
    {
      label: '총 수익률',
      value: formatPercent(numberValue(stats.total_return_pct ?? stats.Total_Return)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.total_return_pct ?? stats.Total_Return), 'return'),
      ),
      description: '투자 원금 대비 총 수익률',
    },
    {
      label: '총 거래수',
      value: String(numberValue(stats.total_trades ?? stats.Total_Trading_Days, 0)),
      tone: 'neutral',
      description: '전체 기간 동안 체결된 거래 수',
    },
    {
      label: '승률',
      value: formatPercent(numberValue(stats.win_rate_pct ?? stats.Win_Rate)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.win_rate_pct ?? stats.Win_Rate), 'winRate'),
      ),
      description: '전체 거래 중 이익을 기록한 비율',
    },
    {
      label: '최대 손실',
      value: formatPercent(numberValue(stats.max_drawdown_pct ?? stats.Max_Drawdown)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.max_drawdown_pct ?? stats.Max_Drawdown), 'drawdown'),
      ),
      description: '최대 Drawdown(최대 낙폭)',
    },
    {
      label: '샤프 비율',
      value: numberValue(stats.sharpe_ratio ?? stats.Sharpe_Ratio).toFixed(2),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.sharpe_ratio ?? stats.Sharpe_Ratio), 'sharpe'),
      ),
      description: '리스크 대비 성과 지표 (Sharpe)',
    },
    {
      label: 'Profit Factor',
      value: numberValue(stats.profit_factor ?? stats.Profit_Factor, 1).toFixed(2),
      tone:
        numberValue(stats.profit_factor ?? stats.Profit_Factor, 1) >= 1.5
          ? 'positive'
          : numberValue(stats.profit_factor ?? stats.Profit_Factor, 1) >= 1
          ? 'neutral'
          : 'negative',
      description: '이익과 손실의 비율 (Profit Factor)',
    },
  ];

  if (typeof stats.benchmark_total_return_pct === 'number') {
    const tickerLabel =
      typeof stats.benchmark_ticker === 'string'
        ? String(stats.benchmark_ticker).toUpperCase()
        : undefined;
    statItems.push({
      label: tickerLabel ? `벤치마크(${tickerLabel}) 수익률` : '벤치마크 수익률',
      value: formatPercent(numberValue(stats.benchmark_total_return_pct)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.benchmark_total_return_pct), 'return'),
      ),
      description: '선택한 벤치마크의 총 수익률',
    });
  }

  if (typeof stats.alpha_vs_benchmark_pct === 'number') {
    statItems.push({
      label: '알파 (벤치마크 대비)',
      value: formatPercent(numberValue(stats.alpha_vs_benchmark_pct)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.alpha_vs_benchmark_pct), 'return'),
      ),
      description: '벤치마크 대비 초과 수익률',
    });
  }

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <h4 className="text-lg font-semibold text-foreground">백테스트 성과</h4>
        <p className="text-xs text-muted-foreground">
          주요 지표를 통해 포트폴리오의 성과와 리스크를 빠르게 파악하세요.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {statItems.map(item => (
          <Card
            key={item.label}
            className={cn(
              'overflow-hidden border border-border/70 bg-card/70 shadow-sm transition-shadow hover:shadow-md',
            )}
          >
            <CardContent className="space-y-3 px-5 py-4">
              <h5 className="text-sm font-medium text-muted-foreground">
                <FinancialTermTooltip term={item.label}>{item.label}</FinancialTermTooltip>
              </h5>
              <div
                className={cn(
                  'inline-flex items-center gap-2 rounded-full border px-3 py-2 text-base font-semibold',
                  toneClassMap[item.tone],
                )}
              >
                {item.value}
              </div>
              <p className="text-xs text-muted-foreground">{item.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
};

export default StatsSummary;
