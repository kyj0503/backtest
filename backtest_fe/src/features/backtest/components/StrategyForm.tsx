import React, { useMemo, useState } from 'react';
import { STRATEGY_CONFIGS, StrategyParameter } from '../model/strategyConfig';
import { StrategyParamValue } from '../model/api-types';
import { FormField } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import { HelpCircle } from 'lucide-react';
import StrategyHelpModal from './StrategyHelpModal';

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
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);

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
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <FormField
            label="투자 전략"
            type="select"
            value={selectedStrategy}
            onChange={(value) => setSelectedStrategy(value.toString())}
            options={strategyOptions}
          />
        </div>
        <Button
          type="button"
          variant="outline"
          size="default"
          onClick={() => setIsHelpModalOpen(true)}
          className="flex items-center gap-2 whitespace-nowrap"
        >
          <HelpCircle className="w-4 h-4" />
          전략 도움말
        </Button>
      </div>

      {currentConfig && (
        <div className="text-sm text-muted-foreground bg-muted/30 rounded-lg p-3">
          {currentConfig.description}
        </div>
      )}

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

      <StrategyHelpModal
        strategyId={selectedStrategy}
        open={isHelpModalOpen}
        onOpenChange={setIsHelpModalOpen}
      />
    </div>
  );
};

export default StrategyForm;
