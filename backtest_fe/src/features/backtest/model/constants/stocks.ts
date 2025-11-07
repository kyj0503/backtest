/**
 * 미리 정의된 주식 종목 목록
 */

export const PREDEFINED_STOCKS = [
  { value: 'CUSTOM', label: '직접 입력' },

  // 미국 주식 및 ETF (21개)
  { value: 'AAPL', label: 'AAPL - Apple Inc.' },
  { value: 'GOOGL', label: 'GOOGL - Alphabet Inc.' },
  { value: 'MSFT', label: 'MSFT - Microsoft Corp.' },
  { value: 'TSLA', label: 'TSLA - Tesla Inc.' },
  { value: 'AMZN', label: 'AMZN - Amazon.com Inc.' },
  { value: 'NVDA', label: 'NVDA - NVIDIA Corp.' },
  { value: 'META', label: 'META - Meta Platforms Inc.' },
  { value: 'NFLX', label: 'NFLX - Netflix Inc.' },
  { value: 'JPM', label: 'JPM - JPMorgan Chase & Co.' },
  { value: 'V', label: 'V - Visa Inc.' },
  { value: 'JNJ', label: 'JNJ - Johnson & Johnson' },
  { value: 'WMT', label: 'WMT - Walmart Inc.' },
  { value: 'PG', label: 'PG - Procter & Gamble Co.' },
  { value: 'DIS', label: 'DIS - Walt Disney Co.' },
  { value: 'BAC', label: 'BAC - Bank of America Corp.' },
  { value: 'CSCO', label: 'CSCO - Cisco Systems Inc.' },
  { value: 'INTC', label: 'INTC - Intel Corp.' },
  { value: 'AMD', label: 'AMD - Advanced Micro Devices Inc.' },
  { value: 'SPY', label: 'SPY - SPDR S&P 500 ETF' },
  { value: 'QQQ', label: 'QQQ - Invesco QQQ Trust' },
  { value: 'VTI', label: 'VTI - Vanguard Total Stock Market ETF' },

  // 한국 주식 (18개)
  { value: '005930.KS', label: '005930.KS - 삼성전자' },
  { value: '000660.KS', label: '000660.KS - SK하이닉스' },
  { value: '005380.KS', label: '005380.KS - 현대자동차' },
  { value: '000270.KS', label: '000270.KS - 기아' },
  { value: '035420.KS', label: '035420.KS - NAVER' },
  { value: '051910.KS', label: '051910.KS - LG화학' },
  { value: '006400.KS', label: '006400.KS - 삼성SDI' },
  { value: '035720.KS', label: '035720.KS - 카카오' },
  { value: '003550.KS', label: '003550.KS - LG' },
  { value: '017670.KS', label: '017670.KS - SK텔레콤' },
  { value: '096770.KS', label: '096770.KS - SK이노베이션' },
  { value: '034730.KS', label: '034730.KS - SK' },
  { value: '028260.KS', label: '028260.KS - 삼성물산' },
  { value: '012330.KS', label: '012330.KS - 현대모비스' },
  { value: '068270.KS', label: '068270.KS - 셀트리온' },
  { value: '207940.KS', label: '207940.KS - 삼성바이오로직스' },
  { value: '105560.KS', label: '105560.KS - KB금융' },
  { value: '055550.KS', label: '055550.KS - 신한지주' },
  { value: '086790.KS', label: '086790.KS - 하나금융지주' },
  { value: '015760.KS', label: '015760.KS - 한국전력' }
];

/**
 * 종목 심볼을 표시용 문자열로 변환
 */
export const getStockDisplayName = (symbol: string): string => {
  const stock = PREDEFINED_STOCKS.find(s => s.value === symbol);
  return stock ? stock.label : symbol;
};
