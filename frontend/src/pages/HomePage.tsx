import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine, FaCalculator, FaNewspaper, FaArrowRight, FaCheckCircle, FaBullseye } from 'react-icons/fa';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* 메인 히어로 섹션 */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-blue-600 mb-6">
            백테스팅을 시작하세요
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            단일 종목 또는 포트폴리오를 선택하고 투자 전략을 설정한 후 백테스트를 실행해보세요.
          </p>
          <Link 
            to="/backtest" 
            className="inline-flex items-center bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors shadow-lg"
          >
            <FaChartLine className="mr-2" />
            지금 시작하기
          </Link>
        </div>

        {/* 기능 소개 섹션 */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <div className="w-20 h-20 bg-blue-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <FaChartLine className="w-10 h-10 text-blue-600" />
            </div>
            <h5 className="text-xl font-semibold mb-3">다양한 전략</h5>
            <p className="text-gray-600 text-sm">
              Buy & Hold, SMA Crossover, RSI, Bollinger Bands, MACD 등 
              검증된 투자 전략을 제공합니다.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-20 h-20 bg-green-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <FaCalculator className="w-10 h-10 text-green-600" />
            </div>
            <h5 className="text-xl font-semibold mb-3">포트폴리오 분석</h5>
            <p className="text-gray-600 text-sm">
              여러 종목으로 구성된 포트폴리오의 성과를 분석하고 
              리밸런싱 전략을 테스트할 수 있습니다.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-20 h-20 bg-cyan-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <FaNewspaper className="w-10 h-10 text-cyan-600" />
            </div>
            <h5 className="text-xl font-semibold mb-3">실시간 시각화</h5>
            <p className="text-gray-600 text-sm">
              인터랙티브 차트로 백테스트 결과를 직관적으로 
              확인하고 분석할 수 있습니다.
            </p>
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
                  실시간 주가 데이터 (Yahoo Finance)
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  커스터마이징 가능한 전략 파라미터
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  상세한 성과 지표 (샤프 비율, 최대 낙폭 등)
                </li>
              </ul>
            </div>
            <div>
              <ul className="space-y-3">
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  거래 기록 및 진입/청산 포인트 표시
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  포트폴리오 리밸런싱 시뮬레이션
                </li>
                <li className="flex items-center">
                  <FaCheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  다양한 차트 타입 (캔들스틱, 라인, 거래량)
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
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-4 text-sm font-semibold">
                1
              </div>
              <div>
                <h6 className="text-lg font-semibold mb-2">종목 또는 포트폴리오 선택</h6>
                <p className="text-gray-600">단일 종목 백테스트 또는 여러 종목으로 구성된 포트폴리오를 선택하세요.</p>
              </div>
            </div>
            <div className="flex items-start mb-6">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-4 text-sm font-semibold">
                2
              </div>
              <div>
                <h6 className="text-lg font-semibold mb-2">기간 및 전략 설정</h6>
                <p className="text-gray-600">백테스트 기간을 설정하고 원하는 투자 전략과 파라미터를 선택하세요.</p>
              </div>
            </div>
            <div className="flex items-start mb-6">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-4 text-sm font-semibold">
                3
              </div>
              <div>
                <h6 className="text-lg font-semibold mb-2">백테스트 실행 및 결과 분석</h6>
                <p className="text-gray-600">백테스트를 실행하고 차트와 통계를 통해 결과를 분석하세요.</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA 섹션 */}
        <div className="text-center bg-blue-50 p-8 rounded-lg">
          <h5 className="text-xl font-semibold text-blue-600 mb-4">지금 바로 백테스팅을 시작해보세요!</h5>
          <Link 
            to="/backtest" 
            className="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            백테스트 페이지로 이동 →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
