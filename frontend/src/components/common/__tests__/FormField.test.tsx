import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormField } from '../FormField';

describe('FormField', () => {
  describe('기본 렌더링', () => {
    it('라벨과 입력 필드가 올바르게 렌더링되어야 함', () => {
      render(
        <FormField
          label="테스트 라벨"
          type="text"
          value=""
          onChange={() => {}}
        />
      );

      expect(screen.getByText('테스트 라벨')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('필수 라벨이 표시되어야 함', () => {
      render(
        <FormField
          label="필수 필드"
          type="text"
          value=""
          onChange={() => {}}
          required
        />
      );

      expect(screen.getByText(/필수 필드/)).toBeInTheDocument();
      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('도움말 텍스트가 표시되어야 함', () => {
      const helpText = '이것은 도움말 텍스트입니다';
      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={() => {}}
          helpText={helpText}
        />
      );

      expect(screen.getByText(helpText)).toBeInTheDocument();
    });
  });

  describe('에러 처리', () => {
    it('에러 메시지가 표시되어야 함', () => {
      const errorMessage = '이 필드는 필수입니다';
      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={() => {}}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('에러가 있을 때 에러 스타일이 적용되어야 함', () => {
      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={() => {}}
          error="에러 메시지"
        />
      );

      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border-destructive');
    });
  });

  describe('입력 타입별 렌더링', () => {
    it('select 타입이 올바르게 렌더링되어야 함', () => {
      const options = [
        { value: 'option1', label: '옵션 1' },
        { value: 'option2', label: '옵션 2' }
      ];

      render(
        <FormField
          label="선택 필드"
          type="select"
          value=""
          onChange={() => {}}
          options={options}
        />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
      expect(screen.getByText('옵션 1')).toBeInTheDocument();
      expect(screen.getByText('옵션 2')).toBeInTheDocument();
    });

    it('textarea 타입이 올바르게 렌더링되어야 함', () => {
      render(
        <FormField
          label="텍스트 영역"
          type="textarea"
          value=""
          onChange={() => {}}
        />
      );

      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('textbox').tagName).toBe('TEXTAREA');
    });

    it('number 타입이 올바르게 렌더링되어야 함', () => {
      render(
        <FormField
          label="숫자 필드"
          type="number"
          value=""
          onChange={() => {}}
          min={0}
          max={100}
          step={1}
        />
      );

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('type', 'number');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
      expect(input).toHaveAttribute('step', '1');
    });

    it('date 타입이 올바르게 렌더링되어야 함', () => {
      render(
        <FormField
          label="날짜 필드"
          type="date"
          value=""
          onChange={() => {}}
        />
      );

      const input = screen.getByDisplayValue('');
      expect(input).toHaveAttribute('type', 'date');
    });
  });

  describe('사용자 상호작용', () => {
    it('텍스트 입력 변경 시 onChange가 호출되어야 함', async () => {
      const handleChange = vi.fn();
      const user = userEvent.setup();

      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={handleChange}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, 'test');

      expect(handleChange).toHaveBeenCalled();
    });

    it('select 변경 시 onChange가 호출되어야 함', async () => {
      const handleChange = vi.fn();
      const user = userEvent.setup();
      const options = [
        { value: 'option1', label: '옵션 1' },
        { value: 'option2', label: '옵션 2' }
      ];

      render(
        <FormField
          label="선택 필드"
          type="select"
          value=""
          onChange={handleChange}
          options={options}
        />
      );

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'option1');

      expect(handleChange).toHaveBeenCalledWith('option1');
    });

    it('숫자 입력 시 올바른 값이 전달되어야 함', async () => {
      const handleChange = vi.fn();
      const user = userEvent.setup();

      render(
        <FormField
          label="숫자 필드"
          type="number"
          value=""
          onChange={handleChange}
        />
      );

      const input = screen.getByRole('spinbutton');
      await user.clear(input);
      await user.type(input, '123');

      // 숫자 타입에서 문자별로 parseFloat 처리되므로 마지막 문자인 '3'이 3으로 변환됨
      expect(handleChange).toHaveBeenLastCalledWith(3);
    });
  });

  describe('속성 전달', () => {
    it('disabled 상태가 올바르게 적용되어야 함', () => {
      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={() => {}}
          disabled
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });

    it('placeholder가 올바르게 설정되어야 함', () => {
      const placeholder = '값을 입력하세요';
      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={() => {}}
          placeholder={placeholder}
        />
      );

      expect(screen.getByPlaceholderText(placeholder)).toBeInTheDocument();
    });

    it('value가 올바르게 설정되어야 함', () => {
      render(
        <FormField
          label="테스트"
          type="text"
          value="초기값"
          onChange={() => {}}
        />
      );

      expect(screen.getByDisplayValue('초기값')).toBeInTheDocument();
    });

    it('숫자 value가 올바르게 설정되어야 함', () => {
      render(
        <FormField
          label="숫자 필드"
          type="number"
          value={42}
          onChange={() => {}}
        />
      );

      expect(screen.getByDisplayValue('42')).toBeInTheDocument();
    });
  });

  describe('옵션 처리', () => {
    it('빈 옵션 배열을 처리해야 함', () => {
      render(
        <FormField
          label="선택 필드"
          type="select"
          value=""
          onChange={() => {}}
          options={[]}
        />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('숫자 value를 가진 옵션을 처리해야 함', () => {
      const options = [
        { value: 1, label: '옵션 1' },
        { value: 2, label: '옵션 2' }
      ];

      render(
        <FormField
          label="선택 필드"
          type="select"
          value=""
          onChange={() => {}}
          options={options}
        />
      );

      expect(screen.getByText('옵션 1')).toBeInTheDocument();
      expect(screen.getByText('옵션 2')).toBeInTheDocument();
    });
  });

  describe('스타일링', () => {
    it('사용자 정의 className이 적용되어야 함', () => {
      render(
        <FormField
          label="테스트"
          type="text"
          value=""
          onChange={() => {}}
          className="custom-class"
        />
      );

      const container = screen.getByRole('textbox').closest('.space-y-2');
      expect(container).toHaveClass('custom-class');
    });
  });
});
