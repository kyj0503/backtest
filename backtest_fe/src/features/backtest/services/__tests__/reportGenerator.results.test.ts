/**
 * reportGenerator(텍스트/CSV 리포트) 테스트 (A-12)
 *
 * 사용자가 내려받는 파일의 섹션 구성과 값을 고정한다. 승률·프로핏 팩터·연간
 * 수익률 줄은 다른 작업에서 의미·표시를 바꾸는 중이라 값과 라벨을 단정하지 않는다.
 */
import { describe, it, expect } from 'vitest'
import { generateCSVReport, generateTextReport } from '../reportGenerator'
import type {
  BacktestResultData,
  PortfolioData,
  TradeMarker,
} from '../../model/types/backtest-result-types'
import {
  RESULT_DATES,
  makePortfolioData,
  makeSingleStockData,
} from '@/test/fixtures/backtestResults'

const lines = (text: string) => text.split('\n')

describe('generateTextReport — 포트폴리오', () => {
  const report = generateTextReport(makePortfolioData(), true)

  it('머리말과 꼬리말을 갖는다', () => {
    expect(report).toContain('백테스트 결과 리포트')
    expect(report).toMatch(/생성 일시: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)
    expect(report.trimEnd().endsWith('='.repeat(80))).toBe(true)
    expect(report).toContain('리포트 끝')
  })

  it('구성 종목과 비중을 나열한다', () => {
    expect(report).toContain('[ 포트폴리오 백테스트 ]')
    expect(report).toContain('■ 포트폴리오 구성')
    expect(report).toMatch(/AAPL\s+- 비중: 60\.00%/)
    expect(report).toMatch(/MSFT\s+- 비중: 40\.00%/)
  })

  it('기간·자산가치·수익률·낙폭 등 주요 지표를 담는다', () => {
    expect(report).toContain(`백테스트 기간       : ${RESULT_DATES[0]} ~ ${RESULT_DATES[7]}`)
    expect(report).toContain('초기 자본금         : $10,000')
    expect(report).toContain('최종 자산가치       : $10,700')
    expect(report).toContain('총 수익률           : 7.00%')
    expect(report).toContain('최대 낙폭(MDD)      : -3.20%')
    expect(report).toContain('총 거래일수         : 8일')
  })

  it('개별 종목 수익률은 BE가 준 백분율을 그대로, 비중은 비율을 퍼센트로 보여 준다', () => {
    expect(report).toContain('■ 개별 종목 수익률')
    expect(report).toMatch(/AAPL\s+- 수익률: 8\.00%\s+\|\s+비중: 60\.00%/)
    expect(report).toMatch(/시작가: \$125\.00\s+\|\s+종료가: \$135\.00/)
  })

  it('환율 데이터가 없으면 환율 섹션을 넣지 않는다', () => {
    expect(report).not.toContain('환율 정보')
  })

  it('환율 데이터가 있으면 시작·종료·최고·최저·변동률을 요약한다', () => {
    const text = generateTextReport(
      makePortfolioData({
        exchange_rates: [
          { date: RESULT_DATES[0], rate: 1300 },
          { date: RESULT_DATES[1], rate: 1350 },
          { date: RESULT_DATES[2], rate: 1250 },
          { date: RESULT_DATES[3], rate: 1326 },
        ],
      }),
      true
    )
    expect(text).toContain('■ 환율 정보 (KRW/USD)')
    expect(text).toContain('시작 환율           : ₩1300.00')
    expect(text).toContain('종료 환율           : ₩1326.00')
    expect(text).toContain('최고 환율           : ₩1350.00')
    expect(text).toContain('최저 환율           : ₩1250.00')
    expect(text).toContain('환율 변동           : 2.00%')
  })

  it('isPortfolio=false로 포트폴리오 데이터를 넘기면 본문 없이 머리말·꼬리말만 만든다', () => {
    const text = generateTextReport(makePortfolioData(), false)
    expect(text).not.toContain('[ 포트폴리오 백테스트 ]')
    expect(text).not.toContain('[ 단일 종목 백테스트 ]')
    expect(text).toContain('리포트 끝')
  })
})

