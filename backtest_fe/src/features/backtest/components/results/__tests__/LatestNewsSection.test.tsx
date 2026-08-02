/**
 * LatestNewsSection 컴포넌트 테스트
 *
 * **테스트 범위**:
 * - XSS 방지(P1-01): 네이버 뉴스 API의 title/description을
 *   dangerouslySetInnerHTML로 렌더링하면, 백엔드의 `<.*?>` 정규식 필터를
 *   닫히지 않은 태그로 우회한 악성 마크업이 실제 DOM 엘리먼트로 실행될 수 있다.
 *   텍스트로만 렌더링되어야 하며, 어떤 경우에도 엘리먼트가 생성되면 안 된다.
 * - HTML 엔티티 디코딩: 텍스트로 렌더링하더라도 `&quot;` 같은 엔티티는
 *   사람이 읽을 수 있는 문자로 보여야 한다.
 *
 * **테스트 전략**:
 * - Vitest + happy-dom
 * - 실제 렌더링 검증 (DOM 구조 / textContent)
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import LatestNewsSection from '../LatestNewsSection';
import type { NewsItem } from '../../../model/types/backtest-result-types';

describe('LatestNewsSection', () => {
  const baseNewsItem = {
    link: 'https://example.com/news/1',
    pubDate: 'Mon, 01 Sep 2025 21:01:00 +0900',
  };

  describe('XSS 방지 (P1-01)', () => {
    it('닫힌 <img onerror> 마크업이 엘리먼트로 실행되지 않고 원본 텍스트가 보인다', () => {
      // Given: 닫는 '>' 가 있는 악성 페이로드
      const maliciousTitle = `<img src=x onerror="document.title='pwned'">`;
      const newsItem: NewsItem = {
        ...baseNewsItem,
        title: maliciousTitle,
        description: '정상 설명',
      };

      // When
      const { container } = render(
        <LatestNewsSection latestNews={{ AAPL: [newsItem] }} />
      );

      // Then: img 엘리먼트가 생성되지 않아야 하고, 원본 문자열이 텍스트로 그대로 보여야 함
      expect(container.querySelector('img')).toBeNull();
      expect(container.textContent).toContain(maliciousTitle);
    });

    it('닫는 태그가 없는(unterminated) payload도 img 엘리먼트로 실행되지 않는다', () => {
      // Given: 백엔드의 `<.*?>` 정규식 필터를 우회하는, 닫히지 않은 태그
      // (정규식은 '>' 로 끝나야 매칭되므로 이 문자열은 그대로 통과한다)
      const unterminated = '<img src=x onerror=alert(1)';
      const newsItem: NewsItem = {
        ...baseNewsItem,
        title: '정상 제목',
        description: unterminated,
      };

      // When
      const { container } = render(
        <LatestNewsSection latestNews={{ AAPL: [newsItem] }} />
      );

      // Then
      expect(container.querySelector('img')).toBeNull();
    });
  });

  describe('HTML 엔티티 디코딩', () => {
    it('제목의 HTML 엔티티를 디코딩해 사람이 읽을 수 있는 텍스트로 표시한다', () => {
      // Given
      const newsItem: NewsItem = {
        ...baseNewsItem,
        title: 'AAPL &quot;beats&quot; &amp; rises',
        description: '정상 설명',
      };

      // When
      const { container } = render(
        <LatestNewsSection latestNews={{ AAPL: [newsItem] }} />
      );

      // Then
      expect(container.textContent).toContain('AAPL "beats" & rises');
    });

    it('유효한 숫자 엔티티(&#39;)는 정상적으로 디코딩한다', () => {
      // Given
      const newsItem: NewsItem = {
        ...baseNewsItem,
        title: 'AAPL&#39;s rally',
        description: '정상 설명',
      };

      // When
      const { container } = render(
        <LatestNewsSection latestNews={{ AAPL: [newsItem] }} />
      );

      // Then
      expect(container.textContent).toContain("AAPL's rally");
    });

    it('0x10FFFF를 초과하는 숫자 엔티티가 있어도 예외 없이 렌더링되고 원본 문자열이 보인다', () => {
      // Given: String.fromCodePoint가 RangeError를 던지는 범위 밖 코드포인트.
      // 뉴스 제목은 외부(네이버 API) 입력이므로 공격자가 값을 채울 수 있다.
      const oversizedEntityTitle = '가격 &#99999999999999; 급등';
      const newsItem: NewsItem = {
        ...baseNewsItem,
        title: oversizedEntityTitle,
        description: '정상 설명',
      };

      // When: 렌더링 자체가 예외를 던지면 안 됨 (ErrorBoundary가 잡더라도
      // 뉴스 섹션 전체가 죽는 것은 회귀)
      let renderResult: ReturnType<typeof render> | undefined;
      expect(() => {
        renderResult = render(
          <LatestNewsSection latestNews={{ AAPL: [newsItem] }} />
        );
      }).not.toThrow();

      // Then: 디코딩하지 못한 엔티티는 원본 문자열 그대로 보여야 함
      expect(renderResult?.container.textContent).toContain(oversizedEntityTitle);
    });
  });
});
