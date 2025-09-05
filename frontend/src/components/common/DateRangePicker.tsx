import React, { useState, useRef, useEffect } from 'react';

interface DateRangePickerProps {
  startDate?: string;
  endDate?: string;
  onChange: (startDate: string, endDate: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  minDate?: string;
  maxDate?: string;
  presets?: Array<{
    label: string;
    startDate: string;
    endDate: string;
  }>;
  showPresets?: boolean;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate = '',
  endDate = '',
  onChange,
  placeholder = '날짜 범위를 선택하세요',
  disabled = false,
  className = '',
  minDate,
  maxDate,
  presets = [
    { label: '오늘', startDate: new Date().toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0] },
    { label: '최근 7일', startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0] },
    { label: '최근 30일', startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0] },
    { label: '최근 90일', startDate: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0] },
    { label: '최근 1년', startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0] },
  ],
  showPresets = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempStartDate, setTempStartDate] = useState(startDate);
  const [tempEndDate, setTempEndDate] = useState(endDate);
  
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTempStartDate(startDate);
    setTempEndDate(endDate);
  }, [startDate, endDate]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        // Reset temp values if not applied
        setTempStartDate(startDate);
        setTempEndDate(endDate);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [startDate, endDate]);

  const formatDateRange = (start: string, end: string): string => {
    if (!start && !end) return '';
    if (start && !end) return `${start} ~`;
    if (!start && end) return `~ ${end}`;
    if (start === end) return start;
    return `${start} ~ ${end}`;
  };

  const handleApply = () => {
    if (tempStartDate && tempEndDate && tempStartDate > tempEndDate) {
      // Swap dates if start is after end
      onChange(tempEndDate, tempStartDate);
    } else {
      onChange(tempStartDate, tempEndDate);
    }
    setIsOpen(false);
  };

  const handleClear = () => {
    setTempStartDate('');
    setTempEndDate('');
    onChange('', '');
    setIsOpen(false);
  };

  const handlePresetSelect = (preset: typeof presets[0]) => {
    setTempStartDate(preset.startDate);
    setTempEndDate(preset.endDate);
    onChange(preset.startDate, preset.endDate);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Trigger */}
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`
          w-full
          px-3
          py-2
          text-left
          bg-white
          border
          border-gray-300
          rounded-md
          shadow-sm
          cursor-pointer
          focus:outline-none
          focus:ring-2
          focus:ring-blue-500
          focus:border-blue-500
          ${disabled ? 'bg-gray-50 cursor-not-allowed' : 'hover:border-gray-400'}
        `}
        tabIndex={disabled ? -1 : 0}
      >
        <div className="flex items-center justify-between">
          <span className={startDate || endDate ? 'text-gray-900' : 'text-gray-500'}>
            {formatDateRange(startDate, endDate) || placeholder}
          </span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          <div className="p-4">
            {/* Date inputs */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시작 날짜
                </label>
                <input
                  type="date"
                  value={tempStartDate}
                  onChange={(e) => setTempStartDate(e.target.value)}
                  min={minDate}
                  max={maxDate}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  종료 날짜
                </label>
                <input
                  type="date"
                  value={tempEndDate}
                  onChange={(e) => setTempEndDate(e.target.value)}
                  min={minDate || tempStartDate}
                  max={maxDate}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Validation message */}
              {tempStartDate && tempEndDate && tempStartDate > tempEndDate && (
                <p className="text-sm text-red-600">
                  시작 날짜는 종료 날짜보다 이전이어야 합니다.
                </p>
              )}
            </div>

            {/* Presets */}
            {showPresets && presets.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  빠른 선택
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {presets.map((preset, index) => (
                    <button
                      key={index}
                      onClick={() => handlePresetSelect(preset)}
                      className="px-3 py-2 text-sm text-left text-gray-700 hover:bg-gray-50 rounded-md border border-gray-200 hover:border-gray-300"
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-between mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={handleClear}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                지우기
              </button>
              <div className="space-x-2">
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  onClick={handleApply}
                  disabled={!tempStartDate || !tempEndDate}
                  className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  적용
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;
