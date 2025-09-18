// 주가 변동성 및 뉴스 관련 타입 정의

export interface VolatilityEvent {
  date: string;
  daily_return: number;
  close_price: number;
  volume: number;
  event_type: string;
}

export interface NewsItem {
  title: string;
  description: string;
  link: string;
  pubDate: string;
  company: string;
}

export interface StockVolatilityNewsProps {
  symbols: string[];
  startDate: string;
  endDate: string;
  className?: string;
}

// 티커 심볼을 한국어 기업명으로 매핑 (백엔드와 동일한 매핑 사용)
export const TICKER_TO_COMPANY_NAME: { [key: string]: string } = {
  // 미국 주요 종목
  'AAPL': '애플',
  'MSFT': '마이크로소프트',
  'GOOGL': '구글',
  'GOOGLE': '구글',
  'AMZN': '아마존',
  'TSLA': '테슬라',
  'META': '메타',
  'NVDA': '엔비디아',
  'NFLX': '넷플릭스',
  'AMD': 'AMD',
  'INTC': '인텔',
  'CRM': '세일즈포스',
  'ORCL': '오라클',
  'ADBE': '어도비',
  'PYPL': '페이팔',
  'UBER': '우버',
  'SNAP': '스냅챗',
  'SPOT': '스포티파이',
  'SQ': '스퀘어',
  'ZOOM': '줌',
  'SHOP': '쇼피파이',
  'DOCU': '도큐사인',
  'TWTR': '트위터',
  'PINS': '핀터레스트',
  'DDOG': '데이터독',
  'CRWD': '크라우드스트라이크',
  'OKTA': '옥타',
  'ZM': '줌',
  'WORK': '슬랙',
  'TEAM': '아틀라시안',
  'NET': '클라우드플레어',
  'FSLY': '패스틀리',
  'MDB': '몽고DB',
  'SNOW': '스노우플레이크',
  'PLTR': '팔란티어',
  'ABNB': '에어비앤비',
  'DASH': '도어대시',
  'COIN': '코인베이스',
  'RBLX': '로블록스',
  'U': '유니티',
  'PATH': '유아이패스',
  'BILL': '빌닷컴',
  'ZS': '지스케일러',
  'ESTC': '일래스틱',
  'DBX': '드롭박스',
  'ZI': '젠데스크',
  'PD': '페이저듀티',
  'TWLO': '트윌리오',
  'VEEV': '비바',
  'WDAY': '워크데이',
  'SPLK': '스플렁크',
  'NOW': '서비스나우',
  'TTD': '더트레이드데스크',
  'ROKU': '로쿠',
  
  // 한국 주요 종목
  '005930': '삼성전자',
  '000660': 'SK하이닉스',
  '035420': 'NAVER',
  '051910': 'LG화학',
  '006400': '삼성SDI',
  '207940': '삼성바이오로직스',
  '035720': '카카오',
  '068270': '셀트리온',
  '028260': '삼성물산',
  '015760': '한국전력',
  '096770': 'SK이노베이션',
  '017670': 'SK텔레콤',
  '030200': 'KT',
  '033780': 'KT&G',
  '003550': 'LG',
  '066570': 'LG전자',
  '011200': 'HMM',
  '047810': '한국항공우주',
  '326030': 'SK바이오팜',
  '003670': '포스코홀딩스',
  '012330': '현대모비스',
  '005380': '현대차',
  '000270': '기아',
  '009150': '삼성전기',
  '018260': '삼성에스디에스'
};

// 유틸리티 함수들
export const getCompanyName = (ticker: string): string => {
  return TICKER_TO_COMPANY_NAME[ticker.toUpperCase()] || ticker;
};

export const formatPercent = (value: number): string => {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
};

export const formatPrice = (value: number): string => {
  return `$${value.toFixed(2)}`;
};

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost') {
      return 'http://localhost:8001';
    } else {
      return `${window.location.protocol}//${window.location.hostname}:8001`;
    }
  }
  return 'http://localhost:8001';
};
