import React, { useState, useEffect, ChangeEvent } from 'react';
import { UnifiedBacktestRequest } from '../types/api';
import { PREDEFINED_STOCKS, STRATEGY_CONFIGS, ASSET_TYPES, AssetType } from '../constants/strategies';

interface Stock {
  symbol: string;
  amount: number;
  investmentType: 'lump_sum' | 'dca';
  dcaPeriods?: number;
  assetType?: AssetType; // 자산 타입 추가
}

interface UnifiedBacktestFormProps {
  onSubmit: (request: UnifiedBacktestRequest) => Promise<void>;
  loading?: boolean;
}

const UnifiedBacktestForm: React.FC<UnifiedBacktestFormProps> = ({ onSubmit, loading = false }) => {
  const [portfolio, setPortfolio] = useState<Stock[]>([{ 
    symbol: '', 
    amount: 10000, 
    investmentType: 'lump_sum',
    dcaPeriods: 12 
  }]);
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [selectedStrategy, setSelectedStrategy] = useState('buy_and_hold');
  const [strategyParams, setStrategyParams] = useState<Record<string, any>>({});
  const [rebalanceFrequency, setRebalanceFrequency] = useState('monthly');
  const [commission, setCommission] = useState(0.2); // 퍼센트 형태로 변경 (0.2%)
  const [errors, setErrors] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 전략 변경 시 기본값 설정
  useEffect(() => {
    const config = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (config && config.parameters) {
      const defaultParams: Record<string, any> = {};
      Object.entries(config.parameters).forEach(([key, param]) => {
        defaultParams[key] = (param as any).default;
      });
      setStrategyParams(defaultParams);
    } else {
      setStrategyParams({});
    }
  }, [selectedStrategy]);

  const validatePortfolio = (): string[] => {
    const validationErrors: string[] = [];

    if (portfolio.length === 0) {
      validationErrors.push('포트폴리오는 최소 1개 종목을 포함해야 합니다.');
      return validationErrors;
    }

    if (portfolio.length > 10) {
      validationErrors.push('포트폴리오는 최대 10개 종목까지 포함할 수 있습니다.');
    }

    // 빈 심볼 검사 (CUSTOM 선택 후 미입력 제외)
    const emptySymbols = portfolio.filter(stock => !stock.symbol.trim() || stock.symbol === 'CUSTOM');
    if (emptySymbols.length > 0) {
      validationErrors.push('모든 종목 심볼을 입력해주세요.');
    }

    // 투자 금액 검사
    const invalidAmounts = portfolio.filter(stock => stock.amount <= 0);
    if (invalidAmounts.length > 0) {
      validationErrors.push('모든 투자 금액은 0보다 커야 합니다.');
    }

    // DCA 기간 검사
    const invalidDCA = portfolio.filter(stock => 
      stock.investmentType === 'dca' && (!stock.dcaPeriods || stock.dcaPeriods < 1 || stock.dcaPeriods > 60)
    );
    if (invalidDCA.length > 0) {
      validationErrors.push('DCA 기간은 1개월 이상 60개월 이하여야 합니다.');
    }

    return validationErrors;
  };

  const addStock = () => {
    setPortfolio([...portfolio, { 
      symbol: '', 
      amount: 10000, 
      investmentType: 'lump_sum',
      dcaPeriods: 12,
      assetType: ASSET_TYPES.STOCK
    }]);
  };

  const addCash = () => {
    setPortfolio([...portfolio, { 
      symbol: '현금', 
      amount: 10000, 
      investmentType: 'lump_sum',
      dcaPeriods: 12,
      assetType: ASSET_TYPES.CASH
    }]);
  };

  const removeStock = (index: number) => {
    const newPortfolio = portfolio.filter((_, i) => i !== index);
    setPortfolio(newPortfolio);
  };

  const updateStock = (index: number, field: keyof Stock, value: string | number) => {
    const newPortfolio = [...portfolio];
    if (field === 'symbol') {
      newPortfolio[index].symbol = (value as string).toUpperCase();
      // 심볼이 변경될 때 자산 타입을 자동으로 조정
      if ((value as string).toUpperCase() === '현금' || (value as string).toUpperCase() === 'CASH') {
        newPortfolio[index].assetType = ASSET_TYPES.CASH;
      } else {
        newPortfolio[index].assetType = ASSET_TYPES.STOCK;
      }
    } else if (field === 'investmentType') {
      newPortfolio[index].investmentType = value as 'lump_sum' | 'dca';
    } else if (field === 'assetType') {
      newPortfolio[index].assetType = value as AssetType;
    } else {
      newPortfolio[index][field] = Number(value);
    }
    setPortfolio(newPortfolio);
  };

  const updateStrategyParam = (key: string, value: any) => {
    setStrategyParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const generateStrategyParams = () => {
    const config = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (!config || !config.parameters) return {};

    const params: Record<string, any> = {};
    Object.entries(config.parameters).forEach(([key, paramConfig]) => {
      const value = strategyParams[key];
      if (value !== undefined) {
        params[key] = (paramConfig as any).type === 'int' ? parseInt(value) : value;
      }
    });
    return params;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);

    const validationErrors = validatePortfolio();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      setIsLoading(false);
      return;
    }

    try {
      // 포트폴리오 데이터 준비 (백엔드 API 스키마에 맞춤)
      const portfolioData = portfolio.map(stock => ({
        symbol: stock.symbol.toUpperCase(),
        amount: stock.amount,
        investment_type: stock.investmentType,
        dca_periods: stock.dcaPeriods || 12,
        asset_type: stock.assetType || ASSET_TYPES.STOCK
      }));

      const params = generateStrategyParams();
      console.log('Portfolio data being sent:', portfolioData);
      console.log('Strategy params being sent:', params);

      await onSubmit({
        portfolio: portfolioData,
        start_date: startDate,
        end_date: endDate,
        strategy: selectedStrategy || 'buy_and_hold',
        strategy_params: params,
        commission: commission / 100, // 퍼센트를 소수점으로 변환 (0.2 -> 0.002)
        rebalance_frequency: rebalanceFrequency
      });
    } catch (error) {
      console.error('백테스트 실행 중 오류:', error);
      const errorMessage = error instanceof Error ? error.message : '백테스트 실행 중 오류가 발생했습니다.';
      setErrors([errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderStrategyParams = () => {
    const config = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
    if (!config || !config.parameters) return null;

    return (
      <div className="mb-8">
        <h5 className="text-lg font-semibold mb-4">전략 파라미터</h5>
        <div className="grid md:grid-cols-2 gap-6">
          {Object.entries(config.parameters).map(([key, paramConfig]) => {
            const param = paramConfig as any;
            return (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {key === 'short_window' ? '단기 이동평균 기간' :
                   key === 'long_window' ? '장기 이동평균 기간' :
                   key === 'rsi_period' ? 'RSI 기간' :
                   key === 'rsi_oversold' ? 'RSI 과매도 기준' :
                   key === 'rsi_overbought' ? 'RSI 과매수 기준' : key}
                </label>
                <input
                  type="number"
                  value={strategyParams[key] || param.default}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => updateStrategyParam(key, e.target.value)}
                  min={param.min}
                  max={param.max}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  기본값: {param.default}, 범위: {param.min} - {param.max}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const getTotalAmount = () => {
    return portfolio.reduce((sum, stock) => sum + stock.amount, 0);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 rounded-t-lg">
          <h4 className="text-xl font-semibold text-gray-800 mb-2">🏦 포트폴리오 백테스트</h4>
          <p className="text-sm text-gray-600">
            종목/자산별 투자 금액과 방식을 설정하여 포트폴리오 백테스트를 실행합니다.
          </p>
        </div>
        <div className="p-6">
          {errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800 mb-2">⚠️ 입력 오류</h3>
                  <ul className="text-sm text-red-700 space-y-1">
                    {errors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* 포트폴리오 구성 */}
            <div className="mb-8">
              <h5 className="text-lg font-semibold mb-4">포트폴리오 구성</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">종목/자산</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">투자 금액 ($)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">투자 방식</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">자산 타입</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">비중 (%)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {portfolio.map((stock, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="space-y-2">
                            <select
                              value={stock.symbol || 'CUSTOM'}
                              onChange={(e: ChangeEvent<HTMLSelectElement>) => {
                                const selectedValue = e.target.value;
                                if (selectedValue === 'CUSTOM') {
                                  updateStock(index, 'symbol', '');
                                } else {
                                  updateStock(index, 'symbol', selectedValue);
                                }
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              {PREDEFINED_STOCKS.map(option => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            {(stock.symbol === '' || !PREDEFINED_STOCKS.find(opt => opt.value === stock.symbol)) && (
                              <input
                                type="text"
                                value={stock.symbol}
                                onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'symbol', e.target.value)}
                                placeholder="종목 심볼 입력 (예: AAPL)"
                                maxLength={10}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            value={stock.amount}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'amount', e.target.value)}
                            min="100"
                            step="100"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="space-y-2">
                            <select
                              value={stock.investmentType}
                              onChange={(e: ChangeEvent<HTMLSelectElement>) => updateStock(index, 'investmentType', e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              <option value="lump_sum">일시불 투자</option>
                              <option value="dca">분할 매수 (DCA)</option>
                            </select>
                            {stock.investmentType === 'dca' && (
                              <input
                                type="number"
                                value={stock.dcaPeriods || 12}
                                onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'dcaPeriods', e.target.value)}
                                min="1"
                                max="60"
                                placeholder="개월 수"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                            )}
                          </div>
                          {stock.investmentType === 'dca' && stock.dcaPeriods && (
                            <p className="text-xs text-gray-500 mt-1">
                              월 ${Math.round(stock.amount / stock.dcaPeriods)}씩 {stock.dcaPeriods}개월
                            </p>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <select
                            value={stock.assetType || ASSET_TYPES.STOCK}
                            onChange={(e: ChangeEvent<HTMLSelectElement>) => updateStock(index, 'assetType', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value={ASSET_TYPES.STOCK}>주식</option>
                            <option value={ASSET_TYPES.CASH}>현금</option>
                          </select>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {((stock.amount / getTotalAmount()) * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            type="button"
                            onClick={() => removeStock(index)}
                            disabled={portfolio.length <= 1}
                            className="px-3 py-1 text-sm font-medium text-red-600 bg-red-50 border border-red-300 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            삭제
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-blue-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">합계</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">${getTotalAmount().toLocaleString()}</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">-</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">-</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">100.0%</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-700"></th>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <div className="flex gap-3 mt-4">
                <button
                  type="button"
                  onClick={addStock}
                  disabled={portfolio.length >= 10}
                  className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  + 종목 추가
                </button>
                <button
                  type="button"
                  onClick={addCash}
                  disabled={portfolio.length >= 10}
                  title="현금을 포트폴리오에 추가 (무위험 자산)"
                  className="px-4 py-2 text-sm font-medium text-green-600 bg-green-50 border border-green-300 rounded-md hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  💰 현금 추가
                </button>
              </div>
            </div>

            {/* 백테스트 설정 */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">시작 날짜</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">종료 날짜</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">투자 전략</label>
                <select
                  value={selectedStrategy}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedStrategy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="buy_and_hold">매수 후 보유</option>
                  <option value="sma_crossover">단순이동평균 교차</option>
                  <option value="rsi_strategy">RSI 전략</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">리밸런싱 주기</label>
                <select
                  value={rebalanceFrequency}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setRebalanceFrequency(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="never">리밸런싱 안함</option>
                  <option value="monthly">매월</option>
                  <option value="quarterly">분기별</option>
                  <option value="yearly">연간</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  포트폴리오 비중을 다시 맞추는 주기
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">거래 수수료 (%)</label>
                <input
                  type="number"
                  value={commission}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setCommission(Number(e.target.value))}
                  min="0"
                  max="5"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  예: 0.2 (0.2% 수수료)
                </p>
              </div>
            </div>

            {/* 전략 파라미터 */}
            {renderStrategyParams()}

            {/* 실행 버튼 */}
            <div>
              <button
                type="submit"
                disabled={loading || isLoading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg text-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading || isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    포트폴리오 백테스트 실행 중...
                  </span>
                ) : (
                  '📈 포트폴리오 백테스트 실행'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UnifiedBacktestForm;