describe('generateTextReport — 단일 종목', () => {
  it('기본 정보·지표·거래 내역을 담는다', () => {
    const text = generateTextReport(makeSingleStockData(), false)

    expect(text).toContain('[ 단일 종목 백테스트 ]')
    expect(text).toContain('종목                : AAPL')
    expect(text).toContain('전략                : sma_strategy')
    expect(text).toContain('총 수익률           : 3.50%')
    expect(text).toContain('최대 낙폭(MDD)      : -2.10%')
    expect(text).toContain('총 거래 횟수: 4회')
    expect(text).toContain('타입       : 진입 (매수)')
    expect(text).toContain('타입       : 청산 (매도)')
    expect(text).toContain('손익률     : 1.96%')
    expect(text).toContain('수량       : 10')
  })

  it('값이 숫자가 아닌 지표는 N/A로 표시한다', () => {
    const text = generateTextReport(makeSingleStockData({ summary_stats: {} }), false)

    expect(text).toContain('총 수익률           : N/A%')
    expect(text).toContain('샤프 비율           : N/A')
    expect(text).toContain('총 거래 수          : 0회')
  })

  it('선택 지표(변동성·소르티노·칼마·알파·베타)는 있을 때만 넣는다', () => {
    const without = generateTextReport(makeSingleStockData(), false)
    expect(without).not.toContain('소르티노 비율')

    const withExtras = generateTextReport(
      makeSingleStockData({
        summary_stats: {
          total_return_pct: 1,
          volatility_pct: 12.345,
          sortino_ratio: 1.5,
          calmar_ratio: 0.8,
          alpha: 0.1,
          beta: 1.2,
        },
      }),
      false
    )
    expect(withExtras).toContain('변동성              : 12.35%')
    expect(withExtras).toContain('소르티노 비율       : 1.50')
    expect(withExtras).toContain('칼마 비율           : 0.80')
    expect(withExtras).toContain('알파                : 0.10')
    expect(withExtras).toContain('베타                : 1.20')
  })

  it('거래가 50건을 넘으면 앞 50건만 쓰고 나머지 수를 알린다', () => {
    const many: TradeMarker[] = Array.from({ length: 53 }, (_, i) => ({
      date: `2023-02-${String((i % 28) + 1).padStart(2, '0')}`,
      type: i % 2 === 0 ? 'entry' : 'exit',
      price: 100 + i,
    }))
    const text = generateTextReport(makeSingleStockData({ trade_markers: many }), false)

    expect(text).toContain('총 거래 횟수: 53회')
    expect(text).toContain('[거래 50]')
    expect(text).not.toContain('[거래 51]')
    expect(text).toContain('... 그 외 3개 거래 생략')
  })

  it('거래가 없으면 거래 내역 섹션을 넣지 않는다', () => {
    const text = generateTextReport(makeSingleStockData({ trade_markers: [] }), false)
    expect(text).not.toContain('■ 거래 내역')
  })
})

