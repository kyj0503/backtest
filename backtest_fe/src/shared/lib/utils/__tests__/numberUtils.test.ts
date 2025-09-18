import { describe, it, expect } from 'vitest';
import {
  formatNumber,
  formatCurrency,
  formatPercent,
  formatPrice,
  formatKoreanCurrency,
  formatLargeNumber,
  formatCompactNumber,
  formatScientific,
  formatRatio,
  formatBasisPoints,
  formatPercentChange,
  formatAbsoluteChange,
  formatVolume,
  formatMarketCap,
  formatSharpeRatio,
  formatVolatility,
  formatBeta,
  formatDrawdown,
  isValidNumber,
  parseNumber,
  parsePercentage,
  parseCurrency,
  clamp,
  round,
  roundUp,
  roundDown,
  average,
  median,
  standardDeviation,
  variance,
  normalize,
  denormalize,
  scale,
  safeDivide,
  getColorByValue,
  getIntensityColor
} from '../numberUtils';

describe('numberUtils', () => {
  describe('formatNumber', () => {
    it('숫자를 한국어 로케일로 포맷해야 함', () => {
      expect(formatNumber(1234.56, 2)).toBe('1,234.56');
      expect(formatNumber(1000000)).toBe('1,000,000');
      expect(formatNumber(0)).toBe('0');
    });

    it('소수점 자릿수를 지정할 수 있어야 함', () => {
      expect(formatNumber(1234.5678, 2)).toBe('1,234.57');
      expect(formatNumber(1234.5678, 0)).toBe('1,235');
    });
  });

  describe('formatCurrency', () => {
    it('큰 숫자를 축약된 통화 형식으로 포맷해야 함', () => {
      expect(formatCurrency(1234567890)).toBe('1.2B');
      expect(formatCurrency(1234567)).toBe('1.2M');
      expect(formatCurrency(1234)).toBe('1.2K');
    });

    it('작은 숫자는 천 단위 구분자와 함께 표시해야 함', () => {
      expect(formatCurrency(999)).toBe('999');
    });
  });

  describe('formatPercent', () => {
    it('백분율을 올바른 기호와 함께 포맷해야 함', () => {
      expect(formatPercent(12.34)).toBe('+12.34%');
      expect(formatPercent(-12.34)).toBe('-12.34%');
      expect(formatPercent(0)).toBe('0.00%');
    });

    it('소수점 자릿수를 지정할 수 있어야 함', () => {
      expect(formatPercent(12.3456, 1)).toBe('+12.3%');
      expect(formatPercent(12.3456, 3)).toBe('+12.346%');
    });
  });

  describe('formatPrice', () => {
    it('가격을 달러 형식으로 포맷해야 함', () => {
      expect(formatPrice(1234.56)).toBe('$1234.56');
      expect(formatPrice(0)).toBe('$0.00');
    });

    it('소수점 자릿수를 지정할 수 있어야 함', () => {
      expect(formatPrice(1234.5678, 3)).toBe('$1234.568');
    });
  });

  describe('formatKoreanCurrency', () => {
    it('한국 통화 단위로 포맷해야 함', () => {
      expect(formatKoreanCurrency(123456789)).toBe('1.2억원');
      expect(formatKoreanCurrency(12345)).toBe('1.2만원');
      expect(formatKoreanCurrency(999)).toBe('999원');
    });
  });

  describe('formatLargeNumber', () => {
    it('큰 숫자를 축약된 형태로 포맷해야 함', () => {
      expect(formatLargeNumber(1000000000000)).toBe('1.0T');
      expect(formatLargeNumber(1000000000)).toBe('1.0B');
      expect(formatLargeNumber(1000000)).toBe('1.0M');
      expect(formatLargeNumber(1000)).toBe('1.0K');
    });

    it('작은 숫자는 그대로 포맷해야 함', () => {
      expect(formatLargeNumber(999)).toBe('999');
    });
  });

  describe('formatCompactNumber', () => {
    it('국제화 API를 사용하여 컴팩트 형식으로 포맷해야 함', () => {
      expect(formatCompactNumber(1000000)).toBe('100만');
      expect(formatCompactNumber(1234567)).toBe('123.5만');
    });
  });

  describe('formatScientific', () => {
    it('과학적 표기법으로 포맷해야 함', () => {
      expect(formatScientific(1234.56)).toBe('1.23e+3');
      expect(formatScientific(0.001234, 3)).toBe('1.234e-3');
    });
  });

  describe('formatRatio', () => {
    it('비율을 계산하고 포맷해야 함', () => {
      expect(formatRatio(10, 5)).toBe('2.00');
      expect(formatRatio(1, 3, 3)).toBe('0.333');
    });

    it('0으로 나누기를 처리해야 함', () => {
      expect(formatRatio(10, 0)).toBe('N/A');
    });
  });

  describe('formatBasisPoints', () => {
    it('베이시스 포인트로 포맷해야 함', () => {
      expect(formatBasisPoints(0.01)).toBe('100bp');
      expect(formatBasisPoints(0.0025)).toBe('25bp');
    });
  });

  describe('formatPercentChange', () => {
    it('백분율 변화를 계산하고 포맷해야 함', () => {
      expect(formatPercentChange(100, 110)).toBe('+10.00%');
      expect(formatPercentChange(100, 90)).toBe('-10.00%');
    });

    it('0으로 나누기를 처리해야 함', () => {
      expect(formatPercentChange(0, 100)).toBe('N/A');
    });
  });

  describe('formatAbsoluteChange', () => {
    it('절대값 변화를 포맷해야 함', () => {
      expect(formatAbsoluteChange(100, 110)).toBe('+10.00');
      expect(formatAbsoluteChange(100, 90)).toBe('-10.00');
    });
  });

  describe('formatVolume', () => {
    it('거래량을 축약된 형태로 포맷해야 함', () => {
      expect(formatVolume(1234567890)).toBe('1.2B');
      expect(formatVolume(1234567)).toBe('1.2M');
      expect(formatVolume(1234)).toBe('1.2K');
    });
  });

  describe('formatMarketCap', () => {
    it('시가총액을 포맷해야 함', () => {
      expect(formatMarketCap(1000000000)).toBe('1.0B');
    });
  });

  describe('formatSharpeRatio', () => {
    it('샤프 비율을 3자리 소수점으로 포맷해야 함', () => {
      expect(formatSharpeRatio(1.2345)).toBe('1.234');
    });
  });

  describe('formatVolatility', () => {
    it('변동성을 백분율로 포맷해야 함', () => {
      expect(formatVolatility(0.15)).toBe('+15.00%');
    });
  });

  describe('formatBeta', () => {
    it('베타를 3자리 소수점으로 포맷해야 함', () => {
      expect(formatBeta(1.2345)).toBe('1.234');
    });
  });

  describe('formatDrawdown', () => {
    it('드로우다운을 절대값 백분율로 포맷해야 함', () => {
      expect(formatDrawdown(-0.15)).toBe('+0.15%');
      expect(formatDrawdown(0.15)).toBe('+0.15%');
    });
  });

  describe('isValidNumber', () => {
    it('유효한 숫자에 대해 true를 반환해야 함', () => {
      expect(isValidNumber(123)).toBe(true);
      expect(isValidNumber(-123.45)).toBe(true);
      expect(isValidNumber(0)).toBe(true);
    });

    it('무효한 값에 대해 false를 반환해야 함', () => {
      expect(isValidNumber(NaN)).toBe(false);
      expect(isValidNumber(Infinity)).toBe(false);
      expect(isValidNumber('invalid')).toBe(false);
    });
  });

  describe('parseNumber', () => {
    it('문자열을 숫자로 변환해야 함', () => {
      expect(parseNumber('123.45')).toBe(123.45);
      expect(parseNumber('-123')).toBe(-123);
    });

    it('무효한 문자열에 대해 null을 반환해야 함', () => {
      expect(parseNumber('invalid')).toBeNull();
      expect(parseNumber('')).toBeNull();
    });
  });

  describe('parsePercentage', () => {
    it('백분율 문자열을 소수로 변환해야 함', () => {
      expect(parsePercentage('12.34%')).toBe(0.1234);
      expect(parsePercentage('100')).toBe(1);
    });

    it('무효한 백분율에 대해 null을 반환해야 함', () => {
      expect(parsePercentage('invalid')).toBeNull();
    });
  });

  describe('parseCurrency', () => {
    it('통화 문자열을 숫자로 변환해야 함', () => {
      expect(parseCurrency('$1,234.56')).toBe(1234.56);
      expect(parseCurrency('₩10,000')).toBe(10000);
    });

    it('무효한 통화에 대해 null을 반환해야 함', () => {
      expect(parseCurrency('invalid')).toBeNull();
    });
  });

  describe('clamp', () => {
    it('값을 지정된 범위로 제한해야 함', () => {
      expect(clamp(5, 0, 10)).toBe(5);
      expect(clamp(-5, 0, 10)).toBe(0);
      expect(clamp(15, 0, 10)).toBe(10);
    });
  });

  describe('round', () => {
    it('지정된 소수점 자릿수로 반올림해야 함', () => {
      expect(round(1.2345, 2)).toBe(1.23);
      expect(round(1.2355, 2)).toBe(1.24);
      expect(round(1.2345, 0)).toBe(1);
    });
  });

  describe('roundUp', () => {
    it('지정된 소수점 자릿수로 올림해야 함', () => {
      expect(roundUp(1.2345, 2)).toBe(1.24);
      expect(roundUp(1.2301, 2)).toBe(1.24);
    });
  });

  describe('roundDown', () => {
    it('지정된 소수점 자릿수로 내림해야 함', () => {
      expect(roundDown(1.2345, 2)).toBe(1.23);
      expect(roundDown(1.2399, 2)).toBe(1.23);
    });
  });

  describe('average', () => {
    it('평균을 계산해야 함', () => {
      expect(average([1, 2, 3, 4, 5])).toBe(3);
      expect(average([10, 20])).toBe(15);
    });

    it('빈 배열에 대해 0을 반환해야 함', () => {
      expect(average([])).toBe(0);
    });
  });

  describe('median', () => {
    it('홀수 개수의 값에서 중앙값을 찾아야 함', () => {
      expect(median([1, 3, 2, 5, 4])).toBe(3);
    });

    it('짝수 개수의 값에서 중앙값을 계산해야 함', () => {
      expect(median([1, 2, 3, 4])).toBe(2.5);
    });

    it('빈 배열에 대해 0을 반환해야 함', () => {
      expect(median([])).toBe(0);
    });
  });

  describe('standardDeviation', () => {
    it('표준편차를 계산해야 함', () => {
      const result = standardDeviation([1, 2, 3, 4, 5]);
      expect(result).toBeCloseTo(1.414, 2); // √2 ≈ 1.414
    });

    it('모든 값이 같을 때 0을 반환해야 함', () => {
      expect(standardDeviation([5, 5, 5, 5])).toBe(0);
    });

    it('빈 배열에 대해 0을 반환해야 함', () => {
      expect(standardDeviation([])).toBe(0);
    });
  });

  describe('variance', () => {
    it('분산을 계산해야 함', () => {
      const result = variance([1, 2, 3, 4, 5]);
      expect(result).toBeCloseTo(2.0, 1); // 분산
    });

    it('빈 배열에 대해 0을 반환해야 함', () => {
      expect(variance([])).toBe(0);
    });
  });

  describe('normalize', () => {
    it('값을 0-1 범위로 정규화해야 함', () => {
      expect(normalize(5, 0, 10)).toBe(0.5);
      expect(normalize(0, 0, 10)).toBe(0);
      expect(normalize(10, 0, 10)).toBe(1);
    });

    it('최대값과 최소값이 같을 때 0을 반환해야 함', () => {
      expect(normalize(5, 5, 5)).toBe(0);
    });
  });

  describe('denormalize', () => {
    it('정규화된 값을 원래 범위로 복원해야 함', () => {
      expect(denormalize(0.5, 0, 10)).toBe(5);
      expect(denormalize(0, 0, 10)).toBe(0);
      expect(denormalize(1, 0, 10)).toBe(10);
    });
  });

  describe('scale', () => {
    it('한 범위의 값을 다른 범위로 변환해야 함', () => {
      expect(scale(5, 0, 10, 0, 100)).toBe(50);
      expect(scale(2, 0, 10, 20, 30)).toBe(22);
    });
  });

  describe('safeDivide', () => {
    it('일반적인 나눗셈을 수행해야 함', () => {
      expect(safeDivide(10, 2)).toBe(5);
    });

    it('0으로 나누기 시 fallback 값을 반환해야 함', () => {
      expect(safeDivide(10, 0)).toBe(0);
      expect(safeDivide(10, 0, -1)).toBe(-1);
    });
  });

  describe('getColorByValue', () => {
    it('임계값을 기준으로 색상을 반환해야 함', () => {
      expect(getColorByValue(5, 0)).toBe('#10B981'); // 양수 -> 녹색
      expect(getColorByValue(-5, 0)).toBe('#EF4444'); // 음수 -> 빨간색
      expect(getColorByValue(0, 0)).toBe('#10B981'); // 같음 -> 녹색
    });

    it('사용자 정의 임계값을 사용해야 함', () => {
      expect(getColorByValue(5, 10)).toBe('#EF4444'); // 5 < 10 -> 빨간색
      expect(getColorByValue(15, 10)).toBe('#10B981'); // 15 >= 10 -> 녹색
    });
  });

  describe('getIntensityColor', () => {
    it('값의 강도에 따라 투명도가 적용된 색상을 반환해야 함', () => {
      const result = getIntensityColor(5, 0, 10);
      expect(result).toMatch(/rgba\(16, 185, 129, 0\.\d+\)/); // 양수 -> 녹색 계열
    });

    it('음수에 대해 빨간색 계열을 반환해야 함', () => {
      const result = getIntensityColor(-5, 0, 10);
      expect(result).toMatch(/rgba\(239, 68, 68, 0\.\d+\)/); // 음수 -> 빨간색 계열
    });
  });
});
