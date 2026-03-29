import { useMemo } from 'react';
import { useAppStore } from '@/stores/appStore';
import { useCursorPagination } from '@/hooks/usePagination';
import { SimplePagination } from '@/components/common/Pagination';

interface TaskListProps {
  tasks: { id: string; name: string; url: string; objective: string; updatedAt: Date }[];
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  pageSize?: number;
  showPagination?: boolean;
}

const fmtTime = (d: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

const escapeHtml = (s: string) => {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

export function TaskList({
  tasks,
  selectedTaskId,
  onTaskClick,
  pageSize = 10,
  showPagination = true,
}: TaskListProps) {
  useAppStore();

  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }, [tasks]);

  const {
    paginatedItems,
    currentPage,
    totalPages,
    canGoNext,
    canGoPrev,
    nextPage,
    prevPage,
    total,
  } = useCursorPagination(sortedTasks, pageSize);

  const TaskItem = ({ task }: { task: typeof sortedTasks[0] }) => (
    <div
      onClick={() => onTaskClick(task.id)}
      className={`
        border rounded-[14px] p-3 flex flex-col gap-2 cursor-pointer transition-all
        ${selectedTaskId === task.id
          ? 'border-blue-500/55 shadow-lg shadow-blue-500/10'
          : 'border-[var(--border)] hover:border-gray-300 hover:shadow-lg hover:-translate-y-[-1px]'}
      `}
    >
      <div className="flex items-center justify-between gap-[10px] min-w-0">
        <div className="min-w-0 flex-1">
          <div className="font-bold text-sm text-[var(--text)] truncate">{escapeHtml(task.name)}</div>
          <div className="text-xs text-[var(--muted)] truncate" title={task.url}>{escapeHtml(task.url)}</div>
        </div>
        <div className="text-xs font-bold px-[10px] py-1 rounded-full bg-[var(--info-bg)] text-cyan-700 border border-cyan-500/25">TASK</div>
      </div>
      <div className="flex items-center justify-between text-xs text-[var(--muted)]">
        <div>Objective</div>
        <div>更新 {fmtTime(task.updatedAt)}</div>
      </div>
      <div className="text-xs text-[var(--muted)] truncate">{escapeHtml(task.objective)}</div>
    </div>
  );

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--muted)]">
        <div className="text-sm">暂无任务</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-hidden">
        <div className="flex flex-col gap-[10px]">
          {paginatedItems.map((task) => (
            <TaskItem key={task.id} task={task} />
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
            共 {total} 个任务
          </div>
        </div>
      )}
    </div>
  );
}