describe('generateCSVReport — 포트폴리오', () => {
  it('구성·지표·개별 수익률 섹션을 CSV 행으로 만든다', () => {
    const csv = lines(generateCSVReport(makePortfolioData(), true))

    expect(csv[0]).toBe('백테스트 결과 리포트 (CSV)')
    expect(csv).toContain('종목,비중(%)')
    expect(csv).toContain('AAPL,60.00')
    expect(csv).toContain('MSFT,40.00')
    expect(csv).toContain(`백테스트 시작일,${RESULT_DATES[0]}`)
    expect(csv).toContain('총 수익률,7.00%')
    expect(csv).toContain('최대 낙폭(MDD),-3.20%')
    expect(csv).toContain('종목,수익률(%),비중(%),시작가($),종료가($)')
    expect(csv).toContain('AAPL,8.00,60.00,125.00,135.00')
  })

  it('리밸런싱 이력이 있으면 주식 거래를 행마다 기록한다', () => {
    const csv = lines(
      generateCSVReport(
        makePortfolioData({
          rebalance_history: [
            {
              date: RESULT_DATES[4],
              trades: [
                { symbol: 'AAPL', action: 'sell', shares: 1.5, price: 130 },
                { symbol: 'MSFT', action: 'buy', shares: 0.8, price: 245 },
              ],
              weights_before: { AAPL: 0.62, MSFT: 0.38 },
              weights_after: { AAPL: 0.6, MSFT: 0.4 },
              commission_cost: 0.39,
            },
          ],
        }),
        true
      )
    )

    expect(csv).toContain('리밸런싱 히스토리')
    expect(csv).toContain(`${RESULT_DATES[4]},AAPL,매도,195.00,1.5000,130.00,0.39`)
    expect(csv).toContain(`${RESULT_DATES[4]},MSFT,매수,196.00,0.8000,245.00,0.39`)
  })

  it('현금 조정 거래(shares 없이 amount만 옴)도 CSV를 깨뜨리지 않는다', () => {
    // 백엔드 portfolio_rebalancer.py는 현금 비중 조정을 action 'increase'/'decrease',
    // shares 없이 amount·price(1.0)로 기록한다. 주식+현금 포트폴리오에 리밸런싱을
    // 켜면 흔히 나오는 형태다.
    const data = makePortfolioData({
      rebalance_history: [
        {
          date: RESULT_DATES[4],
          trades: [
            { symbol: 'AAPL', action: 'sell', shares: 2, price: 130 },
            { symbol: 'CASH', action: 'increase', amount: 260, price: 1 },
            { symbol: 'USD', action: 'decrease', amount: 50, price: 1 },
          ],
          weights_before: { AAPL: 0.55, CASH: 0.45 },
          weights_after: { AAPL: 0.5, CASH: 0.5 },
        },
      ],
    })

    const csv = lines(generateCSVReport(data, true))
    expect(csv).toContain(`${RESULT_DATES[4]},AAPL,매도,260.00,2.0000,130.00,0.00`)
    expect(csv).toContain(`${RESULT_DATES[4]},CASH,증가,260.00,N/A,1.00,0.00`)
    expect(csv).toContain(`${RESULT_DATES[4]},USD,감소,50.00,N/A,1.00,0.00`)
  })

  it('비중 변화는 첫날·마지막날·30일 간격으로 샘플링해 퍼센트로 쓴다', () => {
    const weightHistory = Array.from({ length: 65 }, (_, i) => ({
      date: `d${i}`,
      AAPL: 0.6,
      MSFT: 0.4,
    }))
    const csv = lines(generateCSVReport(makePortfolioData({ weight_history: weightHistory }), true))

    expect(csv).toContain('날짜,AAPL,MSFT')
    const rows = csv.filter((l) => /^d\d+,/.test(l))
    expect(rows.map((r) => r.split(',')[0])).toEqual(['d0', 'd30', 'd60', 'd64'])
    expect(rows[0]).toBe('d0,60.00%,40.00%')
  })

  it('비중 값이 숫자가 아니면 N/A로 쓴다', () => {
    const csv = lines(
      generateCSVReport(
        makePortfolioData({ weight_history: [{ date: 'd0', AAPL: 'x' }] }),
        true
      )
    )
    expect(csv).toContain('d0,N/A')
  })

  it('자산 가치 추이는 100건 이하면 그대로, 넘으면 7일 간격으로 줄인다', () => {
    const short = makePortfolioData() as BacktestResultData & { equity_data?: unknown }
    short.equity_data = RESULT_DATES.map((date, i) => ({ date, value: 100 + i }))
    const shortCsv = lines(generateCSVReport(short, true))
    expect(shortCsv).toContain('포트폴리오 자산 가치 추이 (주간 샘플링)')
    expect(shortCsv).toContain(`${RESULT_DATES[0]},100.00`)
    expect(shortCsv.filter((l) => /^2023-01-\d\d,\d+\.\d\d$/.test(l))).toHaveLength(8)

    const long = makePortfolioData() as BacktestResultData & { equity_data?: unknown }
    long.equity_data = Array.from({ length: 150 }, (_, i) => ({ date: `e${i}`, value: i }))
    const longCsv = lines(generateCSVReport(long, true))
    const rows = longCsv.filter((l) => /^e\d+,/.test(l))
    // 0, 7, ..., 147 (22개) + 마지막 149
    expect(rows).toHaveLength(23)
    expect(rows[rows.length - 1]).toBe('e149,149.00')
  })

  it('환율 요약에는 평균 환율까지 포함한다', () => {
    const csv = lines(
      generateCSVReport(
        makePortfolioData({
          exchange_rates: [
            { date: RESULT_DATES[0], rate: 1200 },
            { date: RESULT_DATES[1], rate: 1300 },
          ],
        }),
        true
      )
    )
    expect(csv).toContain('환율 정보 요약 (KRW/USD)')
    expect(csv).toContain('평균 환율,₩1250.00')
    expect(csv).toContain('환율 변동,8.33%')
  })
})

