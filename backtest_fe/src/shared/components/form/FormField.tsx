import React from 'react';
import { Input } from '@/shared/ui/input';
import { Textarea } from '@/shared/ui/textarea';
import { Label } from '@/shared/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { TEXT_STYLES } from '@/shared/styles/design-tokens';

export interface FormFieldProps {
  label: React.ReactNode;
  type?: 'text' | 'number' | 'date' | 'select' | 'textarea';
  value: string | number;
  onChange: (value: string | number) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  helpText?: string;
  options?: Array<{ value: string | number; label: string }>;
  className?: string;
  min?: number;
  max?: number;
  step?: number;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  error,
  helpText,
  options,
  className = '',
  min,
  max,
  step
}) => {
  // Label을 컨트롤과 프로그램적으로 연결하기 위한 id (P2-32). FormField가
  // 여러 번 렌더링돼도 useId()가 인스턴스마다 고유한 값을 준다.
  const fieldId = React.useId();

  // number 타입은 사용자가 입력 중인 원문 문자열을 로컬 상태로 그대로 담아
  // 둔다. 예전에는 매 입력마다 parseFloat(e.target.value) || 0으로
  // 커밋해서 필드를 비울 수 없었고(0으로 즉시 스냅), '-'나 '.5' 같은
  // 부분 입력이 거부됐다(P3-17). 문자열이 유효한 유한수로 파싱될 때만 그
  // 숫자를 부모에 커밋한다 — NaN은 절대 onChange로 전달하지 않는다.
  const [rawText, setRawText] = React.useState<string>(() => String(value));
  // 포커스 중에는 외부 value 변화로 로컬 텍스트를 덮어쓰지 않는다. 커밋
  // 즉시 부모가 새 value를 되돌려준다는 보장이 없으므로(예: 상위에서 값을
  // 그대로 반영하지 않거나 리렌더가 한 박자 늦는 경우), value만 보고
  // 동기화하면 타이핑 중간에 값이 되돌아갈 수 있다. blur된 상태에서만
  // (예: 전략 변경으로 기본값이 바뀔 때) 로컬 텍스트를 value로 재동기화한다.
  const [isFocused, setIsFocused] = React.useState(false);

  if (type === 'number' && !isFocused && rawText !== String(value)) {
    setRawText(String(value));
  }

  const commitNumber = (raw: string) => {
    if (raw.trim() === '') return;
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) return;
    onChange(parsed);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (type === 'number') {
      setRawText(e.target.value);
      commitNumber(e.target.value);
      return;
    }
    onChange(e.target.value);
  };

  const handleSelectChange = (newValue: string) => {
    onChange(newValue);
  };

  const renderInput = () => {
    switch (type) {
      case 'select':
        return (
          <Select
            value={value.toString()}
            onValueChange={handleSelectChange}
            disabled={disabled}
          >
            <SelectTrigger id={fieldId} className={error ? 'border-destructive' : ''}>
              <SelectValue placeholder={placeholder || "선택하세요"} />
            </SelectTrigger>
            <SelectContent>
              {options?.map((option) => (
                <SelectItem key={option.value} value={option.value.toString()}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'textarea':
        return (
          <Textarea
            id={fieldId}
            value={value.toString()}
            onChange={handleInputChange}
            placeholder={placeholder}
            disabled={disabled}
            className={error ? 'border-destructive' : ''}
            rows={4}
          />
        );

      case 'number':
        return (
          <Input
            id={fieldId}
            type="number"
            value={rawText}
            onChange={handleInputChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={disabled}
            min={min}
            max={max}
            step={step}
            className={error ? 'border-destructive' : ''}
          />
        );

      default:
        return (
          <Input
            id={fieldId}
            type={type}
            value={value.toString()}
            onChange={handleInputChange}
            placeholder={placeholder}
            disabled={disabled}
            min={min}
            max={max}
            step={step}
            className={`${error ? 'border-destructive' : ''} ${type === 'date' ? 'w-full text-left [&::-webkit-date-and-time-value]:text-left' : ''}`}
          />
        );
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <Label htmlFor={fieldId} className={TEXT_STYLES.label}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>

      <div className="w-full min-w-0">
        {renderInput()}
      </div>

      {helpText && (
        <p className={TEXT_STYLES.caption}>{helpText}</p>
      )}

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};
