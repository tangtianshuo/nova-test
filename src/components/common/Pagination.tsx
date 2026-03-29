import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { clsx } from 'clsx';
import type { PaginationState } from '@/hooks/usePagination';

interface PaginationProps {
  pagination: PaginationState;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  showPageSizeSelector?: boolean;
  className?: string;
}

export function Pagination({
  pagination,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50, 100],
  showPageSizeSelector = true,
  className,
}: PaginationProps) {
  const { page, pageSize, total, totalPages } = pagination;

  if (total === 0) {
    return null;
  }

  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, total);

  const renderPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisiblePages = 7;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);

      if (page > 3) {
        pages.push('ellipsis');
      }

      const startPage = Math.max(2, page - 1);
      const endPage = Math.min(totalPages - 1, page + 1);

      for (let i = startPage; i <= endPage; i++) {
        if (!pages.includes(i)) {
          pages.push(i);
        }
      }

      if (page < totalPages - 2) {
        pages.push('ellipsis');
      }

      if (!pages.includes(totalPages)) {
        pages.push(totalPages);
      }
    }

    return pages;
  };

  const buttonBaseClass = 'px-3 py-1.5 text-sm font-medium rounded-md transition-colors';
  const disabledClass = 'opacity-50 cursor-not-allowed pointer-events-none';

  return (
    <div className={clsx('flex items-center justify-between gap-4', className)}>
      <div className="flex items-center gap-3">
        {showPageSizeSelector && onPageSizeChange && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--muted)]">每页</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="px-2 py-1 text-sm border border-[var(--border)] rounded-md bg-[var(--bg)] text-[var(--text)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size} 条
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="text-xs text-[var(--muted)]">
          显示 {startIndex}-{endIndex}，共 {total} 条
        </div>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(1)}
          disabled={page === 1}
          className={clsx(buttonBaseClass, 'hover:bg-[var(--hover)]', page === 1 && disabledClass)}
          aria-label="首页"
        >
          <ChevronsLeft className="w-4 h-4" />
        </button>

        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          className={clsx(buttonBaseClass, 'hover:bg-[var(--hover)]', page === 1 && disabledClass)}
          aria-label="上一页"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-1">
          {renderPageNumbers().map((pageNum, idx) =>
            pageNum === 'ellipsis' ? (
              <span key={`ellipsis-${idx}`} className="px-2 py-1.5 text-sm text-[var(--muted)]">
                ...
              </span>
            ) : (
              <button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
                className={clsx(
                  buttonBaseClass,
                  'min-w-[32px]',
                  page === pageNum
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'hover:bg-[var(--hover)]'
                )}
              >
                {pageNum}
              </button>
            )
          )}
        </div>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === totalPages}
          className={clsx(buttonBaseClass, 'hover:bg-[var(--hover)]', page === totalPages && disabledClass)}
          aria-label="下一页"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        <button
          onClick={() => onPageChange(totalPages)}
          disabled={page === totalPages}
          className={clsx(buttonBaseClass, 'hover:bg-[var(--hover)]', page === totalPages && disabledClass)}
          aria-label="末页"
        >
          <ChevronsRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

interface SimplePaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function SimplePagination({
  currentPage,
  totalPages,
  onPageChange,
  className,
}: SimplePaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  const buttonBaseClass = 'px-3 py-1 text-xs font-medium rounded transition-colors';
  const disabledClass = 'opacity-40 cursor-not-allowed pointer-events-none';

  return (
    <div className={clsx('flex items-center justify-center gap-2', className)}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={clsx(buttonBaseClass, 'hover:bg-[var(--hover)]', currentPage === 1 && disabledClass)}
      >
        上一页
      </button>

      <span className="text-xs text-[var(--muted)] px-2">
        第 {currentPage}/{totalPages} 页
      </span>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={clsx(buttonBaseClass, 'hover:bg-[var(--hover)]', currentPage === totalPages && disabledClass)}
      >
        下一页
      </button>
    </div>
  );
}
