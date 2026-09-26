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

  // 계산 불가(null)를 숫자 폴백으로 바꾸지 않는다 — 지어낸 숫자가 된다 (A-09)
  const optionalNumber = (value: unknown): number | null => {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
  };
  const NOT_AVAILABLE = '—';

  // 단일 종목 결과(summary_stats)는 backtesting.py의 거래 기준 승률(win_rate_pct)을,
  // 포트폴리오 결과는 일 기준 승률(Win_Rate, 상승일 비율)을 준다.
  const hasTradeBasedWinRate = stats.win_rate_pct !== undefined;
  const winRate = numberValue(stats.win_rate_pct ?? stats.Win_Rate);
  const annualReturn = optionalNumber(stats.Annual_Return ?? stats.cagr_pct);
  const profitFactor = optionalNumber(stats.profit_factor ?? stats.Profit_Factor);

  const statItems: StatItem[] = [
    {
      label: '총 수익률',
      value: formatPercent(numberValue(stats.total_return_pct ?? stats.Total_Return)),
      tone: mapVariantToTone(
        getStatVariant(numberValue(stats.total_return_pct ?? stats.Total_Return), 'return'),
      ),
      description: '투자 원금 대비 총 수익률',
    },
  ];

  if (annualReturn !== null) {
    statItems.push({
      label: '연환산 수익률 (시간가중)',
      value: formatPercent(annualReturn),
      tone: mapVariantToTone(getStatVariant(annualReturn, 'return')),
      description: '분할 매수 납입 시점의 영향을 뺀 연평균 복리 수익률 (TWR)',
    });
  }

  statItems.push(
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
    hasTradeBasedWinRate
      ? {
          label: '거래 승률',
          value: formatPercent(winRate),
          tone: mapVariantToTone(getStatVariant(winRate, 'winRate')),
          description: '전체 거래 중 이익을 기록한 비율',
        }
      : {
          label: '승률 (일 기준)',
          value: formatPercent(winRate),
          tone: mapVariantToTone(getStatVariant(winRate, 'winRate')),
          description: '전체 거래일 중 수익이 난 날의 비율',
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
      value: profitFactor === null ? NOT_AVAILABLE : profitFactor.toFixed(2),
      tone:
        profitFactor === null
          ? 'neutral'
          : profitFactor >= 1.5
          ? 'positive'
          : profitFactor >= 1
          ? 'neutral'
          : 'negative',
      description:
        profitFactor === null
          ? '손실이 없어 계산할 수 없음 (Profit Factor)'
          : '이익과 손실의 비율 (Profit Factor)',
    },
  );

  // 전략 경로는 일 기준 Win_Rate와 별도로 거래 기준 승률을 준다 (거래가 없으면 null)
  if (!hasTradeBasedWinRate && 'Trade_Win_Rate' in stats) {
    const tradeWinRate = optionalNumber(stats.Trade_Win_Rate);
    statItems.push({
      label: '거래 승률',
      value: tradeWinRate === null ? NOT_AVAILABLE : formatPercent(tradeWinRate),
      tone:
        tradeWinRate === null
          ? 'neutral'
          : mapVariantToTone(getStatVariant(tradeWinRate, 'winRate')),
      description:
        tradeWinRate === null
          ? '체결된 거래가 없음'
          : '전 종목의 거래를 합쳐 이익을 낸 거래의 비율',
    });
  }

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
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
                  'inline-flex items-center gap-2 rounded-full border px-3 py-2 text-lg font-semibold',
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
