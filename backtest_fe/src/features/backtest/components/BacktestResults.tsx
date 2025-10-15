import React, { useRef } from 'react';
import ChartsSection from './results/ChartsSection';
import { BacktestResultsProps, TradeMarker, ExchangeRatePoint } from '../model/backtest-result-types';
import { AlertCircle, FileDown } from 'lucide-react';
import { Button } from '@/shared/ui/button';

// Summary stats 타입 정의 (동적 필드를 가진 타입)
interface SummaryStats {
  total_return_pct?: number;
  total_trades?: number;
  win_rate_pct?: number;
  max_drawdown_pct?: number;
  sharpe_ratio?: number;
  profit_factor?: number;
  volatility_pct?: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  alpha?: number;
  beta?: number;
  [key: string]: unknown;
}

const BacktestResults: React.FC<BacktestResultsProps> = ({ data, isPortfolio }) => {
  const resultsRef = useRef<HTMLDivElement>(null);

  const generateReportText = (): string => {
    const lines: string[] = [];
    const timestamp = new Date().toISOString().replace('T', ' ').split('.')[0];

    lines.push('='.repeat(80));
    lines.push('백테스트 결과 리포트');
    lines.push('='.repeat(80));
    lines.push(`생성 일시: ${timestamp}`);
    lines.push('');

    if (isPortfolio && 'portfolio_statistics' in data && data.portfolio_statistics) {
      // 포트폴리오 백테스트
      lines.push('[ 포트폴리오 백테스트 ]');
      lines.push('');

      // 포트폴리오 구성
      if ('portfolio_composition' in data && data.portfolio_composition) {
        lines.push('■ 포트폴리오 구성');
        lines.push('-'.repeat(80));
        data.portfolio_composition.forEach((stock) => {
          lines.push(`  ${stock.symbol.padEnd(10)} - 비중: ${(stock.weight * 100).toFixed(2)}%`);
        });
        lines.push('');
      }

      // 주요 성과 지표
      const stats = data.portfolio_statistics;
      lines.push('■ 주요 성과 지표');
      lines.push('-'.repeat(80));
      lines.push(`  백테스트 기간       : ${stats.Start} ~ ${stats.End}`);
      lines.push(`  운용 기간           : ${stats.Duration}`);
      lines.push(`  초기 자본금         : $${stats.Initial_Value.toLocaleString()}`);
      lines.push(`  최종 자산가치       : $${stats.Final_Value.toLocaleString()}`);
      lines.push(`  최고 자산가치       : $${stats.Peak_Value.toLocaleString()}`);
      lines.push('');
      lines.push(`  총 수익률           : ${stats.Total_Return.toFixed(2)}%`);
      lines.push(`  연간 수익률         : ${stats.Annual_Return.toFixed(2)}%`);
      lines.push(`  연간 변동성         : ${stats.Annual_Volatility.toFixed(2)}%`);
      lines.push('');
      lines.push(`  샤프 비율           : ${stats.Sharpe_Ratio.toFixed(2)}`);
      lines.push(`  최대 낙폭(MDD)      : ${stats.Max_Drawdown.toFixed(2)}%`);
      lines.push(`  평균 낙폭           : ${stats.Avg_Drawdown.toFixed(2)}%`);
      lines.push('');
      lines.push(`  총 거래일수         : ${stats.Total_Trading_Days}일`);
      lines.push(`  상승일수            : ${stats.Positive_Days}일`);
      lines.push(`  하락일수            : ${stats.Negative_Days}일`);
      lines.push(`  승률                : ${stats.Win_Rate.toFixed(2)}%`);
      lines.push(`  Profit Factor       : ${stats.Profit_Factor.toFixed(2)}`);
      lines.push(`  연속 상승 최대      : ${stats.Max_Consecutive_Gains}일`);
      lines.push(`  연속 하락 최대      : ${stats.Max_Consecutive_Losses}일`);
      lines.push('');

      // 개별 종목 수익률
      if ('individual_returns' in data && data.individual_returns) {
        lines.push('■ 개별 종목 수익률');
        lines.push('-'.repeat(80));
        Object.entries(data.individual_returns).forEach(([symbol, info]) => {
          lines.push(`  ${symbol.padEnd(10)} - 수익률: ${(info.return * 100).toFixed(2)}%  |  비중: ${(info.weight * 100).toFixed(2)}%`);
          lines.push(`               시작가: $${info.start_price.toFixed(2)}  |  종료가: $${info.end_price.toFixed(2)}`);
        });
        lines.push('');
      }

    } else if ('ticker' in data && data.ticker) {
      // 단일 종목 백테스트
      lines.push('[ 단일 종목 백테스트 ]');
      lines.push('');

      lines.push('■ 기본 정보');
      lines.push('-'.repeat(80));
      lines.push(`  종목                : ${data.ticker || 'N/A'}`);
      lines.push(`  전략                : ${data.strategy || 'N/A'}`);
      lines.push(`  백테스트 기간       : ${data.start_date || 'N/A'} ~ ${data.end_date || 'N/A'}`);
      lines.push('');

      // 요약 통계
      if (data.summary_stats) {
        const stats = data.summary_stats as SummaryStats;
        lines.push('■ 주요 성과 지표');
        lines.push('-'.repeat(80));
        lines.push(`  총 수익률           : ${typeof stats.total_return_pct === 'number' ? stats.total_return_pct.toFixed(2) : 'N/A'}%`);
        lines.push(`  총 거래 수          : ${stats.total_trades || 0}회`);
        lines.push(`  승률                : ${typeof stats.win_rate_pct === 'number' ? stats.win_rate_pct.toFixed(2) : 'N/A'}%`);
        lines.push(`  최대 낙폭(MDD)      : ${typeof stats.max_drawdown_pct === 'number' ? stats.max_drawdown_pct.toFixed(2) : 'N/A'}%`);
        lines.push(`  샤프 비율           : ${typeof stats.sharpe_ratio === 'number' ? stats.sharpe_ratio.toFixed(2) : 'N/A'}`);
        lines.push(`  Profit Factor       : ${typeof stats.profit_factor === 'number' ? stats.profit_factor.toFixed(2) : 'N/A'}`);
        if (typeof stats.volatility_pct === 'number') lines.push(`  변동성              : ${stats.volatility_pct.toFixed(2)}%`);
        if (typeof stats.sortino_ratio === 'number') lines.push(`  소르티노 비율       : ${stats.sortino_ratio.toFixed(2)}`);
        if (typeof stats.calmar_ratio === 'number') lines.push(`  칼마 비율           : ${stats.calmar_ratio.toFixed(2)}`);
        if (typeof stats.alpha === 'number') lines.push(`  알파                : ${stats.alpha.toFixed(2)}`);
        if (typeof stats.beta === 'number') lines.push(`  베타                : ${stats.beta.toFixed(2)}`);
        lines.push('');
      }

      // 거래 내역
      if (data.trade_markers && data.trade_markers.length > 0) {
        lines.push('■ 거래 내역');
        lines.push('-'.repeat(80));
        lines.push(`  총 거래 횟수: ${data.trade_markers.length}회`);
        lines.push('');
        data.trade_markers.slice(0, 50).forEach((trade: TradeMarker, idx) => {
          lines.push(`  [거래 ${idx + 1}]`);
          lines.push(`    날짜       : ${trade.date}`);
          lines.push(`    타입       : ${trade.type === 'entry' ? '진입 (매수)' : '청산 (매도)'}`);
          if (trade.price !== null && trade.price !== undefined && typeof trade.price === 'number') {
            lines.push(`    가격       : $${trade.price.toFixed(2)}`);
          }
          if (trade.quantity) lines.push(`    수량       : ${trade.quantity}`);
          if (trade.pnl_pct !== null && trade.pnl_pct !== undefined && typeof trade.pnl_pct === 'number') {
            lines.push(`    손익률     : ${trade.pnl_pct.toFixed(2)}%`);
          }
          lines.push('');
        });
        if (data.trade_markers.length > 50) {
          lines.push(`  ... 그 외 ${data.trade_markers.length - 50}개 거래 생략`);
          lines.push('');
        }
      }
    }

    // 환율 정보 (공통)
    if ('exchange_rates' in data && data.exchange_rates && data.exchange_rates.length > 0) {
      const rates = data.exchange_rates.filter((r): r is ExchangeRatePoint => r !== null && typeof r.rate === 'number');

      if (rates.length > 0) {
        const firstRate = rates[0];
        const lastRate = rates[rates.length - 1];
        const maxRate = Math.max(...rates.map((r) => r.rate));
        const minRate = Math.min(...rates.map((r) => r.rate));

        lines.push('■ 환율 정보 (KRW/USD)');
        lines.push('-'.repeat(80));
        lines.push(`  시작 환율           : ₩${firstRate.rate.toFixed(2)}`);
        lines.push(`  종료 환율           : ₩${lastRate.rate.toFixed(2)}`);
        lines.push(`  최고 환율           : ₩${maxRate.toFixed(2)}`);
        lines.push(`  최저 환율           : ₩${minRate.toFixed(2)}`);
        lines.push(`  환율 변동           : ${((lastRate.rate - firstRate.rate) / firstRate.rate * 100).toFixed(2)}%`);
        lines.push('');
      }
    }

    lines.push('='.repeat(80));
    lines.push('리포트 끝');
    lines.push('='.repeat(80));

    return lines.join('\n');
  };

  const downloadAsTextReport = () => {
    try {
      const reportText = generateReportText();
      const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `backtest-report-${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Report download failed:', error);
      alert('리포트 다운로드에 실패했습니다. 콘솔을 확인하세요.');
    }
  };

  // 데이터 유효성 검사
  if (!data) {
    return (
      <div className="mx-auto max-w-[1600px] rounded-[32px] border border-border/40 bg-card/30 p-12 text-center shadow-sm">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
          <AlertCircle className="h-8 w-8 text-yellow-600" />
        </div>
        <h3 className="text-xl font-semibold mb-2">데이터가 없습니다</h3>
        <p className="text-sm text-muted-foreground">백테스트를 실행해 주세요.</p>
      </div>
    );
  }

  // 포트폴리오 데이터 유효성 검사
  if (isPortfolio && (!('portfolio_composition' in data) || !data.portfolio_composition)) {
    return (
      <div className="mx-auto max-w-[1600px] rounded-[32px] border border-border/40 bg-card/30 p-12 text-center shadow-sm">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
          <AlertCircle className="h-8 w-8 text-yellow-600" />
        </div>
        <h3 className="text-xl font-semibold mb-2">포트폴리오 데이터가 없습니다</h3>
        <p className="text-sm text-muted-foreground">유효한 포트폴리오를 구성해 주세요.</p>
      </div>
    );
  }

  return (
    <div ref={resultsRef} className="mx-auto w-full max-w-screen-2xl space-y-6">
      {/* 리포트 다운로드 버튼 */}
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={downloadAsTextReport}>
          <FileDown className="w-4 h-4 mr-2" />
          리포트 다운로드
        </Button>
      </div>

      {/* 차트 섹션 */}
      <ChartsSection data={data} isPortfolio={isPortfolio} />
    </div>
  );
};

export default BacktestResults;
