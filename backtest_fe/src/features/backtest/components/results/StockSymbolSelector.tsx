/**
 * 종목 선택 버튼 공통 컴포넌트
 *
 * **역할**:
 * - 여러 종목 중 하나를 선택하는 버튼 그룹
 * - 티커 심볼을 보기 좋은 이름(한글/영문)으로 표시
 * - 급등락 이벤트, 최신 뉴스, 주가 차트 등에서 재사용
 *
 * **사용 예시**:
 * ```tsx
 * <StockSymbolSelector
 *   symbols={['AAPL', '005930.KS', 'GOOGL']}
 *   selectedSymbol={selectedSymbol}
 *   onSelectSymbol={setSelectedSymbol}
 * />
 * ```
 */
import React from 'react';
import { Button } from '@/shared/ui/button';
import { getStockDisplayName } from '../../model/strategyConfig';

interface StockSymbolSelectorProps {
  /** 표시할 종목 심볼 목록 */
  symbols: string[];
  /** 현재 선택된 종목 심볼 */
  selectedSymbol: string;
  /** 종목 선택 핸들러 */
  onSelectSymbol: (symbol: string) => void;
  /** 추가 CSS 클래스 */
  className?: string;
  /** 각 종목별 배지 숫자 (선택사항) */
  badges?: { [symbol: string]: number };
  /** 비활성화할 종목 목록 */
  disabledSymbols?: string[];
}

const StockSymbolSelector: React.FC<StockSymbolSelectorProps> = ({
  symbols,
  selectedSymbol,
  onSelectSymbol,
  className = '',
  badges,
  disabledSymbols = [],
}) => {
  // 종목이 1개 이하면 선택 버튼 표시하지 않음
  if (symbols.length <= 1) {
    return null;
  }

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {symbols.map((symbol) => {
        const displayName = getStockDisplayName(symbol);
        const badge = badges?.[symbol];
        const isDisabled = disabledSymbols.includes(symbol);

        return (
          <Button
            key={symbol}
            variant={selectedSymbol === symbol ? 'default' : 'outline'}
            size="sm"
            onClick={() => onSelectSymbol(symbol)}
            disabled={isDisabled}
            className="flex items-center gap-2"
          >
            {displayName}
            {badge !== undefined && badge > 0 && (
              <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                {badge}
              </span>
            )}
          </Button>
        );
      })}
    </div>
  );
};

export default StockSymbolSelector;
