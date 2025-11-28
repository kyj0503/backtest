import React from 'react';

export const HowToUseSection: React.FC = () => {
  return (
    <section className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:max-w-6xl">
        <div className="space-y-10 sm:space-y-16">
          <div className="text-center space-y-3 sm:space-y-4 px-4">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">어떻게 사용하나요?</h2>
            <p className="text-base sm:text-lg text-muted-foreground">
              단 4단계로 나만의 투자 전략을 검증하고 개선할 수 있습니다.
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-6 sm:gap-8">
            <div className="p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
              <h3 className="font-bold text-primary mb-2">Step 1. 포트폴리오 구성</h3>
              <p className="text-sm text-muted-foreground mb-4">
                원하는 주식, ETF, 암호화폐 등 여러 종목을 담아 나만의 포트폴리오를 만드세요. 각 종목의 비중을 조절하여 다양한 자산 배분 전략을 테스트할 수 있습니다.
              </p>
              <img
                src="/images/landing/backtest-ticker.png"
                alt="포트폴리오 구성 화면"
                className="w-full rounded-lg shadow-md border border-border/30"
              />
            </div>
            <div className="p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
              <h3 className="font-bold text-primary mb-2">Step 2. 전략 선택 및 설정</h3>
              <p className="text-sm text-muted-foreground mb-4">
                매수 후 보유 전략부터 이동평균교차 전략, RSI 전략 등 다양한 내장 전략 중 하나를 선택하세요. 각 전략의 세부 파라미터를 조정하여 최적의 설정을 찾을 수 있습니다.
              </p>
              <img
                src="/images/landing/backtest-strategy.png"
                alt="전략 선택 화면"
                className="w-full rounded-lg shadow-md border border-border/30"
              />
            </div>
            <div className="p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
              <h3 className="font-bold text-primary mb-2">Step 3. 기간 및 조건 설정</h3>
              <p className="text-sm text-muted-foreground mb-4">
                백테스트를 실행할 기간과 초기 투자금, 수수료 등 상세한 조건을 설정하여 현실적인 시뮬레이션 환경을 구성합니다.
              </p>
              <img
                src="/images/landing/backtest-date.png"
                alt="기간 및 조건 설정 화면"
                className="w-full rounded-lg shadow-md border border-border/30"
              />
            </div>
            <div className="p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
              <h3 className="font-bold text-primary mb-2">Step 4. 결과 분석 및 개선</h3>
              <p className="text-sm text-muted-foreground mb-4">
                그래프와 통계 데이터를 통해 전략의 성과를 다각도로 분석하세요. 수익률, MDD, 승률 등 지표를 확인하고 전략을 수정하며 더 나은 투자 방법을 찾아보세요.
              </p>
              <img
                src="/images/landing/backtest-compare.png"
                alt="결과 분석 화면"
                className="w-full rounded-lg shadow-md border border-border/30"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
