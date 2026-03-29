import { useState, useMemo, useCallback } from 'react';

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  pageSizeOptions?: number[];
}

export interface UsePaginationReturn {
  pagination: PaginationState;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  setPageSize: (size: number) => void;
  canGoNext: boolean;
  canGoPrev: boolean;
  pageSizeOptions: number[];
  startIndex: number;
  endIndex: number;
  resetPagination: () => void;
}

export function usePagination(options: UsePaginationOptions = {}): UsePaginationReturn {
  const {
    initialPage = 1,
    initialPageSize = 20,
    pageSizeOptions = [10, 20, 50, 100],
  } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [total, setTotal] = useState(0);

  const totalPages = useMemo(() => {
    if (total === 0) return 0;
    return Math.ceil(total / pageSize);
  }, [total, pageSize]);

  const goToPage = useCallback((newPage: number) => {
    const validPage = Math.max(1, Math.min(newPage, totalPages || 1));
    setPage(validPage);
  }, [totalPages]);

  const nextPage = useCallback(() => {
    if (page < totalPages) {
      setPage(page + 1);
    }
  }, [page, totalPages]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(page - 1);
    }
  }, [page]);

  const setPageSizeWithReset = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const resetPagination = useCallback(() => {
    setPage(1);
    setTotal(0);
  }, []);

  const canGoNext = page < totalPages;
  const canGoPrev = page > 1;

  const startIndex = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, total);

  return {
    pagination: {
      page,
      pageSize,
      total,
      totalPages,
    },
    goToPage,
    nextPage,
    prevPage,
    setPageSize: setPageSizeWithReset,
    canGoNext,
    canGoPrev,
    pageSizeOptions,
    startIndex,
    endIndex,
    resetPagination,
  };
}

export function useCursorPagination<T>(items: T[], pageSize: number = 20) {
  const [cursor, setCursor] = useState(0);

  const paginatedItems = useMemo(() => {
    return items.slice(cursor, cursor + pageSize);
  }, [items, cursor, pageSize]);

  const totalPages = useMemo(() => {
    return Math.ceil(items.length / pageSize);
  }, [items.length, pageSize]);

  const currentPage = useMemo(() => {
    return Math.floor(cursor / pageSize) + 1;
  }, [cursor, pageSize]);

  const canGoNext = cursor + pageSize < items.length;
  const canGoPrev = cursor > 0;

  const nextPage = useCallback(() => {
    if (canGoNext) {
      setCursor(cursor + pageSize);
    }
  }, [cursor, pageSize, canGoNext]);

  const prevPage = useCallback(() => {
    if (canGoPrev) {
      setCursor(Math.max(0, cursor - pageSize));
    }
  }, [cursor, pageSize, canGoPrev]);

  const goToPage = useCallback((page: number) => {
    const newCursor = Math.max(0, (page - 1) * pageSize);
    setCursor(newCursor);
  }, [pageSize]);

  const resetPagination = useCallback(() => {
    setCursor(0);
  }, []);

  return {
    paginatedItems,
    currentPage,
    totalPages,
    canGoNext,
    canGoPrev,
    nextPage,
    prevPage,
    goToPage,
    resetPagination,
    total: items.length,
    startIndex: cursor + 1,
    endIndex: Math.min(cursor + pageSize, items.length),
  };
}
