/**
 * PortfolioSummary 접근성 테스트 (P2-32)
 *
 * FormField.tsx와 같은 패턴: <Label>이 <Input> 옆에 렌더링만 될 뿐
 * htmlFor/id로 묶이지 않아 "전체 투자금액($)" 입력이 스크린리더에게
 * 무명이었다.
 */
import { describe, it, expect, vi } from 'vitest'
// @/test/utils의 render는 BrowserRouter만 감싸고, wrapper 옵션은 타입에서
// 아예 제외되어 있다(Omit<RenderOptions, 'wrapper'>). PortfolioSummary는
// FinancialTermTooltip(Radix Tooltip)을 쓰므로 TooltipProvider가 없으면
// "Tooltip must be used within TooltipProvider"로 렌더링 자체가 실패한다.
// test/utils.tsx 수정은 이 작업 범위 밖이라, Router가 필요 없는 이 컴포넌트는
// @testing-library/react의 원본 render를 직접 써서 TooltipProvider로 감싼다.
import { render, screen } from '@testing-library/react'
import { TooltipProvider } from '@/shared/ui/tooltip'
import { PortfolioSummary } from '../PortfolioSummary'
import type { Stock } from '../../../model/types/backtest-form-types'

const portfolio: Stock[] = [
  { symbol: 'AAPL', amount: 5000, weight: 50, investmentType: 'lump_sum', assetType: 'stock' },
  { symbol: 'GOOGL', amount: 5000, weight: 50, investmentType: 'lump_sum', assetType: 'stock' },
]

describe('PortfolioSummary 접근성 (P2-32)', () => {
  it('비중 모드에서 전체 투자금액 입력이 label과 프로그램적으로 연결된다', () => {
    render(
      <TooltipProvider>
        <PortfolioSummary
          portfolio={portfolio}
          portfolioInputMode="weight"
          totalInvestment={10000}
          setTotalInvestment={vi.fn()}
          startDate="2023-01-01"
          endDate="2023-12-31"
        />
      </TooltipProvider>
    )

    expect(screen.getByRole('spinbutton', { name: /전체 투자금액/ })).toBeInTheDocument()
  })
})
