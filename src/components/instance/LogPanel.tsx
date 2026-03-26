import type { LogEntry } from '@/stores/appStore';

interface LogPanelProps {
  logs: LogEntry[];
  page: number;
}

export function LogPanel({ logs }: LogPanelProps) {
  const getLevelClass = (lvl: LogEntry['lvl']) => {
    if (lvl === 'ERROR') return 'text-red-600 bg-red-50';
    if (lvl === 'WARN') return 'text-amber-600 bg-amber-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="border border-[var(--border)] rounded-[var(--radius-sm)] bg-[var(--surface)] flex flex-col overflow-hidden h-full">
      <div className="px-3 py-2 border-b border-[var(--border)] flex items-center justify-between">
        <div className="text-sm font-bold">执行日志</div>
        <div className="text-xs text-[var(--muted)]">{logs.length} 条</div>
      </div>
      <div className="flex-1 overflow-auto p-2 text-xs font-mono">
        {logs.length === 0 ? (
          <div className="text-[var(--muted)] text-center py-4">暂无日志</div>
        ) : (
          logs.slice(-20).map((log, idx) => (
            <div key={idx} className={`px-2 py-1 rounded mb-1 ${getLevelClass(log.lvl)}`}>
              <span className="font-bold mr-2">[{log.lvl}]</span>
              <span>{log.msg}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
