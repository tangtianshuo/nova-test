import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Pagination, SimplePagination } from '../../src/components/common/Pagination';

describe('Pagination Component Tests', () => {
  it('should render pagination controls', () => {
    render(
      <Pagination
        pagination={{ page: 1, pageSize: 10, total: 100, totalPages: 10 }}
        onPageChange={() => {}}
        showPageSizeSelector={false}
      />
    );

    expect(screen.getByLabelText('首页')).toBeInTheDocument();
    expect(screen.getByLabelText('上一页')).toBeInTheDocument();
    expect(screen.getByLabelText('下一页')).toBeInTheDocument();
    expect(screen.getByLabelText('末页')).toBeInTheDocument();
    expect(screen.getByText(/1/)).toBeInTheDocument();
    expect(screen.getByText(/共 100 条/)).toBeInTheDocument();
  });

  it('should hide pagination when total is 0', () => {
    const { container } = render(
      <Pagination
        pagination={{ page: 1, pageSize: 10, total: 0, totalPages: 0 }}
        onPageChange={() => {}}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should call onPageChange when clicking next', async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    render(
      <Pagination
        pagination={{ page: 1, pageSize: 10, total: 100, totalPages: 10 }}
        onPageChange={onPageChange}
        showPageSizeSelector={false}
      />
    );

    await user.click(screen.getByLabelText('下一页'));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('should call onPageChange when clicking prev', async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    render(
      <Pagination
        pagination={{ page: 2, pageSize: 10, total: 100, totalPages: 10 }}
        onPageChange={onPageChange}
        showPageSizeSelector={false}
      />
    );

    await user.click(screen.getByLabelText('上一页'));

    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('should call onPageSizeChange when selecting page size', async () => {
    const user = userEvent.setup();
    const onPageSizeChange = vi.fn();
    const onPageChange = vi.fn();

    render(
      <Pagination
        pagination={{ page: 1, pageSize: 10, total: 100, totalPages: 10 }}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        showPageSizeSelector={true}
      />
    );

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '20');

    expect(onPageSizeChange).toHaveBeenCalledWith(20);
  });

  it('should disable first and prev buttons on first page', () => {
    render(
      <Pagination
        pagination={{ page: 1, pageSize: 10, total: 100, totalPages: 10 }}
        onPageChange={() => {}}
        showPageSizeSelector={false}
      />
    );

    expect(screen.getByLabelText('首页')).toBeDisabled();
    expect(screen.getByLabelText('上一页')).toBeDisabled();
  });

  it('should disable last and next buttons on last page', () => {
    render(
      <Pagination
        pagination={{ page: 10, pageSize: 10, total: 100, totalPages: 10 }}
        onPageChange={() => {}}
        showPageSizeSelector={false}
      />
    );

    expect(screen.getByLabelText('下一页')).toBeDisabled();
    expect(screen.getByLabelText('末页')).toBeDisabled();
  });
});

describe('SimplePagination Component Tests', () => {
  it('should render simple pagination controls', () => {
    render(
      <SimplePagination
        currentPage={1}
        totalPages={5}
        onPageChange={() => {}}
      />
    );

    expect(screen.getByText('上一页')).toBeInTheDocument();
    expect(screen.getByText('下一页')).toBeInTheDocument();
    expect(screen.getByText(/第 1\/5 页/)).toBeInTheDocument();
  });

  it('should hide when totalPages is 1', () => {
    const { container } = render(
      <SimplePagination
        currentPage={1}
        totalPages={1}
        onPageChange={() => {}}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should call onPageChange when clicking buttons', async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    render(
      <SimplePagination
        currentPage={2}
        totalPages={5}
        onPageChange={onPageChange}
      />
    );

    await user.click(screen.getByText('上一页'));
    expect(onPageChange).toHaveBeenCalledWith(1);

    await user.click(screen.getByText('下一页'));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it('should disable prev button on first page', () => {
    render(
      <SimplePagination
        currentPage={1}
        totalPages={5}
        onPageChange={() => {}}
      />
    );

    expect(screen.getByText('上一页')).toBeDisabled();
    expect(screen.getByText('下一页')).not.toBeDisabled();
  });

  it('should disable next button on last page', () => {
    render(
      <SimplePagination
        currentPage={5}
        totalPages={5}
        onPageChange={() => {}}
      />
    );

    expect(screen.getByText('上一页')).not.toBeDisabled();
    expect(screen.getByText('下一页')).toBeDisabled();
  });
});
