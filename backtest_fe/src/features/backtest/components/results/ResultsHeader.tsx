import React, { useMemo } from 'react';
import { CalendarRange, Layers, LineChart, PieChart } from 'lucide-react';
import { Badge } from '@/shared/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import { Separator } from '@/shared/ui/separator';
import { ChartData, PortfolioData, Stock } from '../../model/backtest-result-types';
import { FormLegend } from '@/shared/components';
import { formatPercent } from '@/shared/lib/utils/formatters';

interface ResultsHeaderProps {
  data: ChartData | PortfolioData;
  isPortfolio: boolean;
}

const ResultsHeader: React.FC<ResultsHeaderProps> = ({ data, isPortfolio }) => {
  const { title, subtitle, metaBadges, legendItems } = useMemo(() => {
    if (isPortfolio && 'portfolio_composition' in data) {
      const portfolioData = data as PortfolioData;
      const { portfolio_statistics, portfolio_composition } = portfolioData;
      const tickers = portfolio_composition.map((item: Stock) => item.symbol);
      const isMultipleStocks = tickers.length > 1;

      return {
        title: isMultipleStocks ? '포트폴리오 백테스트 결과' : `${tickers[0]} 백테스트 결과` ,
        subtitle: `${portfolio_statistics.Start} ~ ${portfolio_statistics.End}`,
        metaBadges: [
          { icon: <Layers className="h-3.5 w-3.5" />, label: `${tickers.length}개 자산` },
          { icon: <PieChart className="h-3.5 w-3.5" />, label: tickers.join(' · ') },
        ],
        legendItems: [
          {
            label: `총 수익률 ${formatPercent(portfolio_statistics.Total_Return)}`,
            tone: 'accent' as const,
          },
          { label: '세부 차트와 구성 비중을 확인하세요', tone: 'muted' as const },
        ],
      };
    }

    const chartData = data as ChartData;
    const ticker = chartData.ticker ?? '알 수 없는 종목';
    const strategy = chartData.strategy ?? '전략 미지정';
    return {
      title: `${ticker} · ${strategy} 결과`,
      subtitle: '상세 차트와 거래 내역을 확인하세요',
      metaBadges: [
        { icon: <LineChart className="h-3.5 w-3.5" />, label: strategy },
        ...(chartData.start_date && chartData.end_date
          ? [{ icon: <CalendarRange className="h-3.5 w-3.5" />, label: `${chartData.start_date} ~ ${chartData.end_date}` }]
          : []),
      ],
      legendItems: [
        { label: '성과 지표, 거래 내역, 차트를 한 번에 제공합니다', tone: 'muted' as const },
      ],
    };
  }, [data, isPortfolio]);

  return (
    <Card className="overflow-hidden border border-border/70 bg-card/70 shadow-sm">
      <CardHeader className="space-y-3">
        <div className="space-y-2">
          <CardTitle className="text-2xl font-semibold text-foreground">{title}</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">{subtitle}</CardDescription>
        </div>

        {metaBadges?.length ? (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {metaBadges.map(({ icon, label }) => (
              <Badge
                key={label}
                variant="outline"
                className="flex items-center gap-1 rounded-full border-border/60 bg-background/70 px-3 py-1 text-xs font-medium"
              >
                {icon}
                {label}
              </Badge>
            ))}
          </div>
        ) : null}

        {legendItems?.length ? <FormLegend items={legendItems} className="mt-1" /> : null}
      </CardHeader>
      <Separator className="bg-border/60" />
    </Card>
  );
};

export default ResultsHeader;
