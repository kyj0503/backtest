import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Activity, ArrowRight } from 'lucide-react';
import { Button } from '@/shared/ui/button';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-background via-background to-primary/5 pt-12 sm:pt-20 pb-20 sm:pb-32">
        <div className="container mx-auto px-4 sm:px-6 lg:max-w-5xl">
          <div className="text-center space-y-6 sm:space-y-8">
            <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 rounded-full bg-primary/10 text-primary text-xs sm:text-sm font-medium border border-primary/20">
              <Activity className="w-3 h-3 sm:w-4 sm:h-4" />
              투자 전략 검증 플랫폼
            </div>

            <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight leading-tight">
              <span className="text-foreground">
                백테스트로
              </span>
              <br />
              <span className="text-primary">
                전략을 검증하세요
              </span>
            </h1>

            <p className="text-base sm:text-xl md:text-2xl text-muted-foreground lg:max-w-2xl mx-auto leading-relaxed px-4">
              과거 데이터로 투자 전략을 시뮬레이션하고
              <br />
              실전 투자 전에 성과를 확인하세요
            </p>

            <div className="pt-2 sm:pt-4">
              <Button asChild size="lg" className="text-sm sm:text-base px-6 sm:px-8 py-4 sm:py-6 rounded-full shadow-lg hover:shadow-xl transition-all">
                <Link to="/backtest" className="inline-flex items-center gap-2">
                  시작하기
                  <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* What is Backtesting */}
      <section className="py-16 sm:py-24 bg-muted/30">
        <div className="container mx-auto px-4 sm:px-6 lg:max-w-4xl">
          <div className="space-y-8 sm:space-y-12">
            <div className="text-center space-y-3 sm:space-y-4 px-4">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">백테스트란?</h2>
              <p className="text-base sm:text-lg text-muted-foreground">
                과거 데이터로 투자 전략을 시뮬레이션하는 것입니다
              </p>
            </div>

            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-8 px-4">
              <div className="space-y-3 sm:space-y-4 text-center p-6 sm:p-8 rounded-2xl bg-background border border-border/50 hover:border-primary/30 transition-colors">
                <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                  <span className="text-xl sm:text-2xl font-bold text-primary">1</span>
                </div>
                <h3 className="text-base sm:text-lg font-semibold">전략 설정</h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  종목, 기간, 매매 전략을 선택합니다
                </p>
              </div>

              <div className="space-y-3 sm:space-y-4 text-center p-6 sm:p-8 rounded-2xl bg-background border border-border/50 hover:border-primary/30 transition-colors">
                <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                  <span className="text-xl sm:text-2xl font-bold text-primary">2</span>
                </div>
                <h3 className="text-base sm:text-lg font-semibold">시뮬레이션</h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  과거 데이터로 전략을 실행합니다
                </p>
              </div>

              <div className="space-y-3 sm:space-y-4 text-center p-6 sm:p-8 rounded-2xl bg-background border border-border/50 hover:border-primary/30 transition-colors">
                <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                  <span className="text-xl sm:text-2xl font-bold text-primary">3</span>
                </div>
                <h3 className="text-base sm:text-lg font-semibold">결과 분석</h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  수익률, 위험도 등을 확인합니다
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:max-w-4xl">
          <div className="space-y-10 sm:space-y-16">
            <div className="text-center space-y-3 sm:space-y-4 px-4">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">주요 기능</h2>
            </div>

            <div className="space-y-6 sm:space-y-8 px-4">
              <div className="flex items-start gap-4 sm:gap-6 p-4 sm:p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
                <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                </div>
                <div className="space-y-1 sm:space-y-2">
                  <h3 className="text-base sm:text-xl font-semibold">다양한 투자 전략</h3>
                  <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                    Buy & Hold, SMA, RSI, Bollinger Bands, MACD 등 다양한 기술적 지표 기반 전략을 테스트할 수 있습니다
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 sm:gap-6 p-4 sm:p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
                <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                </div>
                <div className="space-y-1 sm:space-y-2">
                  <h3 className="text-base sm:text-xl font-semibold">포트폴리오 리밸런싱</h3>
                  <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                    여러 자산을 조합한 포트폴리오를 구성하고, 주기적 리밸런싱 전략을 시뮬레이션할 수 있습니다
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 sm:gap-6 p-4 sm:p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
                <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                </div>
                <div className="space-y-1 sm:space-y-2">
                  <h3 className="text-base sm:text-xl font-semibold">상세한 성과 분석</h3>
                  <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                    수익률, 최대낙폭(MDD), 샤프 지수 등 핵심 지표와 벤치마크 대비 성과를 확인할 수 있습니다
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 sm:py-24 bg-gradient-to-b from-primary/5 to-background">
        <div className="container mx-auto px-4 sm:px-6 lg:max-w-3xl text-center space-y-6 sm:space-y-8">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold px-4">
            지금 바로 시작해보세요
          </h2>
          <p className="text-base sm:text-xl text-muted-foreground px-4">
            실제 돈을 투자하기 전에 전략을 검증하세요
          </p>
          <Button asChild size="lg" className="text-sm sm:text-base px-6 sm:px-8 py-4 sm:py-6 rounded-full shadow-lg hover:shadow-xl transition-all">
            <Link to="/backtest" className="inline-flex items-center gap-2">
              백테스트 시작하기
              <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default HomePage;