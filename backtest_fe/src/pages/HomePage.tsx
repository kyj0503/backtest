import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine, FaCalculator, FaNewspaper, FaArrowRight, FaCheckCircle, FaBullseye } from 'react-icons/fa';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: FaChartLine,
      title: '전략 · 지표',
      description: 'Buy & Hold, SMA, RSI, Bollinger, MACD 등을 손쉽게 실험하고 이동평균·RSI·볼밴드 등 오버레이 지표로 결과를 함께 확인합니다.',
      color: 'bg-primary/10 text-primary'
    },
    {
      icon: FaCalculator,
      title: '포트폴리오 · 리밸런싱',
      description: '여러 종목과 현금을 섞어 비중을 설정하고, 월간 등 주기적 리밸런싱을 시뮬레이션합니다. 벤치마크와 비교해 초과수익(알파)도 함께 확인하세요.',
      color: 'bg-green-100 text-green-600'
    },
    {
      icon: FaNewspaper,
      title: '뉴스/환율 · 시각화',
      description: '변동성 이벤트별 관련 뉴스와 USD/KRW 환율을 함께 보며 맥락을 파악하고, 인터랙티브 차트로 결과를 직관적으로 분석하세요.',
      color: 'bg-cyan-100 text-cyan-600'
    }
  ];

  const capabilities = [
    '주가 데이터 (Yahoo Finance) + 벤치마크 비교/알파',
    '커스터마이징 가능한 전략 파라미터·기간·수수료',
    '핵심 성과 지표 (총수익률, 드로우다운, 샤프 등)',
    '거래 기록과 진입/청산 포인트 표시',
    '포트폴리오 리밸런싱/DCA 시뮬레이션, 현금 자산 지원',
    '다양한 차트 (캔들스틱/라인/거래량) + 뉴스/환율 보기'
  ];

  const steps = [
    {
      number: 1,
      title: '종목 또는 포트폴리오 선택',
      description: '단일 종목 백테스트 또는 여러 종목으로 구성된 포트폴리오를 선택하세요.'
    },
    {
      number: 2,
      title: '기간 및 전략 설정',
      description: '백테스트 기간을 설정하고 원하는 투자 전략과 파라미터를 선택하세요.'
    },
    {
      number: 3,
      title: '백테스트 실행 및 결과 분석',
      description: '백테스트를 실행하고 차트와 통계를 통해 결과를 분석하세요.'
    }
  ];

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4 text-sm">
            데이터 기반 투자 전략 플랫폼
          </Badge>
          <h1 className="text-5xl font-bold text-primary mb-4 bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
            라고할때살걸
          </h1>
          <p className="text-xl text-foreground mb-3">
            데이터 기반 투자 전략 백테스팅 플랫폼
          </p>
          <p className="text-base text-muted-foreground mb-8 max-w-3xl mx-auto">
            종목/포트폴리오를 구성하고 전략·기간을 설정하면, 수익률·드로우다운·샤프 등 핵심 지표와 함께
            벤치마크 대비 성과(알파)까지 한눈에 확인할 수 있습니다.
          </p>
          <Button asChild size="lg" className="shadow-lg">
            <Link to="/backtest" className="inline-flex items-center">
              <FaChartLine className="mr-2" />
              지금 시작하기
            </Link>
          </Button>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {features.map((feature, index) => (
            <Card key={index} className="text-center border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardHeader>
                <div className={`w-20 h-20 ${feature.color} rounded-full mx-auto mb-4 flex items-center justify-center`}>
                  <feature.icon className="w-10 h-10" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm leading-relaxed">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Capabilities Section */}
        <Card className="mb-16 shadow-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl flex items-center justify-center">
              <FaBullseye className="text-xl mr-2" />
              주요 기능
            </CardTitle>
            <CardDescription>
              라고할때살걸이 제공하는 핵심 백테스팅 기능들
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {capabilities.map((capability, index) => (
                <div key={index} className="flex items-start">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-muted-foreground leading-relaxed">
                    {capability}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* How to Use Section */}
        <Card className="mb-16 shadow-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl flex items-center justify-center">
              <FaArrowRight className="text-xl mr-2" />
              사용법
            </CardTitle>
            <CardDescription>
              3단계로 완성하는 전략 백테스팅
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-w-4xl mx-auto space-y-6">
              {steps.map((step) => (
                <div key={step.number} className="flex items-start">
                  <Badge 
                    variant="default" 
                    className="w-8 h-8 rounded-full flex items-center justify-center mr-4 text-sm font-semibold flex-shrink-0"
                  >
                    {step.number}
                  </Badge>
                  <div className="flex-1">
                    <h6 className="font-semibold text-foreground mb-2 text-lg">
                      {step.title}
                    </h6>
                    <p className="text-muted-foreground leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* CTA Section */}
        <Card className="bg-primary/5 border-primary/20 shadow-sm">
          <CardContent className="text-center p-8">
            <CardTitle className="text-xl font-semibold text-primary mb-4">
              지금, 데이터로 확신을 더하세요.
            </CardTitle>
            <CardDescription className="text-foreground mb-6 text-base">
              실전 투자 전에 가상의 돈으로 다양한 전략의 수익성을 검증해 보세요.
            </CardDescription>
            <Button asChild size="lg" className="shadow-md">
              <Link to="/backtest">
                백테스트 시작하기 →
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HomePage;