import React, { useState, useRef, useEffect } from 'react';

interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SearchableSelectProps {
  options: Option[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  className?: string;
  dropdownClassName?: string;
  noOptionsMessage?: string;
  loading?: boolean;
  onSearch?: (query: string) => void;
}

const SearchableSelect: React.FC<SearchableSelectProps> = ({
  options,
  value,
  onChange,
  placeholder = '옵션을 선택하세요',
  searchPlaceholder = '검색...',
  disabled = false,
  clearable = false,
  className = '',
  dropdownClassName = '',
  noOptionsMessage = '옵션이 없습니다',
  loading = false,
  onSearch,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find(option => option.value === value);

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    if (onSearch) {
      onSearch(searchQuery);
    }
  }, [searchQuery, onSearch]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const handleToggle = () => {
    if (disabled) return;
    setIsOpen(!isOpen);
    setSearchQuery('');
    setHighlightedIndex(-1);
  };

  const handleSelect = (option: Option) => {
    if (option.disabled) return;
    onChange(option.value);
    setIsOpen(false);
    setSearchQuery('');
    setHighlightedIndex(-1);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange('');
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev => 
            prev < filteredOptions.length - 1 ? prev + 1 : 0
          );
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : filteredOptions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (isOpen && highlightedIndex >= 0) {
          handleSelect(filteredOptions[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSearchQuery('');
        setHighlightedIndex(-1);
        break;
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Trigger */}
      <div
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={`
          w-full px-3 py-2 text-left rounded-md border shadow-sm cursor-pointer
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
          ${disabled ? 'bg-muted cursor-not-allowed text-muted-foreground' : 'bg-background'}
        `}
        style={{ borderColor: 'hsl(var(--input))' }}
        tabIndex={disabled ? -1 : 0}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <div className="flex items-center justify-between">
          <span className={selectedOption ? 'text-foreground' : 'text-muted-foreground'}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <div className="flex items-center space-x-1">
            {clearable && selectedOption && !disabled && (
              <button
                onClick={handleClear}
                className="p-1 hover:bg-accent rounded"
                aria-label="선택 해제"
              >
                <svg className="w-4 h-4 text-muted-foreground" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            )}
            <svg
              className={`w-5 h-5 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className={`
            absolute
            z-50
            w-full
            mt-1
            rounded-md border bg-popover shadow-md animate-in
            max-h-60
            overflow-auto
            ${dropdownClassName}
          `}
        >
          {/* Search input */}
          <div className="p-2 border-b">
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={searchPlaceholder}
              className="form-control"
            />
          </div>

          {/* Options */}
          <div role="listbox">
            {loading ? (
              <div className="px-3 py-2 text-center text-muted-foreground">
                로딩 중...
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-center text-muted-foreground">
                {noOptionsMessage}
              </div>
            ) : (
              filteredOptions.map((option, index) => (
                <div
                  key={option.value}
                  onClick={() => handleSelect(option)}
                  className={`
                    px-3 py-2 cursor-pointer select-none
                    ${option.disabled ? 'text-gray-400 cursor-not-allowed' : 'text-gray-900'}
                    ${index === highlightedIndex ? 'bg-accent' : 'hover:bg-accent/50'}
                    ${option.value === value ? 'bg-primary text-primary-foreground' : ''}
                  `}
                  role="option"
                  aria-selected={option.value === value}
                >
                  {option.label}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchableSelect;
