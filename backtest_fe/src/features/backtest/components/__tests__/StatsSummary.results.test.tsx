/**
 * StatsSummary 성과 지표 카드 테스트 (A-12)
 *
 * 승률(Win_Rate)·프로핏 팩터(Profit_Factor)는 다른 작업에서 의미 통일과
 * "계산 불가 시 null" 처리를 진행 중이다. 그 두 카드의 값·라벨은 여기서
 * 단정하지 않는다. 나머지 지표와 조건부 카드(벤치마크·알파)만 고정한다.
 */
import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { TooltipProvider } from '@/shared/ui/tooltip'
import StatsSummary from '../StatsSummary'
import { makePortfolioStatistics } from '@/test/fixtures/backtestResults'

const renderStats = (stats: Record<string, unknown> | null | undefined) =>
  render(
    <TooltipProvider>
      <StatsSummary stats={stats} />
    </TooltipProvider>
  )

/** 라벨이 붙은 카드(h5 → CardContent)를 찾는다. */
const card = (label: string) => {
  const heading = screen.getByRole('heading', { name: label, level: 5 })
  return heading.parentElement as HTMLElement
}

describe('StatsSummary', () => {
  it('stats가 없으면 아무것도 그리지 않는다', () => {
    const { container: c1 } = renderStats(null)
    expect(c1.querySelector('section')).toBeNull()
    const { container: c2 } = renderStats(undefined)
    expect(c2.querySelector('section')).toBeNull()
  })

  it('포트폴리오 통계(PascalCase 키)로 주요 지표 카드를 그린다', () => {
    renderStats({ ...makePortfolioStatistics() })

    expect(screen.getByRole('heading', { name: '백테스트 성과' })).toBeInTheDocument()
    expect(within(card('총 수익률')).getByText('7.00%')).toBeInTheDocument()
    expect(within(card('거래일 수')).getByText('8')).toBeInTheDocument()
    expect(within(card('최대 손실')).getByText('-3.20%')).toBeInTheDocument()
    expect(within(card('샤프 비율')).getByText('1.10')).toBeInTheDocument()
    expect(within(card('연간 변동성')).getByText('18.00%')).toBeInTheDocument()
    // 포트폴리오 통계에는 Total_Trades가 없으므로 0으로 표시된다.
    expect(within(card('총 거래 횟수')).getByText('0')).toBeInTheDocument()
  })

  it('단일 종목 통계(snake_case 키)도 같은 카드로 보여 준다', () => {
    renderStats({
      total_return_pct: -4.25,
      max_drawdown_pct: -9.5,
      sharpe_ratio: -0.3,
      annual_volatility_pct: 30,
    })

    expect(within(card('총 수익률')).getByText('-4.25%')).toBeInTheDocument()
    expect(within(card('최대 손실')).getByText('-9.50%')).toBeInTheDocument()
    expect(within(card('샤프 비율')).getByText('-0.30')).toBeInTheDocument()
    expect(within(card('연간 변동성')).getByText('30.00%')).toBeInTheDocument()
  })

  it('숫자 문자열은 숫자로 해석하고, 해석할 수 없으면 0으로 표시한다', () => {
    renderStats({ Total_Return: '12.5', Sharpe_Ratio: 'abc' })

    expect(within(card('총 수익률')).getByText('12.50%')).toBeInTheDocument()
    expect(within(card('샤프 비율')).getByText('0.00')).toBeInTheDocument()
  })

  it('수익이면 양(초록), 손실이면 음(빨강) 톤으로 표시한다', () => {
    const { unmount } = renderStats({ Total_Return: 10 })
    expect(within(card('총 수익률')).getByText('10.00%').className).toMatch(/emerald/)
    unmount()

    renderStats({ Total_Return: -10 })
    expect(within(card('총 수익률')).getByText('-10.00%').className).toMatch(/destructive/)
  })

  it('변동성은 낮을수록 안정(초록), 높을수록 위험(빨강) 톤이다', () => {
    const { unmount } = renderStats({ Annual_Volatility: 10 })
    expect(within(card('연간 변동성')).getByText('10.00%').className).toMatch(/emerald/)
    unmount()

    const { unmount: unmount2 } = renderStats({ Annual_Volatility: 20 })
    expect(within(card('연간 변동성')).getByText('20.00%').className).toMatch(/text-foreground/)
    unmount2()

    renderStats({ Annual_Volatility: 40 })
    expect(within(card('연간 변동성')).getByText('40.00%').className).toMatch(/destructive/)
  })

  it('벤치마크·알파 필드가 없으면 해당 카드를 만들지 않는다', () => {
    renderStats({ ...makePortfolioStatistics() })

    expect(screen.queryByRole('heading', { name: /벤치마크/, level: 5 })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /알파/, level: 5 })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /S&P 500/, level: 5 })).not.toBeInTheDocument()
  })

  it('벤치마크·알파·S&P 500 필드가 있으면 추가 카드를 보여 준다', () => {
    renderStats({
      ...makePortfolioStatistics(),
      benchmark_total_return_pct: 5,
      benchmark_ticker: 'qqq',
      alpha_vs_benchmark_pct: 2,
      sp500_total_return_pct: 4,
      alpha_vs_sp500_pct: 3,
    })

    expect(within(card('벤치마크(QQQ) 수익률')).getByText('5.00%')).toBeInTheDocument()
    expect(within(card('알파 (벤치마크 대비)')).getByText('2.00%')).toBeInTheDocument()
    expect(within(card('S&P 500 수익률')).getByText('4.00%')).toBeInTheDocument()
    expect(within(card('S&P 500 대비 성과')).getByText('3.00%')).toBeInTheDocument()
  })

  it('벤치마크 티커가 없으면 일반 라벨을 쓴다', () => {
    renderStats({ benchmark_total_return_pct: -1 })
    expect(within(card('벤치마크 수익률')).getByText('-1.00%')).toBeInTheDocument()
  })
})
