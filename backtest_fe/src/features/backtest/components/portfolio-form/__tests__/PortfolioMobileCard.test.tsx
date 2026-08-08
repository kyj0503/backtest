/**
 * PortfolioMobileCard 접근성 테스트 (P2-32)
 *
 * FormField.tsx:104-110과 같은 패턴: <Label>이 옆에 렌더링만 될 뿐 어떤
 * 컨트롤과도 프로그램적으로 연결되지 않았고, 여러 개의 bare Select
 * 트리거(종목/자산 타입/투자 방식/DCA 주기)도 접근 가능한 이름이 없었다.
 * PortfolioTable.tsx가 자신의 Input들에 aria-label을 붙이는 것을 참고해
 * (index+1)번째 형식의 aria-label로 통일한다.
 */
import type { ReactElement } from 'react'
import { describe, it, expect, vi } from 'vitest'
// @/test/utils의 render는 BrowserRouter만 감싸고, wrapper 옵션은 타입에서
// 아예 제외되어 있다(Omit<RenderOptions, 'wrapper'>). PortfolioMobileCard는
// FinancialTermTooltip(Radix Tooltip)을 쓰므로 TooltipProvider가 없으면
// "Tooltip must be used within TooltipProvider"로 렌더링 자체가 실패한다.
// test/utils.tsx 수정은 이 작업 범위 밖이라, Router가 필요 없는 이 컴포넌트는
// @testing-library/react의 원본 render를 직접 써서 TooltipProvider로 감싼다.
import { render, screen } from '@testing-library/react'
import { TooltipProvider } from '@/shared/ui/tooltip'
import { PortfolioMobileCard } from '../PortfolioMobileCard'
import type { Stock } from '../../../model/types/backtest-form-types'
import { ASSET_TYPES } from '../../../model/strategyConfig'

const renderWithTooltip = (ui: ReactElement) =>
  render(<TooltipProvider>{ui}</TooltipProvider>)

const stockAsset: Stock = {
  symbol: 'AAPL',
  amount: 10000,
  investmentType: 'lump_sum',
  assetType: ASSET_TYPES.STOCK,
}

const cashAsset: Stock = {
  symbol: 'CASH',
  amount: 5000,
  investmentType: 'lump_sum',
  assetType: ASSET_TYPES.CASH,
}

const dcaAsset: Stock = {
  ...stockAsset,
  investmentType: 'dca',
  dcaFrequency: 'monthly_1',
}

describe('PortfolioMobileCard 접근성 (P2-32)', () => {
  it('현금 자산 이름 입력이 접근 가능한 이름을 갖는다', () => {
    renderWithTooltip(
      <PortfolioMobileCard
        stock={cashAsset}
        index={0}
        portfolio={[cashAsset]}
        portfolioInputMode="amount"
        updateStock={vi.fn()}
        removeStock={vi.fn()}
        startDate="2023-01-01"
        endDate="2023-12-31"
      />
    )

    expect(screen.getByRole('textbox', { name: /1번째 현금 자산 이름/ })).toBeInTheDocument()
  })

  it('종목 선택 Select와 투자 금액 입력, 자산 타입/투자 방식 Select가 접근 가능한 이름을 갖는다', () => {
    renderWithTooltip(
      <PortfolioMobileCard
        stock={stockAsset}
        index={0}
        portfolio={[stockAsset]}
        portfolioInputMode="amount"
        updateStock={vi.fn()}
        removeStock={vi.fn()}
        startDate="2023-01-01"
        endDate="2023-12-31"
      />
    )

    expect(screen.getByRole('combobox', { name: /1번째 종목 선택/ })).toBeInTheDocument()
    expect(screen.getByRole('spinbutton', { name: /1번째 종목 투자 금액/ })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /1번째 자산 타입/ })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /1번째 투자 방식/ })).toBeInTheDocument()
  })

  it('종목 심볼이 커스텀(사전 정의 목록에 없음)이면 심볼 직접 입력란도 접근 가능한 이름을 갖는다', () => {
    const customStock: Stock = { ...stockAsset, symbol: 'ZZZZ' }
    renderWithTooltip(
      <PortfolioMobileCard
        stock={customStock}
        index={2}
        portfolio={[customStock]}
        portfolioInputMode="amount"
        updateStock={vi.fn()}
        removeStock={vi.fn()}
        startDate="2023-01-01"
        endDate="2023-12-31"
      />
    )

    expect(screen.getByRole('textbox', { name: /3번째 종목 심볼/ })).toBeInTheDocument()
  })

  it('DCA 투자 방식이면 DCA 주기 Select도 접근 가능한 이름을 갖는다', () => {
    renderWithTooltip(
      <PortfolioMobileCard
        stock={dcaAsset}
        index={1}
        portfolio={[dcaAsset]}
        portfolioInputMode="amount"
        updateStock={vi.fn()}
        removeStock={vi.fn()}
        startDate="2023-01-01"
        endDate="2023-12-31"
      />
    )

    expect(screen.getByRole('combobox', { name: /2번째 DCA 투자 주기/ })).toBeInTheDocument()
  })

  it('비중 모드에서는 비중 입력이 접근 가능한 이름을 갖는다', () => {
    const weighted: Stock = { ...stockAsset, weight: 50 }
    renderWithTooltip(
      <PortfolioMobileCard
        stock={weighted}
        index={0}
        portfolio={[weighted]}
        portfolioInputMode="weight"
        updateStock={vi.fn()}
        removeStock={vi.fn()}
        startDate="2023-01-01"
        endDate="2023-12-31"
      />
    )

    expect(screen.getByRole('spinbutton', { name: /1번째 종목 비중/ })).toBeInTheDocument()
  })
})
