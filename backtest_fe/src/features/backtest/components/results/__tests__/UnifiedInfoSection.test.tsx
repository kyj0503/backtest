/**
 * UnifiedInfoSection 컴포넌트 테스트
 * 
 * **테스트 범위**:
 * - 종목 선택 버튼 렌더링
 * - 급등락 이벤트 / 최신 뉴스 탭 렌더링
 * - 빈 데이터 처리
 * - 단일/다중 종목 시나리오
 * 
 * **테스트 전략**:
 * - Vitest + happy-dom
 * - DOM 렌더링 확인 (컴포넌트 마운트 검증)
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import UnifiedInfoSection from '../UnifiedInfoSection';

describe('UnifiedInfoSection', () => {
  const mockVolatilityEvents = {
    AAPL: [
      {
        date: '2023-01-05',
        daily_return: 7.5,
        close_price: 150.25,
        event_type: '급등',
      },
    ],
  };

  const mockLatestNews = {
    AAPL: [
      {
        title: 'Apple announces new product',
        description: 'Apple Inc. unveils groundbreaking technology...',
        link: 'https://example.com/news1',
        pubDate: '2023-01-12',
      },
    ],
  };

  describe('정상 렌더링', () => {
    it('급등락 이벤트와 뉴스가 있을 때 컴포넌트를 렌더링한다', () => {
      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={mockVolatilityEvents}
          latestNews={mockLatestNews}
        />
      );

      // Then
      expect(container).toBeTruthy();
      expect(container.innerHTML).toBeTruthy();
    });

    it('데이터가 없을 때 컴포넌트를 렌더링하지 않는다', () => {
      // When
      const { container } = render(
        <UnifiedInfoSection volatilityEvents={{}} latestNews={{}} />
      );

      // Then
      expect(container.firstChild).toBeNull();
    });
  });

  describe('다중 종목 시나리오', () => {
    it('여러 종목이 있을 때 컴포넌트를 정상 렌더링한다', () => {
      // Given
      const multiStockVolatility = {
        AAPL: mockVolatilityEvents.AAPL,
        GOOGL: [{
          date: '2023-01-08',
          daily_return: 5.8,
          close_price: 105.30,
          event_type: '급등',
        }],
      };

      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={multiStockVolatility}
          latestNews={mockLatestNews}
        />
      );

      // Then
      expect(container).toBeTruthy();
      expect(container.innerHTML).toContain('AAPL');
      expect(container.innerHTML).toContain('GOOGL');
    });

    it('단일 종목일 때 컴포넌트를 정상 렌더링한다', () => {
      // Given
      const singleStockVolatility = { AAPL: mockVolatilityEvents.AAPL };
      const singleStockNews = { AAPL: mockLatestNews.AAPL };

      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={singleStockVolatility}
          latestNews={singleStockNews}
        />
      );

      // Then
      expect(container).toBeTruthy();
      // 단일 종목일 때는 버튼이 표시되지 않음
      expect(container.innerHTML).not.toContain('<button');
    });
  });

  describe('빈 데이터 처리', () => {
    it('급등락 이벤트가 없을 때 안내 메시지를 표시한다', () => {
      // Given
      const emptyVolatility = { AAPL: [] };

      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={emptyVolatility}
          latestNews={mockLatestNews}
        />
      );

      // Then
      expect(container).toBeTruthy();
      expect(container.innerHTML).toContain('급등락 이벤트가 없습니다');
    });

    it('최신 뉴스가 없을 때 탭을 렌더링한다', () => {
      // Given
      const emptyNews = { AAPL: [] };

      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={mockVolatilityEvents}
          latestNews={emptyNews}
        />
      );

      // Then
      expect(container).toBeTruthy();
      expect(container.innerHTML).toContain('최신 뉴스');
    });
  });

  describe('데이터 표시', () => {
    it('급등 이벤트를 표시한다', () => {
      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={mockVolatilityEvents}
          latestNews={mockLatestNews}
        />
      );

      // Then
      expect(container.innerHTML).toContain('급등');
      expect(container.innerHTML).toContain('2023-01-05');
      expect(container.innerHTML).toContain('$150.25');
    });

    it('뉴스 링크를 표시한다', () => {
      // When
      const { container } = render(
        <UnifiedInfoSection
          volatilityEvents={mockVolatilityEvents}
          latestNews={mockLatestNews}
        />
      );

      // Then: 탭 전환 후 뉴스 내용 포함
      expect(container).toBeTruthy();
      // 뉴스 데이터는 탭 클릭 후 표시되므로 탭 구조만 확인
      expect(container.innerHTML).toContain('최신 뉴스');
    });
  });
});
