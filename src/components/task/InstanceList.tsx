import { useMemo } from 'react';
import type { Instance, StatusType } from '@/stores/appStore';
import { useCursorPagination } from '@/hooks/usePagination';
import { SimplePagination } from '@/components/common/Pagination';

interface InstanceListProps {
  instances: Instance[];
  selectedInstanceId: string | null;
  onInstanceClick: (instanceId: string) => void;
  pageSize?: number;
  showPagination?: boolean;
}

const fmtTime = (d: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

const getStatusBadgeClass = (status: StatusType) => {
  if (status === 'RUNNING') return 'bg-[var(--info-bg)] text-cyan-700 border-cyan-500/25';
  if (status === 'PAUSED_HIL') return 'bg-[var(--warning-bg)] text-amber-700 border-amber-500/25';
  if (status === 'SUCCESS') return 'bg-[var(--success-bg)] text-green-700 border-green-500/25';
  if (status === 'FAILED') return 'bg-[var(--danger-bg)] text-red-700 border-red-500/25';
  return 'bg-[var(--info-bg)] text-cyan-700 border-cyan-500/25';
};

export function InstanceList({
  instances,
  selectedInstanceId,
  onInstanceClick,
  pageSize = 10,
  showPagination = true,
}: InstanceListProps) {
  const sortedInstances = useMemo(() => {
    return [...instances].sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }, [instances]);

  const {
    paginatedItems,
    currentPage,
    totalPages,
    nextPage,
    prevPage,
    total,
  } = useCursorPagination(sortedInstances, pageSize);

  const InstanceItem = ({ instance }: { instance: Instance }) => (
    <div
      onClick={() => onInstanceClick(instance.id)}
      className={`
        border rounded-[14px] p-3 flex flex-col gap-2 cursor-pointer transition-all
        ${selectedInstanceId === instance.id
          ? 'border-blue-500/55 shadow-lg shadow-blue-500/10'
          : 'border-[var(--border)] hover:border-gray-300 hover:shadow-lg hover:-translate-y-[-1px]'}
      `}
    >
      <div className="flex items-center justify-between gap-[10px] min-w-0">
        <div className="min-w-0 flex-1">
          <div className="font-bold text-sm text-[var(--text)] truncate">{instance.id}</div>
          <div className="text-xs text-[var(--muted)]">创建 {fmtTime(instance.createdAt)}</div>
        </div>
        <div className={`text-xs font-bold px-2 py-1 rounded-full border ${getStatusBadgeClass(instance.status)}`}>
          {instance.status}
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-[var(--muted)]">
        <div>步数 {instance.steps.length}</div>
        <div>HIL {instance.hilCount}</div>
      </div>
    </div>
  );

  if (instances.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--muted)]">
        <div className="text-sm">暂无实例</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-hidden">
        <div className="flex flex-col gap-[10px]">
          {paginatedItems.map((instance) => (
            <InstanceItem key={instance.id} instance={instance} />
          ))}
        </div>
      </div>

      {showPagination && totalPages > 1 && (
        <div className="mt-[10px] pt-[10px] border-t border-[var(--border)]">
          <SimplePagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={(page) => {
              if (page > currentPage) {
                nextPage();
              } else if (page < currentPage) {
                prevPage();
              }
            }}
          />
          <div className="text-center text-xs text-[var(--muted)] mt-2">
            共 {total} 个实例
          </div>
        </div>
      )}
    </div>
  );
}
