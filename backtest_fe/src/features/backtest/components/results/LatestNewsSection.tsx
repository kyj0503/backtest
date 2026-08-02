/**
 * 최신 뉴스 섹션 컴포넌트
 * 
 * **역할**:
 * - 최신 뉴스만 별도 박스로 표시
 * - 여러 종목일 경우 종목 선택 버튼으로 전환
 * 
 * **UI 구조**:
 * - 종목 선택 버튼 (여러 종목일 때만 표시)
 * - 내용 영역: 선택된 종목의 최신 뉴스 리스트
 */
import React, { useState, useMemo } from 'react';
import { getStockDisplayName } from '../../model/strategyConfig';
import StockSymbolSelector from './StockSymbolSelector';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';
import { NewsItem } from '../../model/types/backtest-result-types';

interface LatestNewsSectionProps {
  latestNews: { [symbol: string]: NewsItem[] };
}

/** 이름 붙은 HTML 엔티티 중 뉴스 텍스트에 나타날 수 있는 것들만 다룬다. */
const NAMED_HTML_ENTITIES: Record<string, string> = {
  amp: '&',
  lt: '<',
  gt: '>',
  quot: '"',
  apos: "'",
  nbsp: ' ',
};

/**
 * HTML 엔티티만 디코딩한다 (예: &quot; -> ", &amp; -> &, &#39; -> ').
 *
 * **보안 참고 (P1-01)**: 네이버 뉴스 API의 title/description은 백엔드에서
 * `<.*?>` 정규식으로만 필터링되는데, 닫는 '>' 가 없는 태그(예:
 * `<img src=x onerror=alert(1)`)는 이 정규식을 그대로 통과한다. 과거에는
 * 이 값을 dangerouslySetInnerHTML로 렌더링해 그런 페이로드가 실제 DOM
 * 엘리먼트로 파싱·실행됐다.
 *
 * DOMParser/textarea.innerHTML 같은 HTML 파서 기반 디코딩은 일부러 쓰지
 * 않는다 — `<img ...>` 처럼 실제 태그처럼 보이는 부분을 파서가 (텍스트가
 * 아닌) 자식 엘리먼트로 해석해버리면 그 구간의 텍스트가 통째로 사라져,
 * 사용자가 원본 문자열을 확인할 수 없게 된다(테스트 환경인 happy-dom에서
 * 실측 확인: textarea.value가 빈 문자열을 반환했다). 아래처럼 '&...;'
 * 패턴만 치환하는 순수 문자열 처리는 파서 구현 차이에 좌우되지 않고,
 * '<', '>' 같은 문자는 (엔티티로 인코딩되지 않은 이상) 항상 그대로
 * 보존한다.
 *
 * 반환값은 반드시 일반 텍스트(JSX 텍스트 자식)로만 렌더링해야 한다.
 * 절대 innerHTML에 다시 주입하지 말 것 — 그러면 이 함수가 막으려는 것과
 * 동일한 문제가 재발한다.
 */
/** 유니코드에서 유효한 최대 코드포인트 (String.fromCodePoint의 상한). */
const MAX_UNICODE_CODE_POINT = 0x10ffff;

const decodeHtmlEntities = (value: string): string =>
  value.replace(/&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z]+);/g, (match, entity: string) => {
    if (entity[0] === '#') {
      const isHex = entity[1] === 'x' || entity[1] === 'X';
      const codePoint = parseInt(entity.slice(isHex ? 2 : 1), isHex ? 16 : 10);
      // 숫자 엔티티는 외부(네이버 API) 입력이라 공격자가 값을 채울 수 있다.
      // String.fromCodePoint는 0x10FFFF를 넘는 코드포인트에 RangeError를
      // 던지므로, 이름 없는 엔티티와 동일하게 원본 문자열을 그대로 둔다.
      return Number.isNaN(codePoint) || codePoint > MAX_UNICODE_CODE_POINT
        ? match
        : String.fromCodePoint(codePoint);
    }
    return NAMED_HTML_ENTITIES[entity] ?? match;
  });

/**
 * RFC 2822 형식의 날짜를 한국어 날짜 형식으로 변환 (시간 제외)
 * 예: "Mon, 01 Sep 2025 21:01:00 +0900" -> "2025년 9월 1일"
 */
const formatNewsDate = (pubDate: string): string => {
  try {
    const date = new Date(pubDate);
    if (isNaN(date.getTime())) {
      return pubDate; // 파싱 실패 시 원본 반환
    }
    
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    
    return `${year}년 ${month}월 ${day}일`;
  } catch {
    return pubDate; // 에러 발생 시 원본 반환
  }
};

const LatestNewsSection: React.FC<LatestNewsSectionProps> = ({
  latestNews,
}) => {
  // 뉴스가 있는 종목 목록
  const allSymbols = useMemo(() => {
    const symbols = Object.keys(latestNews || {}).filter(
      s => latestNews[s] && latestNews[s].length > 0
    );
    return symbols.sort();
  }, [latestNews]);

  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => allSymbols[0] || '');

  // 선택된 종목의 데이터
  const currentNews = latestNews?.[selectedSymbol] || [];

  // 데이터가 없으면 렌더링하지 않음
  if (allSymbols.length === 0) return null;

  return (
    <div className={CARD_STYLES.base}>
      <div className={`flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between ${SPACING.itemCompact} ${SPACING.contentGap}`}>
        <div className={SPACING.itemCompact}>
          <h3 className={HEADING_STYLES.h3}>최신 뉴스</h3>
          <p className={TEXT_STYLES.caption}>
            백테스트 기간과 관련된 최신 뉴스
          </p>
        </div>
      </div>

      {/* 종목 선택 버튼 (여러 종목일 때만 표시) */}
      <StockSymbolSelector
        symbols={allSymbols}
        selectedSymbol={selectedSymbol}
        onSelectSymbol={setSelectedSymbol}
        className={allSymbols.length > 1 ? SPACING.contentGap : ''}
      />

      {/* 최신 뉴스 내용 */}
      {currentNews.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          {getStockDisplayName(selectedSymbol)}의 최신 뉴스가 없습니다.
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
          {currentNews.map((newsItem, idx) => (
            <a
              key={idx}
              href={newsItem.link}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-2 rounded hover:bg-muted/50 transition-colors border-b border-border/40 last:border-0"
            >
              <div className="text-sm font-medium text-primary hover:underline">
                {decodeHtmlEntities(newsItem.title)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {decodeHtmlEntities(newsItem.description)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {formatNewsDate(newsItem.pubDate)}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
};

export default LatestNewsSection;
