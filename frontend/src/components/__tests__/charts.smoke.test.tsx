import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import EquityChart from '../EquityChart'
import OHLCChart from '../OHLCChart'
import StockPriceChart from '../StockPriceChart'
import TradesChart from '../TradesChart'

describe('Chart components (smoke)', () => {
  it('EquityChart renders an SVG with minimal data', () => {
    const { container } = render(
      <EquityChart
        data={[
          { date: '2023-01-01', return_pct: 0, drawdown_pct: 0 },
          { date: '2023-01-02', return_pct: 1.2, drawdown_pct: -0.5 },
        ]}
      />
    )
    expect(container.firstChild).toBeTruthy()
  })

  it('OHLCChart renders with minimal OHLC + empty indicators/trades', () => {
    const { container } = render(
      <OHLCChart
        data={[{ date: '2023-01-01', open: 1, high: 2, low: 0.5, close: 1.5, volume: 1000 }]}
        indicators={[]}
        trades={[]}
      />
    )
    expect(container.firstChild).toBeTruthy()
  })

  it('StockPriceChart renders with one stock dataset', () => {
    const { container, getByText } = render(
      <StockPriceChart
        stocksData={[{
          symbol: 'AAPL',
          data: [
            { date: '2023-01-01', price: 150 },
            { date: '2023-01-02', price: 151 },
          ],
        }]}
      />
    )
    expect(getByText('AAPL')).toBeInTheDocument()
    expect(container.firstChild).toBeTruthy()
  })

  it('TradesChart renders fallback for no exit trades and renders chart with exits', () => {
    // Fallback message
    const { rerender, getByText, container } = render(
      <TradesChart trades={[{ date: '2023-01-01', type: 'entry', price: 1 }]} />
    )
    expect(getByText('표시할 거래 데이터가 없습니다.')).toBeInTheDocument()

    // With exit trades
    rerender(
      <TradesChart trades={[{ date: '2023-01-02', type: 'exit', pnl_pct: 5 }]} />
    )
    expect(container.firstChild).toBeTruthy()
  })
})
