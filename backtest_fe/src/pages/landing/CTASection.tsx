import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/shared/ui/button';

export const CTASection: React.FC = () => {
  return (
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
  );
};
