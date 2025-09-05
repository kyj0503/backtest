import React from 'react';
import UnifiedBacktestForm from '../components/UnifiedBacktestForm';
import UnifiedBacktestResults from '../components/UnifiedBacktestResults';
import { useBacktest } from '../hooks/useBacktest';

const BacktestPage: React.FC = () => {
  const { results, loading, error, errorType, errorId, isPortfolio, runBacktest, clearError } = useBacktest();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* 페이지 헤더 */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-blue-600 mb-4 flex items-center justify-center gap-2">
            <span className="text-2xl">📊</span>
            <span>백테스트 실행</span>
          </h2>
          <p className="text-gray-600">
            투자 전략을 설정하고 백테스트를 실행해보세요
          </p>
        </div>

        {/* 백테스트 폼 */}
        <div className="mb-12">
          <UnifiedBacktestForm 
            onSubmit={runBacktest} 
            loading={loading} 
          />
        </div>

        {/* 로딩 상태 */}
        {loading && (
          <div className="text-center py-16">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <h4 className="text-xl font-semibold mb-2">백테스트 실행 중...</h4>
            <p className="text-gray-600">데이터를 분석하고 있습니다</p>
          </div>
        )}

        {/* 에러 메시지 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-800 mb-1">
                  {errorType === 'network' ? '네트워크 오류' :
                   errorType === 'data_not_found' ? '데이터 없음' :
                   errorType === 'validation' ? '입력값 오류' :
                   errorType === 'rate_limit' ? '요청 제한 초과' :
                   '오류가 발생했습니다'}
                </h3>
                <p className="text-sm text-red-700 mb-1">{error}</p>
                {errorId && (
                  <p className="text-xs text-red-600">오류 ID: {errorId}</p>
                )}
              </div>
              <div className="ml-auto pl-3">
                <button
                  onClick={clearError}
                  className="inline-flex rounded-md bg-red-50 p-1.5 text-red-500 hover:bg-red-100 focus:outline-none"
                >
                  <span className="sr-only">닫기</span>
                  <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 결과 표시 */}
        {results && !loading && (
          <div>
            <UnifiedBacktestResults 
              data={results} 
              isPortfolio={isPortfolio} 
            />
          </div>
        )}

        {/* 초기 상태 안내 */}
        {!results && !loading && !error && (
          <div className="text-center py-16">
            <div className="text-6xl mb-6">🎯</div>
            <h4 className="text-xl font-semibold mb-4">백테스트 설정을 완료하고 실행 버튼을 눌러주세요</h4>
            <p className="text-gray-600">
              포트폴리오 구성, 투자 전략, 백테스트 기간을 설정한 후<br />
              <strong className="text-blue-600">백테스트 실행</strong> 버튼을 클릭하면 결과를 확인할 수 있습니다.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BacktestPage;
