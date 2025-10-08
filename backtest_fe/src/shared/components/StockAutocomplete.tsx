import React from 'react';
import { Input } from '@/shared/ui/input';

interface StockAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

/**
 * 단순 종목 심볼 입력 컴포넌트
 * 자동완성 기능 없이 직접 입력만 지원
 */
const StockAutocomplete: React.FC<StockAutocompleteProps> = ({
  value,
  onChange,
  placeholder = "종목 심볼 입력 (예: AAPL)",
  className = ""
}) => {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value.toUpperCase());
  };

  return (
    <Input
      type="text"
      value={value}
      onChange={handleInputChange}
      placeholder={placeholder}
      maxLength={10}
      className={className}
      autoComplete="off"
    />
  );
};

export default StockAutocomplete;
