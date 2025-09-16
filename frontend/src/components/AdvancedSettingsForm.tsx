import React, { useMemo, useState } from 'react';
import { RotateCcw, Settings2 } from 'lucide-react';
import { Stock } from '../types/backtest-form';
import { STRATEGY_CONFIGS, StrategyParameter } from '../constants/strategies';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { FormField, FormLegend } from './common';

interface AdvancedSettingsFormProps {
  portfolio: Stock[];
  isVisible: boolean;
  onClose: () => void;
  onApply: (settings: AdvancedStockSettings[]) => void;
}

export interface AdvancedStockSettings {
  stockIndex: number;
  symbol: string;
  startDate?: string;
  endDate?: string;
  strategy?: string;
  strategyParams?: Partial<Record<string, number>>;
}

const AdvancedSettingsForm: React.FC<AdvancedSettingsFormProps> = ({
  portfolio,
  isVisible,
  onClose,
  onApply
}) => {
  const [settings, setSettings] = useState<AdvancedStockSettings[]>(() => 
    portfolio.map((stock, index) => ({
      stockIndex: index,
      symbol: stock.symbol,
      startDate: '',
      endDate: '',
      strategy: 'buy_and_hold',
      strategyParams: {}
    }))
  );

  const strategyOptions = useMemo(
    () =>
      Object.entries(STRATEGY_CONFIGS).map(([id, config]) => ({
        value: id,
        label: config.name,
        description: config.description,
      })),
    [],
  );

  const updateStockSetting = (
    stockIndex: number,
    field: keyof AdvancedStockSettings,
    value: string | number | undefined,
  ) => {
    setSettings(prev =>
      prev.map(setting =>
        setting.stockIndex === stockIndex ? { ...setting, [field]: value } : setting,
      ),
    );
  };

  const applyStrategyDefaults = (strategyId: string) => {
    const config = STRATEGY_CONFIGS[strategyId as keyof typeof STRATEGY_CONFIGS];
    if (!config?.parameters) return {};
    return Object.fromEntries(
      Object.entries(config.parameters).map(([key, param]) => [key, param.default]),
    );
  };

  const updateStrategy = (stockIndex: number, strategyId: string) => {
    const defaultParams = applyStrategyDefaults(strategyId);
    setSettings(prev =>
      prev.map(setting =>
        setting.stockIndex === stockIndex
          ? { ...setting, strategy: strategyId, strategyParams: defaultParams }
          : setting,
      ),
    );
  };

  const updateStrategyParam = (stockIndex: number, paramName: string, value: string) => {
    setSettings(prev =>
      prev.map(setting => {
        if (setting.stockIndex !== stockIndex) return setting;
        const strategyId = setting.strategy ?? 'buy_and_hold';
        const strategyConfig = STRATEGY_CONFIGS[strategyId as keyof typeof STRATEGY_CONFIGS];
        const paramConfig = strategyConfig?.parameters?.[paramName];
        if (!paramConfig) return setting;

        const parsedValue =
          paramConfig.type === 'float' ? parseFloat(value) : parseInt(value, 10);
        if (Number.isNaN(parsedValue)) {
          return setting;
        }

        return {
          ...setting,
          strategyParams: {
            ...(setting.strategyParams ?? {}),
            [paramName]: parsedValue,
          },
        };
      }),
    );
  };

  const handleApply = () => {
    onApply(settings);
    onClose();
  };

  const handleReset = () => {
    setSettings(portfolio.map((stock, index) => ({
      stockIndex: index,
      symbol: stock.symbol,
      startDate: '',
      endDate: '',
      strategy: 'buy_and_hold',
      strategyParams: {}
    })));
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose();
    }
  };

  return (
    <Dialog open={isVisible} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-5xl overflow-hidden p-0">
        <DialogHeader className="space-y-2 border-b border-border/60 px-6 py-4 text-left">
          <DialogTitle className="text-xl font-semibold">고급 사용자 설정</DialogTitle>
          <DialogDescription>
            종목별로 백테스트 기간과 전략을 세밀하게 조정합니다. 비워두면 기본 설정을
            따릅니다.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-4">
          <FormLegend
            items={[
              { label: '개별 기간 & 전략 지정', tone: 'accent' },
              { label: '설정 미입력 시 기본값 사용', tone: 'muted' },
            ]}
          />
        </div>

        <ScrollArea className="max-h-[60vh] px-6 pb-6">
          <Tabs defaultValue="stock-0" className="w-full">
            <TabsList className="grid h-auto w-full grid-cols-3 gap-2 rounded-2xl bg-muted/40 p-2 text-xs md:grid-cols-4 xl:grid-cols-5">
              {portfolio.map((stock, index) => (
                <TabsTrigger
                  key={stock.symbol + index}
                  value={`stock-${index}`}
                  className="rounded-xl px-3 py-2"
                >
                  {stock.symbol || `자산 ${index + 1}`}
                </TabsTrigger>
              ))}
            </TabsList>

            {portfolio.map((stock, index) => {
              const currentSetting = settings.find(s => s.stockIndex === index);
              const selectedStrategy = currentSetting?.strategy ?? 'buy_and_hold';
              const strategyConfig = STRATEGY_CONFIGS[selectedStrategy as keyof typeof STRATEGY_CONFIGS];
              const parameterEntries = Object.entries(strategyConfig?.parameters ?? {}) as Array<
                [string, StrategyParameter]
              >;

              return (
                <TabsContent
                  key={`content-${stock.symbol}-${index}`}
                  value={`stock-${index}`}
                  className="mt-4 space-y-6"
                >
                  <FormLegend
                    items={[
                      { label: stock.symbol || `자산 ${index + 1}`, tone: 'accent' },
                      { label: '전체 설정으로 복귀하려면 비워두세요', tone: 'muted' },
                    ]}
                  />

                  <div className="grid gap-6 md:grid-cols-2">
                    <FormField
                      label="개별 시작일"
                      type="date"
                      value={currentSetting?.startDate ?? ''}
                      onChange={value => updateStockSetting(index, 'startDate', value.toString())}
                    />
                    <FormField
                      label="개별 종료일"
                      type="date"
                      value={currentSetting?.endDate ?? ''}
                      onChange={value => updateStockSetting(index, 'endDate', value.toString())}
                    />
                  </div>

                  <FormField
                    label="개별 전략"
                    type="select"
                    value={selectedStrategy}
                    onChange={value => updateStrategy(index, value.toString())}
                    options={strategyOptions}
                    helpText={strategyConfig?.description}
                  />

                  {parameterEntries.length > 0 && (
                    <div className="grid gap-4 md:grid-cols-2">
                      {parameterEntries.map(([key, param]) => (
                        <FormField
                          key={key}
                          label={param.description || key}
                          type="number"
                          value={
                            currentSetting?.strategyParams?.[key] ?? param.default
                          }
                          onChange={value => updateStrategyParam(index, key, value.toString())}
                          min={param.min}
                          max={param.max}
                          step={param.step}
                          helpText={`기본값 ${param.default} · 범위 ${param.min}~${param.max}`}
                        />
                      ))}
                    </div>
                  )}
                </TabsContent>
              );
            })}
          </Tabs>
        </ScrollArea>

        <Separator />
        <div className="flex items-center justify-between gap-3 px-6 py-4">
          <Button variant="ghost" onClick={handleReset} className="gap-2">
            <RotateCcw className="h-4 w-4" /> 초기화
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              취소
            </Button>
            <Button onClick={handleApply} className="gap-2">
              <Settings2 className="h-4 w-4" /> 설정 적용
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AdvancedSettingsForm;
