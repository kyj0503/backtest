import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { act } from 'react';
import { useBacktestForm } from '../useBacktestForm';

describe('useBacktestForm', () => {

  describe('초기 상태', () => {
    it('기본값으로 올바르게 초기화되어야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      expect(result.current.state.portfolio).toHaveLength(1);
      expect(result.current.state.portfolio[0].symbol).toBe('');
      expect(result.current.state.portfolio[0].amount).toBe(10000);
      expect(result.current.state.dates.startDate).toBe('2023-01-01');
      expect(result.current.state.dates.endDate).toBe('2024-12-31');
      expect(result.current.state.strategy.selectedStrategy).toBe('buy_and_hold');
      expect(result.current.state.strategy.strategyParams).toEqual({});
      expect(result.current.state.settings.commission).toBe(0.2);
      expect(result.current.state.settings.rebalanceFrequency).toBe('monthly');
      expect(result.current.state.ui.errors).toEqual([]);
      expect(result.current.state.ui.isLoading).toBe(false);
    });
  });

  describe('포트폴리오 관리', () => {
    it('주식 추가가 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.addStock();
      });
      
      expect(result.current.state.portfolio).toHaveLength(2);
    });

    it('현금 추가가 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.addCash();
      });
      
      expect(result.current.state.portfolio).toHaveLength(2);
      expect(result.current.state.portfolio[1].assetType).toBe('cash');
    });

    it('주식 정보 업데이트가 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.updateStock(0, 'symbol', 'AAPL');
        result.current.actions.updateStock(0, 'amount', 5000);
      });
      
      expect(result.current.state.portfolio[0].symbol).toBe('AAPL');
      expect(result.current.state.portfolio[0].amount).toBe(5000);
    });

    it('주식 제거가 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.addStock();
        result.current.actions.removeStock(0);
      });
      
      expect(result.current.state.portfolio).toHaveLength(1);
    });

    it('총 투자 금액 계산이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.updateStock(0, 'amount', 5000);
        result.current.actions.addStock();
        result.current.actions.updateStock(1, 'amount', 3000);
      });
      
      expect(result.current.helpers.getTotalAmount()).toBe(8000);
    });
  });

  describe('날짜 관리', () => {
    it('시작 날짜 설정이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setStartDate('2022-01-01');
      });
      
      expect(result.current.state.dates.startDate).toBe('2022-01-01');
    });

    it('종료 날짜 설정이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setEndDate('2023-12-31');
      });
      
      expect(result.current.state.dates.endDate).toBe('2023-12-31');
    });
  });

  describe('전략 관리', () => {
    it('전략 선택이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setSelectedStrategy('sma_cross');
      });
      
      expect(result.current.state.strategy.selectedStrategy).toBe('sma_cross');
    });

    it('전략 파라미터 업데이트가 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.updateStrategyParam('short_window', '10');
        result.current.actions.updateStrategyParam('long_window', '30');
      });
      
      expect(result.current.state.strategy.strategyParams.short_window).toBe('10');
      expect(result.current.state.strategy.strategyParams.long_window).toBe('30');
    });
  });

  describe('설정 관리', () => {
    it('리밸런싱 빈도 설정이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setRebalanceFrequency('weekly');
      });
      
      expect(result.current.state.settings.rebalanceFrequency).toBe('weekly');
    });

    it('수수료 설정이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setCommission(0.1);
      });
      
      expect(result.current.state.settings.commission).toBe(0.1);
    });
  });

  describe('UI 상태 관리', () => {
    it('에러 설정이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      const errors = ['필수 필드가 누락되었습니다'];
      
      act(() => {
        result.current.actions.setErrors(errors);
      });
      
      expect(result.current.state.ui.errors).toEqual(errors);
    });

    it('로딩 상태 설정이 올바르게 작동해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setLoading(true);
      });
      
      expect(result.current.state.ui.isLoading).toBe(true);
    });
  });

  describe('폼 검증', () => {
    it('빈 심볼이 있을 때 검증 오류가 발생해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      const errors = result.current.helpers.validateForm();
      
      expect(errors).toContain('1번째 종목의 심볼을 입력해주세요.');
    });

    it('유효한 폼에서 검증 오류가 없어야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.updateStock(0, 'symbol', 'AAPL');
        result.current.actions.updateStock(0, 'amount', 10000);
        result.current.actions.setStartDate('2023-01-01');
        result.current.actions.setEndDate('2023-12-31');
        result.current.actions.setCommission(0.1);
      });
      
      const errors = result.current.helpers.validateForm();
      
      expect(errors).toHaveLength(0);
    });

    it('시작일이 종료일보다 늦을 때 검증 오류가 발생해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setStartDate('2023-12-31');
        result.current.actions.setEndDate('2023-01-01');
      });
      
      const errors = result.current.helpers.validateForm();
      
      expect(errors).toContain('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
    });

    it('수수료가 범위를 벗어날 때 검증 오류가 발생해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      act(() => {
        result.current.actions.setCommission(10);
      });
      
      const errors = result.current.helpers.validateForm();
      
      expect(errors).toContain('수수료는 0% ~ 5% 사이여야 합니다.');
    });
  });

  describe('폼 리셋', () => {
    it('resetForm이 모든 상태를 초기화해야 함', () => {
      const { result } = renderHook(() => useBacktestForm());
      
      // 폼에 데이터 설정
      act(() => {
        result.current.actions.updateStock(0, 'symbol', 'AAPL');
        result.current.actions.setStartDate('2022-01-01');
        result.current.actions.setSelectedStrategy('sma_cross');
        result.current.actions.setCommission(0.5);
        result.current.actions.setErrors(['테스트 에러']);
        result.current.actions.setLoading(true);
      });
      
      // 폼 리셋
      act(() => {
        result.current.actions.resetForm();
      });
      
      expect(result.current.state.portfolio[0].symbol).toBe('');
      expect(result.current.state.dates.startDate).toBe('2023-01-01');
      expect(result.current.state.dates.endDate).toBe('2024-12-31');
      expect(result.current.state.strategy.selectedStrategy).toBe('buy_and_hold');
      expect(result.current.state.settings.commission).toBe(0.2);
      expect(result.current.state.ui.errors).toEqual([]);
      expect(result.current.state.ui.isLoading).toBe(false);
    });
  });
});
