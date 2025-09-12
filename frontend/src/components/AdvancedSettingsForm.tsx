import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Stock } from '../types/backtest-form';
import { STRATEGY_CONFIGS, StrategyParameter } from '../constants/strategies';

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
  strategyParams?: Record<string, any>;
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

  const updateStockSetting = (stockIndex: number, field: keyof AdvancedStockSettings, value: any) => {
    setSettings(prev => prev.map(setting => 
      setting.stockIndex === stockIndex 
        ? { ...setting, [field]: value }
        : setting
    ));
  };

  const updateStrategyParam = (stockIndex: number, paramName: string, value: any) => {
    setSettings(prev => prev.map(setting => 
      setting.stockIndex === stockIndex 
        ? { 
            ...setting, 
            strategyParams: { 
              ...(setting.strategyParams || {}), 
              [paramName]: value 
            }
          }
        : setting
    ));
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

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <Card>
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle>고급 사용자 설정</CardTitle>
              <Button variant="ghost" onClick={onClose} className="h-8 w-8 p-0">
                <span className="sr-only">닫기</span>
                ✕
              </Button>
            </div>
            <p className="text-sm text-gray-600">
              각 종목별로 개별 날짜 범위와 전략을 설정할 수 있습니다.
            </p>
          </CardHeader>
          <CardContent className="p-6 max-h-[70vh] overflow-y-auto">
            <Tabs defaultValue="stock-0" className="w-full">
              <TabsList className="grid w-full grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-1 h-auto mb-6">
                {portfolio.map((stock, index) => (
                  <TabsTrigger 
                    key={index} 
                    value={`stock-${index}`}
                    className="text-xs px-2 py-2 truncate"
                    title={stock.symbol}
                  >
                    {stock.symbol}
                  </TabsTrigger>
                ))}
              </TabsList>

              {portfolio.map((stock, index) => {
                const currentSetting = settings.find(s => s.stockIndex === index);
                const selectedStrategy = currentSetting?.strategy || 'buy_and_hold';
                const strategyConfig = STRATEGY_CONFIGS[selectedStrategy];
                
                return (
                  <TabsContent key={index} value={`stock-${index}`} className="space-y-6 mt-0">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* 날짜 설정 */}
                      <Card>
                        <CardHeader className="pb-4">
                          <CardTitle className="text-lg">개별 날짜 범위</CardTitle>
                          <p className="text-sm text-gray-600">
                            {stock.symbol}에 대한 개별 백테스트 기간을 설정합니다. 
                            비워두면 전체 설정을 따릅니다.
                          </p>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <Label htmlFor={`start-${index}`}>시작일</Label>
                            <Input
                              id={`start-${index}`}
                              type="date"
                              value={currentSetting?.startDate || ''}
                              onChange={e => updateStockSetting(index, 'startDate', e.target.value)}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <Label htmlFor={`end-${index}`}>종료일</Label>
                            <Input
                              id={`end-${index}`}
                              type="date"
                              value={currentSetting?.endDate || ''}
                              onChange={e => updateStockSetting(index, 'endDate', e.target.value)}
                              className="mt-1"
                            />
                          </div>
                        </CardContent>
                      </Card>

                      {/* 전략 설정 */}
                      <Card>
                        <CardHeader className="pb-4">
                          <CardTitle className="text-lg">개별 전략</CardTitle>
                          <p className="text-sm text-gray-600">
                            {stock.symbol}에 대한 개별 투자 전략을 설정합니다.
                          </p>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <Label htmlFor={`strategy-${index}`}>전략 선택</Label>
                            <select
                              id={`strategy-${index}`}
                              value={selectedStrategy}
                              onChange={e => updateStockSetting(index, 'strategy', e.target.value)}
                              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              {Object.entries(STRATEGY_CONFIGS).map(([strategyId, strategyConfig]) => (
                                <option key={strategyId} value={strategyId}>
                                  {strategyConfig.name}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* 전략 파라미터 */}
                          {strategyConfig?.parameters && Object.entries(strategyConfig.parameters).map(([key, param]: [string, StrategyParameter]) => (
                            <div key={key}>
                              <Label htmlFor={`${key}-${index}`}>
                                {key}
                                {param.description && (
                                  <span className="ml-1 text-xs text-gray-500">
                                    ({param.description})
                                  </span>
                                )}
                              </Label>
                              <Input
                                id={`${key}-${index}`}
                                type="number"
                                min={param.min}
                                max={param.max}
                                step={param.step || (param.type === 'int' ? 1 : 0.1)}
                                value={currentSetting?.strategyParams?.[key] || param.default}
                                onChange={e => {
                                  const value = param.type === 'int' ? 
                                    parseInt(e.target.value) : parseFloat(e.target.value);
                                  updateStrategyParam(index, key, value);
                                }}
                                className="mt-1"
                              />
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    </div>
                  </TabsContent>
                );
              })}
            </Tabs>

            {/* 액션 버튼 */}
            <div className="flex justify-between pt-6 border-t mt-6">
              <Button variant="outline" onClick={handleReset}>
                초기화
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={onClose}>
                  취소
                </Button>
                <Button onClick={handleApply}>
                  설정 적용
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdvancedSettingsForm;