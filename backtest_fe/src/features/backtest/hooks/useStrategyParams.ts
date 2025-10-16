import { useCallback } from 'react';
import { STRATEGY_CONFIGS, StrategyConfig, StrategyParameter } from '../model/strategyConfig';
import { StrategyParamValue } from '../model/api-types';

export interface StrategyParam {
  key: string;
  label: string;
  value: StrategyParamValue;
  min: number;
  max: number;
  default: number;
  description?: string;
}

export interface UseStrategyParamsReturn {
  getStrategyConfig: (strategy: string) => StrategyConfig | undefined;
  getDefaultParams: (strategy: string) => Record<string, number>;
  getStrategyParams: (strategy: string, currentParams: Record<string, StrategyParamValue>) => StrategyParam[];
  updateParam: (currentParams: Record<string, StrategyParamValue>, key: string, value: string) => Record<string, StrategyParamValue>;
  validateParams: (strategy: string, params: Record<string, StrategyParamValue>) => string[];
  getParamLabel: (key: string) => string;
}

export const useStrategyParams = (): UseStrategyParamsReturn => {
  const getStrategyConfig = useCallback((strategy: string) => {
    return STRATEGY_CONFIGS[strategy as keyof typeof STRATEGY_CONFIGS];
  }, []);

  const getDefaultParams = useCallback((strategy: string): Record<string, number> => {
    const config = getStrategyConfig(strategy);
    if (!config || !config.parameters) return {};

    const defaultParams: Record<string, number> = {};
    Object.entries(config.parameters).forEach(([key, param]: [string, StrategyParameter]) => {
      defaultParams[key] = param.default;
    });
    return defaultParams;
  }, [getStrategyConfig]);

  const getStrategyParams = useCallback((strategy: string, currentParams: Record<string, StrategyParamValue>): StrategyParam[] => {
    const config = getStrategyConfig(strategy);
    if (!config || !config.parameters) return [];

    return Object.entries(config.parameters).map(([key, param]: [string, StrategyParameter]) => {
      return {
        key,
        label: getParamLabel(key),
        value: currentParams[key] !== undefined ? currentParams[key] : param.default,
        min: param.min,
        max: param.max,
        default: param.default,
        description: param.description
      };
    });
  }, [getStrategyConfig]);

  const updateParam = useCallback((currentParams: Record<string, StrategyParamValue>, key: string, value: string): Record<string, StrategyParamValue> => {
    return {
      ...currentParams,
      [key]: value
    };
  }, []);

  const validateParams = useCallback((strategy: string, params: Record<string, StrategyParamValue>): string[] => {
    const config = getStrategyConfig(strategy);
    const errors: string[] = [];

    if (!config || !config.parameters) return errors;

    Object.entries(config.parameters).forEach(([key, param]: [string, StrategyParameter]) => {
      const value = params[key];

      if (value === undefined || value === null || value === '') {
        errors.push(`${getParamLabel(key)} 값을 입력해주세요.`);
        return;
      }

      const numValue = Number(value);
      if (isNaN(numValue)) {
        errors.push(`${getParamLabel(key)}는 숫자여야 합니다.`);
        return;
      }

      if (numValue < param.min || numValue > param.max) {
        errors.push(`${getParamLabel(key)}는 ${param.min} ~ ${param.max} 사이여야 합니다.`);
      }
    });

    return errors;
  }, [getStrategyConfig]);

  const getParamLabel = useCallback((key: string): string => {
    const labelMap: Record<string, string> = {
      'short_window': '단기 이동평균 기간',
      'long_window': '장기 이동평균 기간',
      'rsi_period': 'RSI 기간',
      'rsi_oversold': 'RSI 과매도 기준',
      'rsi_overbought': 'RSI 과매수 기준',
      'bb_period': '볼린저 밴드 기간',
      'bb_std': '볼린저 밴드 표준편차',
      'macd_fast': 'MACD 빠른 기간',
      'macd_slow': 'MACD 느린 기간',
      'macd_signal': 'MACD 신호선 기간',
      'fast_window': '단기 EMA 기간',
      'slow_window': '장기 EMA 기간'
    };
    
    return labelMap[key] || key;
  }, []);

  return {
    getStrategyConfig,
    getDefaultParams,
    getStrategyParams,
    updateParam,
    validateParams,
    getParamLabel
  };
};
