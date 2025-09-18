import React, { useMemo } from 'react';
import { Sparkles } from 'lucide-react';
import { STRATEGY_CONFIGS, StrategyParameter } from '../model/strategyConfig';
import { FormField, FormLegend } from '@/shared/components';

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
      <div className="space-y-3">
        <FormField
          label="투자 전략"
          type="select"
          value={selectedStrategy}
          onChange={(value) => setSelectedStrategy(value.toString())}
          options={strategyOptions}
        />
        <FormLegend
          icon={<Sparkles className="h-3.5 w-3.5" />}
          items={[
            {
              label: currentConfig?.description ?? '전략을 선택해 설명을 확인하세요',
              tone: 'muted',
            },
            {
              label: parameterEntries.length
                ? `파라미터 ${parameterEntries.length}개`
                : '추가 파라미터 없음',
              tone: parameterEntries.length ? 'accent' : 'muted',
            },
          ]}
        />
      </div>

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
