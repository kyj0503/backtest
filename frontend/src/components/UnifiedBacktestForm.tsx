import React, { useState, useEffect } from 'react';
import { UnifiedBacktestRequest } from '../types/api';
import { STRATEGY_CONFIGS, ASSET_TYPES, AssetType } from '../constants/strategies';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import CommissionForm from './CommissionForm';
import PortfolioForm from './PortfolioForm';

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

  const getTotalAmount = () => {
    return portfolio.reduce((sum, stock) => sum + stock.amount, 0);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 rounded-t-lg">
          <h4 className="text-xl font-semibold text-gray-800 mb-2">포트폴리오 백테스트</h4>
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
                  <h3 className="text-sm font-medium text-red-800 mb-2">입력 오류</h3>
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
            <PortfolioForm
              portfolio={portfolio}
              updateStock={updateStock}
              addStock={addStock}
              addCash={addCash}
              removeStock={removeStock}
              getTotalAmount={getTotalAmount}
            />

            {/* 백테스트 설정 */}
            <div className="mb-8">
              <h5 className="text-lg font-semibold mb-4">백테스트 설정</h5>
              <DateRangeForm
                startDate={startDate}
                setStartDate={setStartDate}
                endDate={endDate}
                setEndDate={setEndDate}
              />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <StrategyForm
                selectedStrategy={selectedStrategy}
                setSelectedStrategy={setSelectedStrategy}
                strategyParams={strategyParams}
                updateStrategyParam={updateStrategyParam}
              />
              <CommissionForm
                rebalanceFrequency={rebalanceFrequency}
                setRebalanceFrequency={setRebalanceFrequency}
                commission={commission}
                setCommission={setCommission}
              />
            </div>

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
