import React, { ChangeEvent } from 'react';
import { STRATEGY_CONFIGS } from '../constants/strategies';

export interface StrategyFormProps {
  selectedStrategy: string;
  setSelectedStrategy: (strategy: string) => void;
  strategyParams: Record<string, any>;
  updateStrategyParam: (key: string, value: string) => void;
}

const StrategyForm: React.FC<StrategyFormProps> = ({
  selectedStrategy,
  setSelectedStrategy,
  strategyParams,
  updateStrategyParam
}) => {
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

  return (
    <div className="space-y-8">
      {/* 투자 전략 선택 */}
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

      {/* 전략 파라미터 */}
      {renderStrategyParams()}
    </div>
  );
};

export default StrategyForm;
