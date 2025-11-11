import React from 'react';
import { formatPercent, getStatVariant } from '@/shared/lib/utils/formatters';
import { FinancialTermTooltip } from '@/shared/components';
import { Card, CardContent } from '@/shared/ui/card';
import { cn } from '@/shared/lib/core/utils';
import { HEADING_STYLES, TEXT_STYLES } from '@/shared/styles/design-tokens';

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
      label: '거래일 수',
      value: String(numberValue(stats.Total_Trading_Days, 0)),
      tone: 'neutral',
      description: '백테스트가 실행된 총 거래일 수',
    },
    {
      label: '총 거래 횟수',
      value: String(numberValue(stats.Total_Trades, 0)),
      tone: 'neutral',
      description: '실제 매수/매도가 발생한 총 거래 횟수',
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
      label: '연간 변동성',
      value: formatPercent(numberValue(stats.annual_volatility_pct ?? stats.Annual_Volatility)),
      tone: (() => {
        const volatility = numberValue(stats.annual_volatility_pct ?? stats.Annual_Volatility);
        // 낮을수록 안정적 (초록색), 높을수록 위험 (빨간색)
        if (volatility < 15) return 'positive';  // 낮은 변동성 (안정)
        if (volatility < 25) return 'neutral';   // 보통 변동성
        return 'negative';                       // 높은 변동성 (위험)
      })(),
      description: '수익률의 변동 폭 (낮을수록 안정적)',
    },
    {
      label: '프로핏 팩터',
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

  if (typeof stats.sp500_total_return_pct === 'number') {
    statItems.push({
      label: 'S&P 500 수익률',
      value: formatPercent(numberValue(stats.sp500_total_return_pct)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.sp500_total_return_pct), 'return'),
      ),
      description: '동일 기간 S&P 500 지수의 총 수익률',
    });
  }

  if (typeof stats.alpha_vs_sp500_pct === 'number') {
    statItems.push({
      label: 'S&P 500 대비 성과',
      value: formatPercent(numberValue(stats.alpha_vs_sp500_pct)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.alpha_vs_sp500_pct), 'return'),
      ),
      description: 'S&P 500 지수 대비 초과 수익률',
    });
  }

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <h4 className={HEADING_STYLES.h3}>백테스트 성과</h4>
        <p className={TEXT_STYLES.captionSmall}>
          주요 지표를 통해 포트폴리오의 성과와 리스크를 빠르게 파악하세요.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {statItems.map(item => (
          <Card
            key={item.label}
            className={cn(
              'overflow-hidden border border-border/40 bg-card shadow-sm transition-shadow hover:shadow-md',
            )}
          >
            <CardContent className="space-y-3 px-5 py-4">
              <h5 className={TEXT_STYLES.label}>
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
              <p className={TEXT_STYLES.captionSmall}>{item.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
};

export default StatsSummary;
