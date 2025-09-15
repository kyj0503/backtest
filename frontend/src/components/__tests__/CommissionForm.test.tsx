import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import CommissionForm from '../CommissionForm';

describe('CommissionForm', () => {
  const defaultProps = {
    rebalanceFrequency: 'monthly',
    setRebalanceFrequency: vi.fn(),
    commission: 0.2,
    setCommission: vi.fn(),
  };

  it('기본 렌더링이 올바르게 되어야 함', () => {
    render(<CommissionForm {...defaultProps} />);

    // 라벨들이 렌더링되는지 확인
    expect(screen.getByText('리밸런싱 주기')).toBeInTheDocument();
    expect(screen.getByText('거래 수수료')).toBeInTheDocument();
    expect(screen.getByDisplayValue('0.2')).toBeInTheDocument();
  });

  it('수수료 값 변경 시 setCommission이 호출되어야 함', async () => {
    const mockSetCommission = vi.fn();
    const user = userEvent.setup();
    
    render(
      <CommissionForm
        {...defaultProps}
        setCommission={mockSetCommission}
      />
    );

    const input = screen.getByDisplayValue('0.2');
    await act(async () => {
      await user.clear(input);
      await user.type(input, '0.5');
    });

    expect(mockSetCommission).toHaveBeenCalled();
  });

  it('도움말 텍스트가 표시되어야 함', () => {
    render(<CommissionForm {...defaultProps} />);

    expect(screen.getByText('포트폴리오 비중을 다시 맞추는 주기')).toBeInTheDocument();
    expect(screen.getByText('예: 0.2 (0.2% 수수료)')).toBeInTheDocument();
  });
})
