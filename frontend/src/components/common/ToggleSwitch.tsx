import React from 'react';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  labelPosition?: 'left' | 'right';
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md',
  className = '',
  labelPosition = 'right',
}) => {

  const getSizeClasses = () => {
    const sizes = {
      sm: {
        switch: 'w-8 h-4',
        thumb: 'w-3 h-3',
        translate: 'translate-x-4',
      },
      md: {
        switch: 'w-11 h-6',
        thumb: 'w-5 h-5',
        translate: 'translate-x-5',
      },
      lg: {
        switch: 'w-14 h-7',
        thumb: 'w-6 h-6',
        translate: 'translate-x-7',
      },
    };
    return sizes[size];
  };

  const sizeClasses = getSizeClasses();

  const switchClasses = [
    'relative',
    'inline-flex',
    'items-center',
    'rounded-full',
    'transition-colors',
    'duration-200',
    'ease-in-out',
    'focus-visible:outline-none',
    'focus-visible:ring-2',
    'focus-visible:ring-offset-2',
    'focus-visible:ring-blue-500',
    sizeClasses.switch,
    disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
    checked ? 'bg-primary' : 'bg-input',
  ].join(' ');

  const thumbClasses = [
    'inline-block',
    'rounded-full',
    'bg-background',
    'shadow',
    'transform',
    'ring-0',
    'transition',
    'duration-200',
    'ease-in-out',
    sizeClasses.thumb,
    checked ? sizeClasses.translate : 'translate-x-0',
  ].join(' ');

  const handleToggle = () => {
    if (!disabled) {
      onChange(!checked);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleToggle();
    }
  };

  const switchElement = (
    <button
      type="button"
      className={switchClasses}
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={handleToggle}
      onKeyDown={handleKeyDown}
    >
      <span className={thumbClasses} />
    </button>
  );

  if (!label && !description) {
    return <div className={className}>{switchElement}</div>;
  }

  return (
    <div className={`flex items-start ${className}`}>
      {labelPosition === 'left' && (
        <div className="mr-3 flex-1">
          {label && (
            <label className="text-sm font-medium text-gray-900">
              {label}
            </label>
          )}
          {description && (
            <p className="text-sm text-gray-500">{description}</p>
          )}
        </div>
      )}
      
      <div className="flex-shrink-0">
        {switchElement}
      </div>
      
      {labelPosition === 'right' && (
        <div className="ml-3 flex-1">
          {label && (
            <label className="text-sm font-medium text-gray-900">
              {label}
            </label>
          )}
          {description && (
            <p className="text-sm text-gray-500">{description}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default ToggleSwitch;
