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

            {/* Hero Image - 메인 대표 이미지 */}
            <div className="mt-8 sm:mt-12 px-2">
              <img
                src="/public/images/landing/backtest-main.png"
                alt="백테스트 플랫폼 메인 화면"
                className="w-full max-w-6xl mx-auto rounded-2xl shadow-2xl border border-border/50"
              />
            </div>
          </div>
        </div>
      </section>

      {/* What is Backtesting */}
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

            {/* Process Illustration Image */}
            <div className="mt-8 sm:mt-12 px-2">
              <img
                src="/public/images/landing/backtest-result.png"
                alt="백테스트 프로세스"
                className="w-full max-w-6xl mx-auto rounded-2xl shadow-2xl border border-border/50"
              />
            </div>
          </div>
        </div>
      </section>

      {/* How to use */}
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
                  src="/public/images/landing/backtest-ticker.png"
                  alt="포트폴리오 구성 화면"
                  className="w-full rounded-lg shadow-md border border-border/30"
                />
              </div>
              <div className="p-6 rounded-2xl border border-border/50 hover:bg-muted/30 transition-colors">
                <h3 className="font-bold text-primary mb-2">Step 2. 전략 선택 및 설정</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  매수 후 보유(Buy & Hold)부터 이동평균, RSI 등 다양한 내장 전략 중 하나를 선택하세요. 각 전략의 세부 파라미터를 조정하여 최적의 설정을 찾을 수 있습니다.
                </p>
                <img
                  src="/public/images/landing/backtest-strategy.png"
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
                  src="/public/images/landing/backtest-date.png"
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
                  src="/public/images/landing/backtest-compare.png"
                  alt="결과 분석 화면"
                  className="w-full rounded-lg shadow-md border border-border/30"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
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

            {/* Feature Showcase Image */}
            <div className="mt-8 sm:mt-12 px-2">
              <img
                src="/public/images/landing/backtest-rebalance.png"
                alt="주요 기능 대시보드"
                className="w-full max-w-6xl mx-auto rounded-2xl shadow-2xl border border-border/50"
              />
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