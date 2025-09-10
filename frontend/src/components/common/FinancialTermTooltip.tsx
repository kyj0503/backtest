import React, { useState } from 'react';

interface FinancialTermTooltipProps {
  term: string;
  children: React.ReactNode;
  className?: string;
}

// 금융용어 설명 데이터
const financialTerms: Record<string, string> = {
  '샤프 비율': '위험 대비 수익률을 측정하는 지표. 높을수록 좋음. (수익률 - 무위험수익률) / 변동성으로 계산됩니다.',
  '최대 손실': '백테스트 기간 중 최고점에서 최저점까지의 최대 하락폭. 투자 위험도를 나타냅니다.',
  '드로우다운': '최고점 대비 현재 손실률. 포트폴리오가 얼마나 하락했는지를 보여줍니다.',
  '변동성': '가격의 변동 정도를 나타내는 지표. 높을수록 위험하지만 수익 기회도 클 수 있습니다.',
  '수익률': '투자 원금 대비 얻은 이익의 비율. 연간수익률은 1년 기준으로 환산한 값입니다.',
  '승률': '전체 거래 중 수익을 낸 거래의 비율. 높을수록 안정적인 전략을 의미합니다.',
  '프로핏 팩터': '총 수익 / 총 손실 비율. 1보다 크면 수익성 있는 전략을 의미합니다.',
  '백테스트': '과거 데이터를 사용해 투자 전략의 성과를 미리 검증하는 방법입니다.',
  '포트폴리오': '여러 자산을 조합한 투자 묶음. 분산투자로 위험을 줄이는 효과가 있습니다.',
  '리밸런싱': '목표 비중에 맞게 포트폴리오를 주기적으로 조정하는 것입니다.',
  '분할매수': '일정 기간마다 같은 금액으로 매수하여 평균 단가를 낮추는 투자 방법입니다.',
  'DCA': 'Dollar Cost Averaging의 줄임말. 분할매수와 같은 의미입니다.',
  '환율': '두 국가 통화 간의 교환 비율. 해외 투자 시 수익률에 영향을 줍니다.',
  '거래수': '백테스트 기간 중 실행된 매매 거래의 총 횟수입니다.',
  '기간': '백테스트를 실행한 전체 날짜 범위를 의미합니다.',
  '초기자본': '백테스트 시작 시점의 투자 원금입니다.',
  '최종자본': '백테스트 종료 시점의 총 자산 가치입니다.',
  '최고자본': '백테스트 기간 중 달성한 최고 자산 가치입니다.',
  '매수보유': 'Buy and Hold. 매수 후 그대로 보유하는 장기투자 전략입니다.',
  'SMA': 'Simple Moving Average. 단순 이동평균선으로 가격 추세 분석에 사용됩니다.',
  'RSI': 'Relative Strength Index. 과매수/과매도 상태를 판단하는 기술적 지표입니다.',
  '이동평균': '일정 기간의 평균 가격을 선으로 연결한 기술적 분석 도구입니다.',
  '골든크로스': '단기 이동평균선이 장기 이동평균선을 상향 돌파하는 매수 신호입니다.',
  '데드크로스': '단기 이동평균선이 장기 이동평균선을 하향 돌파하는 매도 신호입니다.',
  '수수료': '거래 시 발생하는 비용. 백테스트에서 현실적인 결과를 위해 반영됩니다.',
  '슬리피지': '주문 가격과 실제 체결 가격의 차이. 유동성 부족 시 발생할 수 있습니다.',
  '베타': '시장 대비 개별 자산의 변동성 정도. 1보다 크면 시장보다 변동성이 큽니다.',
  'CAGR': 'Compound Annual Growth Rate. 연평균 복합 성장률로 장기 수익률을 나타냅니다.'
};

const FinancialTermTooltip: React.FC<FinancialTermTooltipProps> = ({ 
  term, 
  children, 
  className = "" 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  const explanation = financialTerms[term];
  
  if (!explanation) {
    return <>{children}</>;
  }

  return (
    <div 
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      <span className="cursor-help border-b border-dotted border-blue-400 text-blue-600">
        {children}
      </span>
      
      {isVisible && (
        <div className="absolute z-50 p-3 text-sm text-white bg-gray-800 rounded-lg shadow-lg max-w-xs min-w-48 bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          <div className="font-medium mb-1">{term}</div>
          <div className="text-gray-200">{explanation}</div>
          {/* 화살표 */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
        </div>
      )}
    </div>
  );
};

export default FinancialTermTooltip;
