import React from 'react';

export const WhatIsBacktestSection: React.FC = () => {
  return (
    <section className="py-16 sm:py-24 bg-muted/30">
      <div className="container mx-auto px-4 sm:px-6 lg:max-w-6xl">
        <div className="space-y-8 sm:space-y-12">
          <div className="text-center space-y-3 sm:space-y-4 px-4">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">백테스트란?</h2>
            <p className="text-base sm:text-lg text-muted-foreground">
              과거의 시장은 미래를 위한 최고의 교과서입니다.<br />백테스트는 과거 데이터를 기반으로 투자 전략의 성과를 가상으로 검증하는 과정입니다.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-8 px-4">
            <div className="space-y-3 sm:space-y-4 text-center p-6 sm:p-8 rounded-2xl bg-background border border-border/50 hover:border-primary/30 transition-colors">
              <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                <span className="text-xl sm:text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="text-base sm:text-lg font-semibold">전략 수립</h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                어떤 종목을, 언제, 어떻게 사고팔지 자신만의 투자 규칙을 정합니다.
              </p>
            </div>

            <div className="space-y-3 sm:space-y-4 text-center p-6 sm:p-8 rounded-2xl bg-background border border-border/50 hover:border-primary/30 transition-colors">
              <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                <span className="text-xl sm:text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="text-base sm:text-lg font-semibold">시뮬레이션</h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                과거 시장 데이터에 수립한 전략을 적용하여 가상 매매를 실행합니다.
              </p>
            </div>

            <div className="space-y-3 sm:space-y-4 text-center p-6 sm:p-8 rounded-2xl bg-background border border-border/50 hover:border-primary/30 transition-colors">
              <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                <span className="text-xl sm:text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="text-base sm:text-lg font-semibold">결과 분석</h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                수익률, 최대 낙폭(MDD), 승률 등 성과 지표를 통해 전략의 강점과 약점을 파악합니다.
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 sm:gap-8 mt-8 sm:mt-12 px-2">
            <img
              src="/images/landing/backtest-result 1.png"
              alt="백테스트 프로세스"
              className="w-full rounded-2xl shadow-xl border border-border/50"
            />
            <img
              src="/images/landing/backtest-result 2.png"
              alt="백테스트 프로세스"
              className="w-full rounded-2xl shadow-xl border border-border/50"
            />
          </div>
        </div>
      </div>
    </section>
  );
};
