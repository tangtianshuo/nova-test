import type { Instance } from '@/stores/appStore';

interface MetricsSummaryProps {
  instance: Instance | null;
}

export function MetricsSummary({ instance }: MetricsSummaryProps) {
  const status = instance?.status || 'PENDING';

  const getStatusBadgeClass = (s: string) => {
    if (s === 'RUNNING') return 'bg-[var(--info-bg)] text-cyan-700 border-cyan-500/25';
    if (s === 'PAUSED_HIL') return 'bg-[var(--warning-bg)] text-amber-700 border-amber-500/25';
    if (s === 'SUCCESS') return 'bg-[var(--success-bg)] text-green-700 border-green-500/25';
    if (s === 'FAILED') return 'bg-[var(--danger-bg)] text-red-700 border-red-500/25';
    return 'bg-gray-100 text-gray-500';
  };

  return (
    <div className="grid grid-cols-4 gap-[10px] p-[10px]">
      <div className="border border-[var(--border)] rounded-[14px] p-[10px] flex flex-col gap-1 bg-gradient-to-b from-white/95 to-[rgba(247,248,250,0.7)]">
        <div className={`text-xs font-bold px-2 py-1 rounded-full border w-fit ${getStatusBadgeClass(status)}`}>
          {status}
        </div>
        <div className="text-xs text-[var(--muted)]">状态</div>
      </div>
      <div className="border border-[var(--border)] rounded-[14px] p-[10px] flex flex-col gap-1 bg-gradient-to-b from-white/95 to-[rgba(247,248,250,0.7)]">
        <div className="text-base font-extrabold text-[var(--text)] tracking-wide">{instance?.steps.length ?? 0}</div>
        <div className="text-xs text-[var(--muted)]">步数</div>
      </div>
      <div className="border border-[var(--border)] rounded-[14px] p-[10px] flex flex-col gap-1 bg-gradient-to-b from-white/95 to-[rgba(247,248,250,0.7)]">
        <div className="text-base font-extrabold text-[var(--text)] tracking-wide">{instance?.hilCount ?? 0}</div>
        <div className="text-xs text-[var(--muted)]">HIL</div>
      </div>
      <div className="border border-[var(--border)] rounded-[14px] p-[10px] flex flex-col gap-1 bg-gradient-to-b from-white/95 to-[rgba(247,248,250,0.7)]">
        <div className="text-base font-extrabold text-[var(--text)] tracking-wide">{instance?.defects.length ?? 0}</div>
        <div className="text-xs text-[var(--muted)]">缺陷</div>
      </div>
    </div>
  );
}
