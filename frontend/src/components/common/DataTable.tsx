import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

export interface Column<T = any> {
  key: string;
  label: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

export interface DataTableProps<T = any> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: string;
  emptyMessage?: string;
  className?: string;
  striped?: boolean;
  hoverable?: boolean;
  bordered?: boolean;
  compact?: boolean;
  onRowClick?: (row: T, index: number) => void;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
}

export function DataTable<T = any>({
  columns,
  data,
  loading = false,
  error,
  emptyMessage = '데이터가 없습니다.',
  className = '',
  striped = false,
  hoverable = true,
  bordered = true,
  compact = false,
  onRowClick,
  onSort,
  sortKey,
  sortDirection
}: DataTableProps<T>) {
  const handleSort = (key: string) => {
    if (!onSort) return;
    
    const direction = sortKey === key && sortDirection === 'asc' ? 'desc' : 'asc';
    onSort(key, direction);
  };

  const getSortIcon = (key: string) => {
    if (sortKey !== key) {
      return (
        <svg className="w-4 h-4 ml-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }
    
    return sortDirection === 'asc' ? (
      <svg className="w-4 h-4 ml-1 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 ml-1 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  const getColumnValue = (row: T, key: string) => {
    return key.split('.').reduce((obj, k) => obj?.[k], row as any);
  };

  const tableClasses = `
    min-w-full 
    ${bordered ? 'divide-y divide-gray-200 border border-gray-200 rounded-lg' : 'divide-y divide-gray-200'}
    ${compact ? 'text-sm' : ''}
    ${className}
  `.trim();

  const headerClasses = `
    ${compact ? 'px-3 py-2' : 'px-6 py-3'}
    text-left text-xs font-medium text-gray-500 uppercase tracking-wider
    bg-gray-50
  `.trim();

  const cellClasses = `
    ${compact ? 'px-3 py-2' : 'px-6 py-4'}
    whitespace-nowrap text-sm
  `.trim();

  if (error) {
    return <ErrorMessage type="error" message={error} />;
  }

  return (
    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
      <table className={tableClasses}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`
                  ${headerClasses}
                  ${column.width ? `w-${column.width}` : ''}
                  ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                  ${column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''}
                  ${column.className || ''}
                `}
                style={column.width ? { width: column.width } : undefined}
                onClick={() => column.sortable && handleSort(column.key)}
              >
                <div className="flex items-center">
                  <span>{column.label}</span>
                  {column.sortable && getSortIcon(column.key)}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        
        <tbody className={`bg-white ${striped ? 'divide-y divide-gray-200' : 'divide-y divide-gray-200'}`}>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-8">
                <LoadingSpinner text="데이터를 불러오는 중..." />
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-8 text-gray-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={`
                  ${striped && rowIndex % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
                  ${hoverable ? 'hover:bg-gray-50' : ''}
                  ${onRowClick ? 'cursor-pointer' : ''}
                `}
                onClick={() => onRowClick?.(row, rowIndex)}
              >
                {columns.map((column) => {
                  const value = getColumnValue(row, column.key);
                  const displayValue = column.render 
                    ? column.render(value, row, rowIndex)
                    : value;

                  return (
                    <td
                      key={column.key}
                      className={`
                        ${cellClasses}
                        ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                        text-gray-900
                      `}
                    >
                      {displayValue}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
