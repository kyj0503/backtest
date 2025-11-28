import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight } from 'lucide-react';
import { Button } from '@/shared/ui/button';

export const HeroSection: React.FC = () => {
  return (
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

          <div className="mt-8 sm:mt-12 px-2">
            <img
              src="/images/landing/backtest-main.png"
              alt="백테스트 플랫폼 메인 화면"
              className="w-full max-w-6xl mx-auto rounded-2xl shadow-2xl border border-border/50"
            />
          </div>
        </div>
      </div>
    </section>
  );
};
