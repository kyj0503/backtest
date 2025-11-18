import React from 'react';
import { TrendingUp, Activity } from 'lucide-react';

export const KeyFeaturesSection: React.FC = () => {
  return (
    <section className="py-16 sm:py-24 bg-muted/30">
      <div className="container mx-auto px-4 sm:px-6 lg:max-w-6xl">
        <div className="space-y-10 sm:space-y-16">
          <div className="text-center space-y-3 sm:space-y-4 px-4">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">주요 기능</h2>
          </div>

          <div className="space-y-6 sm:space-y-8 px-4">
            <div className="flex items-start gap-4 sm:gap-6 p-4 sm:p-6 rounded-2xl border border-border/50 bg-background hover:bg-muted/30 transition-colors">
              <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
              </div>
              <div className="space-y-1 sm:space-y-2">
                <h3 className="text-base sm:text-xl font-semibold">다양한 투자 전략</h3>
                <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                  단순 보유부터 이동평균, RSI, 볼린저 밴드, MACD 등 널리 사용되는 기술적 지표 기반의 전략을 즉시 테스트하고 비교할 수 있습니다.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 sm:gap-6 p-4 sm:p-6 rounded-2xl border border-border/50 bg-background hover:bg-muted/30 transition-colors">
              <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
              </div>
              <div className="space-y-1 sm:space-y-2">
                <h3 className="text-base sm:text-xl font-semibold">포트폴리오 리밸런싱</h3>
                <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                  여러 자산을 조합한 포트폴리오를 구성하고, 주기적 리밸런싱, DCA(분할 매수) 등 고급 전략을 시뮬레이션하여 위험을 분산하고 수익을 최적화하세요.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 sm:gap-6 p-4 sm:p-6 rounded-2xl border border-border/50 bg-background hover:bg-muted/30 transition-colors">
              <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
              </div>
              <div className="space-y-1 sm:space-y-2">
                <h3 className="text-base sm:text-xl font-semibold">상세한 성과 분석</h3>
                <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                  단순 수익률을 넘어 최대 낙폭(MDD), 샤프 지수, 승률 등 핵심 성과 지표와 상세한 거래 내역을 제공하여 전략의 실제 성과를 깊이 있게 분석할 수 있습니다.
                </p>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 sm:gap-8 mt-8 sm:mt-12 px-2">
            <img
              src="/images/landing/backtest-rebalance 1.png"
              alt="주요 기능 대시보드"
              className="w-full rounded-2xl shadow-xl border border-border/50"
            />
            <img
              src="/images/landing/backtest-rebalance 2.png"
              alt="주요 기능 대시보드"
              className="w-full rounded-2xl shadow-xl border border-border/50"
            />
          </div>
        </div>
      </div>
    </section>
  );
};