describe('개별 종목 수익률 — BE 응답 형태 (전략 포트폴리오)', () => {
  // run_strategy_portfolio_backtest의 individual_returns는 시작가·종료가 대신
  // initial_value/final_value를 싣는다. return은 이미 백분율이다.
  const strategyReturns = {
    AAPL: { symbol: 'AAPL', weight: 0.6, amount: 6000, return: 12.5, initial_value: 6000, final_value: 6750, trades: 4, win_rate: 50 },
    CASH: { symbol: 'CASH', weight: 0.4, amount: 4000, return: 0, initial_value: 4000, final_value: 4000, trades: 0, win_rate: 0 },
  } as unknown as PortfolioData['individual_returns']

  it('텍스트 리포트가 시작가 없는 항목에서 깨지지 않고 백분율을 그대로 쓴다', () => {
    const text = generateTextReport(makePortfolioData({ individual_returns: strategyReturns }), true)
    expect(text).toMatch(/AAPL\s+- 수익률: 12\.50%\s+\|\s+비중: 60\.00%/)
    expect(text).toMatch(/CASH\s+- 수익률: 0\.00%\s+\|\s+비중: 40\.00%/)
    expect(text).not.toContain('시작가: $undefined')
    expect(text).toMatch(/투자금: \$6000\.00\s+\|\s+최종 가치: \$6750\.00/)
  })

  it('CSV도 시작가·종료가가 없으면 N/A로 쓴다', () => {
    const csv = lines(generateCSVReport(makePortfolioData({ individual_returns: strategyReturns }), true))
    expect(csv).toContain('AAPL,12.50,60.00,N/A,N/A')
  })
})

describe('generateCSVReport — 단일 종목', () => {
  it('기본 정보·지표·거래 내역·자산 가치를 CSV로 만든다', () => {
    const csv = lines(generateCSVReport(makeSingleStockData(), false))

    expect(csv).toContain('종목,AAPL')
    expect(csv).toContain('전략,sma_strategy')
    expect(csv).toContain('총 수익률,3.50%')
    expect(csv).toContain('거래번호,날짜,타입,가격($),수량,손익률(%)')
    expect(csv).toContain(`1,${RESULT_DATES[1]},진입(매수),102.00,10,N/A`)
    expect(csv).toContain(`2,${RESULT_DATES[3]},청산(매도),104.00,N/A,1.96`)
    expect(csv).toContain('자산 가치 추이 (주간 샘플링)')
    expect(csv).toContain(`${RESULT_DATES[0]},10000.00`)
  })

  it('ticker가 없는 데이터는 빈 CSV를 만든다', () => {
    expect(generateCSVReport(makeSingleStockData({ ticker: undefined }), false)).toBe('')
  })
})
