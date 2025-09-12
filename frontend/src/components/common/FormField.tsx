import React from 'react';

export interface FormFieldProps {
  label: string;
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
  const baseInputClassName = `
    block w-full px-3 py-2 border rounded-md shadow-sm
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
    disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed
    ${error ? 'border-destructive text-destructive placeholder-destructive/50 focus:border-destructive focus:ring-destructive' : 'border-input'}
  `.trim();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const newValue = type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value;
    onChange(newValue);
  };

  const renderInput = () => {
    switch (type) {
      case 'select':
        return (
          <select
            value={value}
            onChange={handleChange}
            disabled={disabled}
            required={required}
            className={baseInputClassName}
          >
            {options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={handleChange}
            placeholder={placeholder}
            disabled={disabled}
            required={required}
            className={`${baseInputClassName} resize-vertical min-h-[100px]`}
            rows={4}
          />
        );
      
      default:
        return (
          <input
            type={type}
            value={value}
            onChange={handleChange}
            placeholder={placeholder}
            disabled={disabled}
            required={required}
            min={min}
            max={max}
            step={step}
            className={baseInputClassName}
          />
        );
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </label>
      
      {renderInput()}
      
      {helpText && (
        <p className="text-sm text-gray-500">{helpText}</p>
      )}
      
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};
