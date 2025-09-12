import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine, FaCalculator, FaNewspaper, FaArrowRight, FaCheckCircle, FaBullseye } from 'react-icons/fa';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* 메인 히어로 섹션 */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-primary mb-4">라고할때살걸</h1>
          <p className="text-xl text-foreground mb-3">데이터 기반 투자 전략 백테스팅 플랫폼</p>
          <p className="text-base text-muted-foreground mb-8 max-w-3xl mx-auto">
            종목/포트폴리오를 구성하고 전략·기간을 설정하면, 수익률·드로우다운·샤프 등 핵심 지표와 함께
            벤치마크 대비 성과(알파)까지 한눈에 확인할 수 있습니다.
          </p>
          <Link
            to="/backtest"
            className="inline-flex items-center bg-primary text-primary-foreground px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors shadow-lg"
          >
            <FaChartLine className="mr-2" />
            지금 시작하기
          </Link>
        </div>

        {/* 기능 소개 섹션 */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <div className="w-20 h-20 bg-primary/10 rounded-full mx-auto mb-6 flex items-center justify-center">
              <FaChartLine className="w-10 h-10 text-primary" />
            </div>
            <h5 className="text-xl font-semibold mb-3">전략 · 지표</h5>
            <p className="text-muted-foreground text-sm">Buy & Hold, SMA, RSI, Bollinger, MACD 등을 손쉽게 실험하고
              이동평균·RSI·볼밴드 등 오버레이 지표로 결과를 함께 확인합니다.</p>
          </div>
          
          <div className="text-center">
            <div className="w-20 h-20 bg-green-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <FaCalculator className="w-10 h-10 text-green-600" />
            </div>
            <h5 className="text-xl font-semibold mb-3">포트폴리오 · 리밸런싱</h5>
            <p className="text-muted-foreground text-sm">여러 종목과 현금을 섞어 비중을 설정하고, 월간 등 주기적 리밸런싱을 시뮬레이션합니다.
              벤치마크와 비교해 초과수익(알파)도 함께 확인하세요.</p>
          </div>
          
          <div className="text-center">
            <div className="w-20 h-20 bg-cyan-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <FaNewspaper className="w-10 h-10 text-cyan-600" />
            </div>
            <h5 className="text-xl font-semibold mb-3">뉴스/환율 · 시각화</h5>
            <p className="text-muted-foreground text-sm">변동성 이벤트별 관련 뉴스와 USD/KRW 환율을 함께 보며 맥락을 파악하고,
              인터랙티브 차트로 결과를 직관적으로 분석하세요.</p>
          </div>
        </div>

        {/* 지원 기능 */}
        <div className="bg-white rounded-lg p-8 mb-16 shadow-sm">
          <h4 className="text-2xl font-semibold text-center mb-8 flex items-center justify-center">
            <FaBullseye className="text-xl mr-2" />
            주요 기능
          </h4>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <ul className="space-y-3">
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  주가 데이터 (Yahoo Finance) + 벤치마크 비교/알파
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  커스터마이징 가능한 전략 파라미터·기간·수수료
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  핵심 성과 지표 (총수익률, 드로우다운, 샤프 등)
                </li>
              </ul>
            </div>
            <div>
              <ul className="space-y-3">
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  거래 기록과 진입/청산 포인트 표시
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  포트폴리오 리밸런싱/DCA 시뮬레이션, 현금 자산 지원
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  다양한 차트 (캔들스틱/라인/거래량) + 뉴스/환율 보기
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 사용법 안내 */}
        <div className="mb-16">
          <h4 className="text-2xl font-semibold text-center mb-8 flex items-center justify-center">
            <FaArrowRight className="text-xl mr-2" />
            사용법
          </h4>
          <div className="max-w-4xl mx-auto">
            <div className="flex items-start mb-6">
                          <li className="flex items-start">
              <div className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center mr-4 text-sm font-semibold">
                1
              </div>
              <div className="flex-1">
                <h6 className="font-semibold text-foreground mb-2">종목 또는 포트폴리오 선택</h6>
                <p className="text-muted-foreground">단일 종목 백테스트 또는 여러 종목으로 구성된 포트폴리오를 선택하세요.</p>
              </div>
            </li>
            </div>
            <div className="flex items-start mb-6">
              <div className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center mr-4 text-sm font-semibold">
                2
              </div>
              <div>
                <h6 className="text-lg font-semibold mb-2">기간 및 전략 설정</h6>
                <p className="text-muted-foreground">백테스트 기간을 설정하고 원하는 투자 전략과 파라미터를 선택하세요.</p>
              </div>
            </div>
            <div className="flex items-start mb-6">
              <div className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center mr-4 text-sm font-semibold">
                3
              </div>
              <div>
                <h6 className="text-lg font-semibold mb-2">백테스트 실행 및 결과 분석</h6>
                <p className="text-muted-foreground">백테스트를 실행하고 차트와 통계를 통해 결과를 분석하세요.</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA 섹션 */}
                <div className="text-center bg-primary/5 p-8 rounded-lg">
          <h5 className="text-xl font-semibold text-primary mb-4">지금, 데이터로 확신을 더하세요.</h5>
          <p className="text-foreground mb-6">실전 투자 전에 가상의 돈으로 다양한 전략의 수익성을 검증해 보세요.</p>
          <Link
            to="/backtest"
            className="inline-block bg-primary text-primary-foreground px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors"
          >
            백테스트 시작하기 →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
