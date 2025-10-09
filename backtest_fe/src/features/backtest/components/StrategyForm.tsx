import React, { useMemo } from 'react';
import { STRATEGY_CONFIGS, StrategyParameter } from '../model/strategyConfig';
import { FormField } from '@/shared/components';

export interface StrategyFormProps {
  selectedStrategy: string;
  setSelectedStrategy: (strategy: string) => void;
  strategyParams: Record<string, string | number>;
  updateStrategyParam: (key: string, value: string) => void;
}

const StrategyForm: React.FC<StrategyFormProps> = ({
  selectedStrategy,
  setSelectedStrategy,
  strategyParams,
  updateStrategyParam
}) => {
  const strategyOptions = useMemo(
    () =>
      Object.entries(STRATEGY_CONFIGS).map(([id, config]) => ({
        value: id,
        label: config.name,
      })),
    [],
  );

  const currentConfig = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
  const parameterEntries = Object.entries(currentConfig?.parameters ?? {}) as Array<
    [string, StrategyParameter]
  >;

  return (
    <div className="space-y-6">
      <FormField
        label="투자 전략"
        type="select"
        value={selectedStrategy}
        onChange={(value) => setSelectedStrategy(value.toString())}
        options={strategyOptions}
      />

      {parameterEntries.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {parameterEntries.map(([key, param]) => (
            <FormField
              key={key}
              label={param.description || key}
              type="number"
              value={strategyParams[key] ?? param.default}
              onChange={(value) => updateStrategyParam(key, value.toString())}
              min={param.min}
              max={param.max}
              step={param.step}
              helpText={`기본값 ${param.default} · 범위 ${param.min}~${param.max}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default StrategyForm;
