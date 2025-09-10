import React, { useState, useEffect, useRef } from 'react';

interface Stock {
  symbol: string;
  name: string;
}

interface StockAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

// 주요 주식 목록 (실제 프로덕션에서는 API에서 가져와야 함)
const STOCK_SUGGESTIONS: Stock[] = [
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corporation' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.' },
  { symbol: 'TSLA', name: 'Tesla Inc.' },
  { symbol: 'META', name: 'Meta Platforms Inc.' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation' },
  { symbol: 'NFLX', name: 'Netflix Inc.' },
  { symbol: 'SPOT', name: 'Spotify Technology S.A.' },
  { symbol: 'CRM', name: 'Salesforce Inc.' },
  { symbol: 'ADBE', name: 'Adobe Inc.' },
  { symbol: 'PYPL', name: 'PayPal Holdings Inc.' },
  { symbol: 'INTC', name: 'Intel Corporation' },
  { symbol: 'AMD', name: 'Advanced Micro Devices Inc.' },
  { symbol: 'ORCL', name: 'Oracle Corporation' },
  { symbol: 'UBER', name: 'Uber Technologies Inc.' },
  { symbol: 'LYFT', name: 'Lyft Inc.' },
  { symbol: 'SNAP', name: 'Snap Inc.' },
  { symbol: 'TWTR', name: 'Twitter Inc.' },
  { symbol: 'SQ', name: 'Block Inc.' },
  { symbol: 'SHOP', name: 'Shopify Inc.' },
  { symbol: 'ZM', name: 'Zoom Video Communications Inc.' },
  { symbol: 'ROKU', name: 'Roku Inc.' },
  { symbol: 'DOCU', name: 'DocuSign Inc.' },
  { symbol: 'PLTR', name: 'Palantir Technologies Inc.' },
  { symbol: 'COIN', name: 'Coinbase Global Inc.' },
  { symbol: 'RBLX', name: 'Roblox Corporation' },
  { symbol: 'HOOD', name: 'Robinhood Markets Inc.' },
  { symbol: 'BB', name: 'BlackBerry Limited' },
  { symbol: 'NOK', name: 'Nokia Corporation' },
  { symbol: 'AMC', name: 'AMC Entertainment Holdings Inc.' },
  { symbol: 'GME', name: 'GameStop Corp.' },
  { symbol: 'BABA', name: 'Alibaba Group Holding Limited' },
  { symbol: 'JD', name: 'JD.com Inc.' },
  { symbol: 'NIO', name: 'NIO Inc.' },
  { symbol: 'XPEV', name: 'XPeng Inc.' },
  { symbol: 'LI', name: 'Li Auto Inc.' },
  { symbol: 'BIDU', name: 'Baidu Inc.' },
  { symbol: 'TCEHY', name: 'Tencent Holdings Limited' },
  { symbol: 'TSM', name: 'Taiwan Semiconductor Manufacturing Company Limited' },
  { symbol: 'V', name: 'Visa Inc.' },
  { symbol: 'MA', name: 'Mastercard Incorporated' },
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.' },
  { symbol: 'BAC', name: 'Bank of America Corporation' },
  { symbol: 'WFC', name: 'Wells Fargo & Company' },
  { symbol: 'GS', name: 'The Goldman Sachs Group Inc.' },
  { symbol: 'MS', name: 'Morgan Stanley' },
  { symbol: 'BRK.B', name: 'Berkshire Hathaway Inc.' },
  { symbol: 'JNJ', name: 'Johnson & Johnson' },
  { symbol: 'PFE', name: 'Pfizer Inc.' },
  { symbol: 'MRNA', name: 'Moderna Inc.' },
  { symbol: 'BNTX', name: 'BioNTech SE' },
  { symbol: 'KO', name: 'The Coca-Cola Company' },
  { symbol: 'PEP', name: 'PepsiCo Inc.' },
  { symbol: 'MCD', name: 'McDonald\'s Corporation' },
  { symbol: 'SBUX', name: 'Starbucks Corporation' },
  { symbol: 'DIS', name: 'The Walt Disney Company' },
  { symbol: 'WMT', name: 'Walmart Inc.' },
  { symbol: 'TGT', name: 'Target Corporation' },
  { symbol: 'HD', name: 'The Home Depot Inc.' },
  { symbol: 'LOW', name: 'Lowe\'s Companies Inc.' },
  { symbol: 'COST', name: 'Costco Wholesale Corporation' },
  { symbol: 'F', name: 'Ford Motor Company' },
  { symbol: 'GM', name: 'General Motors Company' },
  { symbol: 'BA', name: 'The Boeing Company' },
  { symbol: 'CAT', name: 'Caterpillar Inc.' },
  { symbol: 'GE', name: 'General Electric Company' },
  { symbol: '3M', name: '3M Company' },
  { symbol: 'IBM', name: 'International Business Machines Corporation' },
  { symbol: 'XOM', name: 'Exxon Mobil Corporation' },
  { symbol: 'CVX', name: 'Chevron Corporation' },
  { symbol: 'COP', name: 'ConocoPhillips' }
];

const StockAutocomplete: React.FC<StockAutocompleteProps> = ({
  value,
  onChange,
  placeholder = "종목 심볼 입력 (예: AAPL)",
  className = ""
}) => {
  const [suggestions, setSuggestions] = useState<Stock[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (value.length > 0) {
      const filteredSuggestions = STOCK_SUGGESTIONS.filter(stock =>
        stock.symbol.toLowerCase().includes(value.toLowerCase()) ||
        stock.name.toLowerCase().includes(value.toLowerCase())
      ).slice(0, 10); // 최대 10개 제한

      setSuggestions(filteredSuggestions);
      setShowSuggestions(filteredSuggestions.length > 0);
      setActiveSuggestion(-1);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const handleSuggestionClick = (stock: Stock) => {
    onChange(stock.symbol);
    setShowSuggestions(false);
    setActiveSuggestion(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveSuggestion(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (activeSuggestion >= 0 && suggestions[activeSuggestion]) {
          handleSuggestionClick(suggestions[activeSuggestion]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setActiveSuggestion(-1);
        break;
    }
  };

  const handleBlur = () => {
    // 약간의 지연을 두어 클릭 이벤트가 먼저 처리되도록 함
    setTimeout(() => {
      setShowSuggestions(false);
      setActiveSuggestion(-1);
    }, 150);
  };

  const handleFocus = () => {
    if (value.length > 0 && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  // 활성 제안 항목이 변경될 때 스크롤 조정
  useEffect(() => {
    if (activeSuggestion >= 0 && suggestionRefs.current[activeSuggestion]) {
      suggestionRefs.current[activeSuggestion]?.scrollIntoView({
        block: 'nearest'
      });
    }
  }, [activeSuggestion]);

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        onFocus={handleFocus}
        placeholder={placeholder}
        maxLength={10}
        className={`w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${className}`}
        autoComplete="off"
      />
      
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 z-50 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
          {suggestions.map((stock, index) => (
            <div
              key={stock.symbol}
              ref={el => suggestionRefs.current[index] = el}
              className={`px-3 py-2 cursor-pointer hover:bg-blue-50 ${
                index === activeSuggestion ? 'bg-blue-100' : ''
              }`}
              onClick={() => handleSuggestionClick(stock)}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm">{stock.symbol}</span>
                <span className="text-xs text-gray-500 truncate ml-2">{stock.name}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockAutocomplete;
