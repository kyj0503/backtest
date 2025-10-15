import React, { useMemo } from 'react';
import { STRATEGY_CONFIGS, StrategyParameter } from '../model/strategyConfig';
import { StrategyParamValue } from '../model/api-types';
import { FormField } from '@/shared/components';

export interface StrategyFormProps {
  selectedStrategy: string;
  setSelectedStrategy: (strategy: string) => void;
  strategyParams: Record<string, StrategyParamValue>;
  updateStrategyParam: (key: string, value: StrategyParamValue) => void;
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
          {parameterEntries.map(([key, param]) => {
            const currentValue = strategyParams[key] ?? param.default;
            const displayValue = typeof currentValue === 'string' || typeof currentValue === 'number' ? currentValue : param.default;

            return (
              <FormField
                key={key}
                label={param.description || key}
                type="number"
                value={displayValue}
                onChange={(value) => updateStrategyParam(key, value.toString())}
                min={param.min}
                max={param.max}
                step={param.step}
                helpText={`기본값 ${param.default} · 범위 ${param.min}~${param.max}`}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StrategyForm;
