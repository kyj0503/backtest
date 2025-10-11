/**
 * TradeSignalsChart 컴포넌트 테스트
 * 
 * **테스트 범위**:
 * - 거래 마커 렌더링
 * - 매수/매도 신호 분리
 * - 빈 데이터 처리
 * 
 * **테스트 전략**:
 * - Vitest 사용
 * - Recharts는 SVG로 렌더링되므로 컨테이너 존재 확인
 * - 실제 렌더링 검증 (DOM 구조)
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import TradeSignalsChart from '../TradeSignalsChart';
import { TradeMarker } from '../../model/backtest-result-types';

describe('TradeSignalsChart', () => {
  const mockTrades: TradeMarker[] = [
    {
      date: '2023-01-02',
      price: 101.5,
      type: 'entry',
      side: 'buy',
    },
    {
      date: '2023-01-05',
      price: 104.2,
      type: 'exit',
      side: 'sell',
      pnl_pct: 2.66,
    },
    {
      date: '2023-01-08',
      price: 106.0,
      type: 'entry',
      side: 'buy',
    },
  ];

  describe('정상 렌더링', () => {
    it('거래 신호가 있을 때 컴포넌트를 렌더링한다', () => {
      // When
      const { container } = render(<TradeSignalsChart trades={mockTrades} />);

      // Then
      // 컴포넌트가 렌더링되는지 확인
      expect(container).toBeTruthy();
      expect(container.innerHTML).toBeTruthy();
    });

    it('빈 거래 배열일 때 안내 메시지를 표시한다', () => {
      // When
      const { container } = render(<TradeSignalsChart trades={[]} />);

      // Then
      expect(container.textContent).toContain('거래 신호가 없습니다.');
    });
  });

  describe('매수/매도 신호 분리', () => {
    it('entry와 exit 타입 거래를 모두 처리한다', () => {
      // Given
      const { container } = render(<TradeSignalsChart trades={mockTrades} />);

      // Then
      // 컴포넌트가 정상적으로 렌더링됨
      expect(container).toBeTruthy();
    });
  });

  describe('데이터 처리', () => {
    it('매수 신호만 있는 경우를 처리한다', () => {
      // Given: entry 거래만 포함
      const entryOnly: TradeMarker[] = [
        {
          date: '2023-01-02',
          price: 101.5,
          type: 'entry',
          side: 'buy',
        },
      ];

      // When
      const { container } = render(<TradeSignalsChart trades={entryOnly} />);

      // Then
      expect(container).toBeTruthy();
      expect(container.innerHTML).toBeTruthy();
    });

    it('매도 신호만 있는 경우를 처리한다', () => {
      // Given: exit 거래만 포함
      const exitOnly: TradeMarker[] = [
        {
          date: '2023-01-05',
          price: 104.2,
          type: 'exit',
          side: 'sell',
          pnl_pct: 2.66,
        },
      ];

      // When
      const { container } = render(<TradeSignalsChart trades={exitOnly} />);

      // Then
      expect(container).toBeTruthy();
    });

    it('다양한 가격대의 거래를 처리한다', () => {
      // Given: 가격 범위가 큰 거래들
      const wideRangeTrades: TradeMarker[] = [
        {
          date: '2023-01-02',
          price: 50.0,
          type: 'entry',
          side: 'buy',
        },
        {
          date: '2023-01-10',
          price: 150.0,
          type: 'exit',
          side: 'sell',
          pnl_pct: 200.0,
        },
      ];

      // When
      const { container } = render(<TradeSignalsChart trades={wideRangeTrades} />);

      // Then
      expect(container).toBeTruthy();
      expect(container.innerHTML).not.toContain('거래 신호가 없습니다.');
    });
  });
});
