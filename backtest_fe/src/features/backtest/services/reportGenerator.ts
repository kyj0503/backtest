import type {
  BacktestResultData,
  TradeMarker,
  ExchangeRatePoint,
  RebalanceEvent,
  RebalanceTrade,
  WeightHistoryPoint,
  EquityPoint
} from '../model/types/backtest-result-types';

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

export const generateTextReport = (data: BacktestResultData, isPortfolio: boolean): string => {
  const lines: string[] = [];
  const timestamp = new Date().toISOString().replace('T', ' ').split('.')[0];

  lines.push('='.repeat(80));
  lines.push('백테스트 결과 리포트');
  lines.push('='.repeat(80));
  lines.push(`생성 일시: ${timestamp}`);
  lines.push('');

  if (isPortfolio && 'portfolio_statistics' in data && data.portfolio_statistics) {
    lines.push('[ 포트폴리오 백테스트 ]');
    lines.push('');

    if ('portfolio_composition' in data && data.portfolio_composition) {
      lines.push('■ 포트폴리오 구성');
      lines.push('-'.repeat(80));
      data.portfolio_composition.forEach((stock) => {
        lines.push(`  ${stock.symbol.padEnd(10)} - 비중: ${(stock.weight * 100).toFixed(2)}%`);
      });
      lines.push('');
    }

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
    lines.push(`  프로핏 팩터         : ${stats.Profit_Factor.toFixed(2)}`);
    lines.push(`  연속 상승 최대      : ${stats.Max_Consecutive_Gains}일`);
    lines.push(`  연속 하락 최대      : ${stats.Max_Consecutive_Losses}일`);
    lines.push('');

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
    lines.push('[ 단일 종목 백테스트 ]');
    lines.push('');

    lines.push('■ 기본 정보');
    lines.push('-'.repeat(80));
    lines.push(`  종목                : ${data.ticker || 'N/A'}`);
    lines.push(`  전략                : ${data.strategy || 'N/A'}`);
    lines.push(`  백테스트 기간       : ${data.start_date || 'N/A'} ~ ${data.end_date || 'N/A'}`);
    lines.push('');

    if (data.summary_stats) {
      const stats = data.summary_stats as SummaryStats;
      lines.push('■ 주요 성과 지표');
      lines.push('-'.repeat(80));
      lines.push(`  총 수익률           : ${typeof stats.total_return_pct === 'number' ? stats.total_return_pct.toFixed(2) : 'N/A'}%`);
      lines.push(`  총 거래 수          : ${stats.total_trades || 0}회`);
      lines.push(`  승률                : ${typeof stats.win_rate_pct === 'number' ? stats.win_rate_pct.toFixed(2) : 'N/A'}%`);
      lines.push(`  최대 낙폭(MDD)      : ${typeof stats.max_drawdown_pct === 'number' ? stats.max_drawdown_pct.toFixed(2) : 'N/A'}%`);
      lines.push(`  샤프 비율           : ${typeof stats.sharpe_ratio === 'number' ? stats.sharpe_ratio.toFixed(2) : 'N/A'}`);
      lines.push(`  프로핏 팩터         : ${typeof stats.profit_factor === 'number' ? stats.profit_factor.toFixed(2) : 'N/A'}`);
      if (typeof stats.volatility_pct === 'number') lines.push(`  변동성              : ${stats.volatility_pct.toFixed(2)}%`);
      if (typeof stats.sortino_ratio === 'number') lines.push(`  소르티노 비율       : ${stats.sortino_ratio.toFixed(2)}`);
      if (typeof stats.calmar_ratio === 'number') lines.push(`  칼마 비율           : ${stats.calmar_ratio.toFixed(2)}`);
      if (typeof stats.alpha === 'number') lines.push(`  알파                : ${stats.alpha.toFixed(2)}`);
      if (typeof stats.beta === 'number') lines.push(`  베타                : ${stats.beta.toFixed(2)}`);
      lines.push('');
    }

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

export const generateCSVReport = (data: BacktestResultData, isPortfolio: boolean): string => {
  const csvRows: string[] = [];
  const timestamp = new Date().toISOString().replace('T', ' ').split('.')[0];

  if (isPortfolio && 'portfolio_statistics' in data && data.portfolio_statistics) {
    csvRows.push('백테스트 결과 리포트 (CSV)');
    csvRows.push(`생성 일시,${timestamp}`);
    csvRows.push('');

    if ('portfolio_composition' in data && data.portfolio_composition) {
      csvRows.push('포트폴리오 구성');
      csvRows.push('종목,비중(%)');
      data.portfolio_composition.forEach((stock) => {
        csvRows.push(`${stock.symbol},${(stock.weight * 100).toFixed(2)}`);
      });
      csvRows.push('');
    }

    const stats = data.portfolio_statistics;
    csvRows.push('주요 성과 지표');
    csvRows.push('항목,값');
    csvRows.push(`백테스트 시작일,${stats.Start}`);
    csvRows.push(`백테스트 종료일,${stats.End}`);
    csvRows.push(`운용 기간,${stats.Duration}`);
    csvRows.push(`초기 자본금,$${stats.Initial_Value.toLocaleString()}`);
    csvRows.push(`최종 자산가치,$${stats.Final_Value.toLocaleString()}`);
    csvRows.push(`최고 자산가치,$${stats.Peak_Value.toLocaleString()}`);
    csvRows.push(`총 수익률,${stats.Total_Return.toFixed(2)}%`);
    csvRows.push(`연간 수익률,${stats.Annual_Return.toFixed(2)}%`);
    csvRows.push(`연간 변동성,${stats.Annual_Volatility.toFixed(2)}%`);
    csvRows.push(`샤프 비율,${stats.Sharpe_Ratio.toFixed(2)}`);
    csvRows.push(`최대 낙폭(MDD),${stats.Max_Drawdown.toFixed(2)}%`);
    csvRows.push(`평균 낙폭,${stats.Avg_Drawdown.toFixed(2)}%`);
    csvRows.push(`총 거래일수,${stats.Total_Trading_Days}`);
    csvRows.push(`상승일수,${stats.Positive_Days}`);
    csvRows.push(`하락일수,${stats.Negative_Days}`);
    csvRows.push(`승률,${stats.Win_Rate.toFixed(2)}%`);
    csvRows.push(`프로핏 팩터,${stats.Profit_Factor.toFixed(2)}`);
    csvRows.push(`연속 상승 최대,${stats.Max_Consecutive_Gains}`);
    csvRows.push(`연속 하락 최대,${stats.Max_Consecutive_Losses}`);
    csvRows.push('');

    if ('individual_returns' in data && data.individual_returns) {
      csvRows.push('개별 종목 수익률');
      csvRows.push('종목,수익률(%),비중(%),시작가($),종료가($)');
      Object.entries(data.individual_returns).forEach(([symbol, info]) => {
        csvRows.push(`${symbol},${(info.return * 100).toFixed(2)},${(info.weight * 100).toFixed(2)},${info.start_price.toFixed(2)},${info.end_price.toFixed(2)}`);
      });
      csvRows.push('');
    }

    if ('rebalance_history' in data && Array.isArray(data.rebalance_history) && data.rebalance_history.length > 0) {
      csvRows.push('리밸런싱 히스토리');
      csvRows.push('날짜,종목,거래타입,거래금액($),거래수량,거래가격($),수수료($)');
      data.rebalance_history.forEach((event: RebalanceEvent) => {
        const trades = event.trades || [];
        trades.forEach((trade: RebalanceTrade) => {
          const value = trade.amount !== undefined ? trade.amount : (trade.shares * trade.price);
          csvRows.push(`${event.date},${trade.symbol},${trade.action === 'buy' ? '매수' : '매도'},${Math.abs(value).toFixed(2)},${trade.shares.toFixed(4)},${trade.price.toFixed(2)},${(event.commission_cost || 0).toFixed(2)}`);
        });
      });
      csvRows.push('');
    }

    if ('weight_history' in data && Array.isArray(data.weight_history) && data.weight_history.length > 0) {
      csvRows.push('포트폴리오 비중 변화 (매월 1일 기준)');

      const symbols = Object.keys(data.weight_history[0]).filter(key => key !== 'date');
      csvRows.push(`날짜,${symbols.join(',')}`);

      const weightHistory = data.weight_history;
      const sampledHistory = weightHistory.filter((_: WeightHistoryPoint, idx: number) => {
        return idx === 0 || idx === weightHistory.length - 1 || idx % 30 === 0;
      });

      sampledHistory.forEach((point: WeightHistoryPoint) => {
        const weights = symbols.map(symbol => {
          const weight = point[symbol];
          return typeof weight === 'number' ? (weight * 100).toFixed(2) + '%' : 'N/A';
        });
        csvRows.push(`${point.date},${weights.join(',')}`);
      });
      csvRows.push('');
    }

    if ('equity_data' in data && Array.isArray(data.equity_data) && data.equity_data.length > 0) {
      csvRows.push('포트폴리오 자산 가치 추이 (주간 샘플링)');
      csvRows.push('날짜,자산가치($)');

      const equityData = data.equity_data;
      const sampledEquity = equityData.length > 100
        ? equityData.filter((_: EquityPoint, idx: number) => idx % 7 === 0 || idx === equityData.length - 1)
        : equityData;

      sampledEquity.forEach((point: EquityPoint) => {
        const equityValue = point.value !== undefined ? point.value : (point as { equity?: number }).equity || 0;
        csvRows.push(`${point.date},${equityValue.toFixed(2)}`);
      });
      csvRows.push('');
    }

  } else if ('ticker' in data && data.ticker) {
    csvRows.push('백테스트 결과 리포트 (CSV)');
    csvRows.push(`생성 일시,${timestamp}`);
    csvRows.push('');

    csvRows.push('기본 정보');
    csvRows.push('항목,값');
    csvRows.push(`종목,${data.ticker || 'N/A'}`);
    csvRows.push(`전략,${data.strategy || 'N/A'}`);
    csvRows.push(`백테스트 시작일,${data.start_date || 'N/A'}`);
    csvRows.push(`백테스트 종료일,${data.end_date || 'N/A'}`);
    csvRows.push('');

    if (data.summary_stats) {
      const stats = data.summary_stats as SummaryStats;
      csvRows.push('주요 성과 지표');
      csvRows.push('항목,값');
      csvRows.push(`총 수익률,${typeof stats.total_return_pct === 'number' ? stats.total_return_pct.toFixed(2) : 'N/A'}%`);
      csvRows.push(`총 거래 수,${stats.total_trades || 0}`);
      csvRows.push(`승률,${typeof stats.win_rate_pct === 'number' ? stats.win_rate_pct.toFixed(2) : 'N/A'}%`);
      csvRows.push(`최대 낙폭(MDD),${typeof stats.max_drawdown_pct === 'number' ? stats.max_drawdown_pct.toFixed(2) : 'N/A'}%`);
      csvRows.push(`샤프 비율,${typeof stats.sharpe_ratio === 'number' ? stats.sharpe_ratio.toFixed(2) : 'N/A'}`);
      csvRows.push(`프로핏 팩터,${typeof stats.profit_factor === 'number' ? stats.profit_factor.toFixed(2) : 'N/A'}`);
      if (typeof stats.volatility_pct === 'number') csvRows.push(`변동성,${stats.volatility_pct.toFixed(2)}%`);
      if (typeof stats.sortino_ratio === 'number') csvRows.push(`소르티노 비율,${stats.sortino_ratio.toFixed(2)}`);
      if (typeof stats.calmar_ratio === 'number') csvRows.push(`칼마 비율,${stats.calmar_ratio.toFixed(2)}`);
      if (typeof stats.alpha === 'number') csvRows.push(`알파,${stats.alpha.toFixed(2)}`);
      if (typeof stats.beta === 'number') csvRows.push(`베타,${stats.beta.toFixed(2)}`);
      csvRows.push('');
    }

    if (data.trade_markers && data.trade_markers.length > 0) {
      csvRows.push('거래 내역');
      csvRows.push('거래번호,날짜,타입,가격($),수량,손익률(%)');
      data.trade_markers.forEach((trade: TradeMarker, idx) => {
        const type = trade.type === 'entry' ? '진입(매수)' : '청산(매도)';
        const price = (trade.price !== null && trade.price !== undefined && typeof trade.price === 'number')
          ? trade.price.toFixed(2) : 'N/A';
        const quantity = trade.quantity || 'N/A';
        const pnl = (trade.pnl_pct !== null && trade.pnl_pct !== undefined && typeof trade.pnl_pct === 'number')
          ? trade.pnl_pct.toFixed(2) : 'N/A';
        csvRows.push(`${idx + 1},${trade.date},${type},${price},${quantity},${pnl}`);
      });
      csvRows.push('');
    }

    if ('equity_data' in data && Array.isArray(data.equity_data) && data.equity_data.length > 0) {
      csvRows.push('자산 가치 추이 (주간 샘플링)');
      csvRows.push('날짜,자산가치($)');

      const equityData = data.equity_data;
      const sampledEquity = equityData.length > 100
        ? equityData.filter((_: EquityPoint, idx: number) => idx % 7 === 0 || idx === equityData.length - 1)
        : equityData;

      sampledEquity.forEach((point: EquityPoint) => {
        const equityValue = point.value !== undefined ? point.value : (point as { equity?: number }).equity || 0;
        csvRows.push(`${point.date},${equityValue.toFixed(2)}`);
      });
      csvRows.push('');
    }
  }

  if ('exchange_rates' in data && data.exchange_rates && data.exchange_rates.length > 0) {
    const rates = data.exchange_rates.filter((r): r is ExchangeRatePoint => r !== null && typeof r.rate === 'number');

    if (rates.length > 0) {
      const firstRate = rates[0];
      const lastRate = rates[rates.length - 1];
      const maxRate = Math.max(...rates.map((r) => r.rate));
      const minRate = Math.min(...rates.map((r) => r.rate));
      const avgRate = rates.reduce((sum, r) => sum + r.rate, 0) / rates.length;

      csvRows.push('환율 정보 요약 (KRW/USD)');
      csvRows.push('항목,값');
      csvRows.push(`시작 환율,₩${firstRate.rate.toFixed(2)}`);
      csvRows.push(`종료 환율,₩${lastRate.rate.toFixed(2)}`);
      csvRows.push(`최고 환율,₩${maxRate.toFixed(2)}`);
      csvRows.push(`최저 환율,₩${minRate.toFixed(2)}`);
      csvRows.push(`평균 환율,₩${avgRate.toFixed(2)}`);
      csvRows.push(`환율 변동,${((lastRate.rate - firstRate.rate) / firstRate.rate * 100).toFixed(2)}%`);
      csvRows.push('');
    }
  }

  return csvRows.join('\n');
};
