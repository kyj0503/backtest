import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  maxVisiblePages?: number;
  className?: string;
  disabled?: boolean;
}

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  showFirstLast = true,
  showPrevNext = true,
  maxVisiblePages = 5,
  className = '',
  disabled = false,
}) => {
  if (totalPages <= 1) return null;

  const getVisiblePages = (): number[] => {
    const pages: number[] = [];
    const half = Math.floor(maxVisiblePages / 2);
    
    let start = Math.max(1, currentPage - half);
    let end = Math.min(totalPages, start + maxVisiblePages - 1);
    
    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  const handlePageChange = (page: number) => {
    if (disabled || page < 1 || page > totalPages || page === currentPage) {
      return;
    }
    onPageChange(page);
  };

  const visiblePages = getVisiblePages();
  const showLeftEllipsis = visiblePages[0] > 1;
  const showRightEllipsis = visiblePages[visiblePages.length - 1] < totalPages;

  const buttonClass = (isActive = false, isDisabled = false) => {
    const baseClasses = [
      'relative',
      'inline-flex',
      'items-center',
      'px-4',
      'py-2',
      'text-sm',
      'font-medium',
      'border',
      'focus:z-20',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-blue-500',
      'focus:ring-offset-2',
    ];

    if (isDisabled) {
      baseClasses.push(
        'text-gray-300',
        'bg-white',
        'border-gray-300',
        'cursor-not-allowed'
      );
    } else if (isActive) {
      baseClasses.push(
        'z-10',
        'bg-blue-50',
        'border-blue-500',
        'text-blue-600'
      );
    } else {
      baseClasses.push(
        'bg-white',
        'border-gray-300',
        'text-gray-500',
        'hover:bg-gray-50',
        'cursor-pointer'
      );
    }

    return baseClasses.join(' ');
  };

  const ellipsisClass = 'relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700';

  return (
    <nav className={`flex items-center justify-between ${className}`} aria-label="Pagination">
      <div className="flex-1 flex justify-between sm:hidden">
        {/* Mobile view */}
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={disabled || currentPage <= 1}
          className={buttonClass(false, disabled || currentPage <= 1)}
        >
          이전
        </button>
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={disabled || currentPage >= totalPages}
          className={buttonClass(false, disabled || currentPage >= totalPages)}
        >
          다음
        </button>
      </div>

      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-gray-700">
            <span className="font-medium">{currentPage}</span> /{' '}
            <span className="font-medium">{totalPages}</span> 페이지
          </p>
        </div>
        
        <div>
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            {/* First page */}
            {showFirstLast && (
              <button
                onClick={() => handlePageChange(1)}
                disabled={disabled || currentPage === 1}
                className={`${buttonClass(false, disabled || currentPage === 1)} rounded-l-md`}
                aria-label="첫 페이지"
              >
                첫 페이지
              </button>
            )}

            {/* Previous page */}
            {showPrevNext && (
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={disabled || currentPage <= 1}
                className={buttonClass(false, disabled || currentPage <= 1)}
                aria-label="이전 페이지"
              >
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            )}

            {/* Left ellipsis */}
            {showLeftEllipsis && (
              <span className={ellipsisClass}>...</span>
            )}

            {/* Page numbers */}
            {visiblePages.map((page) => (
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                disabled={disabled}
                className={buttonClass(page === currentPage, disabled)}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page}
              </button>
            ))}

            {/* Right ellipsis */}
            {showRightEllipsis && (
              <span className={ellipsisClass}>...</span>
            )}

            {/* Next page */}
            {showPrevNext && (
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={disabled || currentPage >= totalPages}
                className={buttonClass(false, disabled || currentPage >= totalPages)}
                aria-label="다음 페이지"
              >
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            )}

            {/* Last page */}
            {showFirstLast && (
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={disabled || currentPage === totalPages}
                className={`${buttonClass(false, disabled || currentPage === totalPages)} rounded-r-md`}
                aria-label="마지막 페이지"
              >
                마지막 페이지
              </button>
            )}
          </nav>
        </div>
      </div>
    </nav>
  );
};

export default Pagination;
