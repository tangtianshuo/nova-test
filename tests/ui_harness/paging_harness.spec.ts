import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePagination, useCursorPagination } from '../../src/hooks/usePagination';

describe('FE-07-07: UI Paging Harness', () => {
  describe('usePagination Hook', () => {
    it('should paginate list items', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      expect(result.current.pagination.page).toBe(1);
      expect(result.current.pagination.pageSize).toBe(10);
      expect(result.current.pagination.total).toBe(0);
    });

    it('should navigate between pages', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      act(() => {
        result.current.setTotal(100);
      });

      expect(result.current.pagination.totalPages).toBe(10);
      expect(result.current.canGoNext).toBe(true);
      expect(result.current.canGoPrev).toBe(false);

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.pagination.page).toBe(2);
      expect(result.current.canGoNext).toBe(true);
      expect(result.current.canGoPrev).toBe(true);

      act(() => {
        result.current.prevPage();
      });

      expect(result.current.pagination.page).toBe(1);
    });

    it('should display page info correctly', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      act(() => {
        result.current.setTotal(95);
      });

      expect(result.current.pagination.totalPages).toBe(10);
      expect(result.current.startIndex).toBe(1);
      expect(result.current.endIndex).toBe(10);

      act(() => {
        result.current.goToPage(5);
      });

      expect(result.current.pagination.page).toBe(5);
      expect(result.current.startIndex).toBe(41);
      expect(result.current.endIndex).toBe(50);
    });

    it('should handle empty list', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      expect(result.current.pagination.total).toBe(0);
      expect(result.current.pagination.totalPages).toBe(0);
      expect(result.current.canGoNext).toBe(false);
      expect(result.current.canGoPrev).toBe(false);
    });

    it('should change page size', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      act(() => {
        result.current.setTotal(100);
      });

      expect(result.current.pagination.totalPages).toBe(10);

      act(() => {
        result.current.setPageSize(20);
      });

      expect(result.current.pagination.pageSize).toBe(20);
      expect(result.current.pagination.totalPages).toBe(5);
      expect(result.current.pagination.page).toBe(1);
    });

    it('should not go beyond first page', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      act(() => {
        result.current.setTotal(100);
      });

      act(() => {
        result.current.prevPage();
      });

      expect(result.current.pagination.page).toBe(1);
    });

    it('should not go beyond last page', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      act(() => {
        result.current.setTotal(100);
      });

      act(() => {
        result.current.goToPage(10);
      });

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.pagination.page).toBe(10);
    });

    it('should reset pagination correctly', () => {
      const { result } = renderHook(() => usePagination({ initialPage: 1, initialPageSize: 10 }));

      act(() => {
        result.current.setTotal(100);
        result.current.goToPage(5);
      });

      expect(result.current.pagination.page).toBe(5);

      act(() => {
        result.current.resetPagination();
      });

      expect(result.current.pagination.page).toBe(1);
      expect(result.current.pagination.total).toBe(0);
    });
  });

  describe('useCursorPagination Hook', () => {
    it('should paginate items using cursor', () => {
      const items = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `Item ${i}` }));
      const { result } = renderHook(() => useCursorPagination(items, 20));

      expect(result.current.paginatedItems.length).toBe(20);
      expect(result.current.currentPage).toBe(1);
      expect(result.current.totalPages).toBe(5);
      expect(result.current.total).toBe(100);
    });

    it('should navigate between pages with cursor', () => {
      const items = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `Item ${i}` }));
      const { result } = renderHook(() => useCursorPagination(items, 20));

      expect(result.current.startIndex).toBe(1);
      expect(result.current.endIndex).toBe(20);

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.currentPage).toBe(2);
      expect(result.current.startIndex).toBe(21);
      expect(result.current.endIndex).toBe(40);

      act(() => {
        result.current.prevPage();
      });

      expect(result.current.currentPage).toBe(1);
    });

    it('should go to specific page', () => {
      const items = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `Item ${i}` }));
      const { result } = renderHook(() => useCursorPagination(items, 20));

      act(() => {
        result.current.goToPage(3);
      });

      expect(result.current.currentPage).toBe(3);
      expect(result.current.startIndex).toBe(41);
      expect(result.current.endIndex).toBe(60);
    });

    it('should handle empty list', () => {
      const items: Array<{ id: number; name: string }> = [];
      const { result } = renderHook(() => useCursorPagination(items, 20));

      expect(result.current.paginatedItems.length).toBe(0);
      expect(result.current.currentPage).toBe(1);
      expect(result.current.totalPages).toBe(0);
    });

    it('should control navigation boundaries', () => {
      const items = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `Item ${i}` }));
      const { result } = renderHook(() => useCursorPagination(items, 20));

      expect(result.current.canGoPrev).toBe(false);
      expect(result.current.canGoNext).toBe(true);

      act(() => {
        result.current.goToPage(5);
      });

      expect(result.current.canGoPrev).toBe(true);
      expect(result.current.canGoNext).toBe(false);
    });
  });
});

describe('UI Paging Performance Tests', () => {
  it('should handle large dataset pagination efficiently', () => {
    const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
      id: i,
      name: `Task ${i}`,
      updatedAt: new Date(Date.now() - i * 1000),
    }));

    const { result } = renderHook(() => useCursorPagination(largeDataset, 50));

    const startTime = performance.now();
    for (let i = 0; i < 200; i++) {
      act(() => {
        result.current.goToPage((i % 200) + 1);
      });
    }
    const endTime = performance.now();

    const duration = endTime - startTime;
    expect(duration).toBeLessThan(1000);
  });

  it('should calculate indices correctly for different page sizes', () => {
    const items = Array.from({ length: 150 }, (_, i) => ({ id: i, name: `Item ${i}` }));

    const { result: result1 } = renderHook(() => useCursorPagination(items, 10));
    expect(result1.current.totalPages).toBe(15);

    const { result: result2 } = renderHook(() => useCursorPagination(items, 20));
    expect(result2.current.totalPages).toBe(8);

    const { result: result3 } = renderHook(() => useCursorPagination(items, 50));
    expect(result3.current.totalPages).toBe(3);
  });

  it('should memoize sorted items correctly', () => {
    const items = Array.from({ length: 1000 }, (_, i) => ({
      id: i,
      name: `Task ${i}`,
      updatedAt: new Date(Date.now() - i * 1000),
    }));

    const { result, rerender } = renderHook(({ data }) => useCursorPagination(data, 20), {
      props: { data: items },
    });

    const firstPaginatedItems = result.current.paginatedItems;
    rerender({ data: items });
    const secondPaginatedItems = result.current.paginatedItems;

    expect(firstPaginatedItems).toEqual(secondPaginatedItems);
  });
});
