import React from 'react';
import { STRATEGY_CONFIGS } from '../constants/strategies';
import { FormField } from './common';

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
            const labelText = 
              key === 'short_window' ? '단기 이동평균 기간' :
              key === 'long_window' ? '장기 이동평균 기간' :
              key === 'rsi_period' ? 'RSI 기간' :
              key === 'rsi_oversold' ? 'RSI 과매도 기준' :
              key === 'rsi_overbought' ? 'RSI 과매수 기준' : key;

            return (
              <FormField
                key={key}
                label={labelText}
                type="number"
                value={strategyParams[key] || param.default}
                onChange={(value) => updateStrategyParam(key, value.toString())}
                min={param.min}
                max={param.max}
                helpText={`기본값: ${param.default}, 범위: ${param.min} - ${param.max}`}
              />
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* 투자 전략 선택 */}
      <FormField
        label="투자 전략"
        type="select"
        value={selectedStrategy}
        onChange={(value) => setSelectedStrategy(value.toString())}
        options={[
          { value: 'buy_and_hold', label: '매수 후 보유' },
          { value: 'sma_crossover', label: '단순이동평균 교차' },
          { value: 'rsi_strategy', label: 'RSI 전략' },
        ]}
      />

      {/* 전략 파라미터 */}
      {renderStrategyParams()}
    </div>
  );
};

export default StrategyForm;
