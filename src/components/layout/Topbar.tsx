import { Play, Pause, Square, Plus } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';

const titleMap: Record<string, [string, string]> = {
  tasks: ['任务', '选择任务与实例，进入 Live Console 观察视觉感知过程'],
  live: ['实例 Live Console', '截图推流 + 标注层 + 动作卡 + 日志 + 时间线（mock）'],
  hil: ['HIL 工单', '当命中风险规则或低置信度时触发阻断，人工确认后恢复执行'],
  report: ['报告回放', '每一步的截图/标注/动作/验证结果可回放与导出'],
};

export function Topbar() {
  const { view, mode, setMode, instances, selectedInstanceId } = useAppStore();
  const [title, desc] = titleMap[view] || ['Demo', ''];

  const instance = instances.find((i) => i.id === selectedInstanceId);
  const canStart =
    instance && (instance.status === 'PENDING' || instance.status === 'FAILED' || instance.status === 'SUCCESS');
  const canPause = instance && instance.status === 'RUNNING';
  const canStop = instance && (instance.status === 'RUNNING' || instance.status === 'PAUSED_HIL');

  const modes: { key: typeof mode; label: string }[] = [
    { key: 'auto', label: '自动执行' },
    { key: 'hil', label: '优先HIL' },
    { key: 'safe', label: '保守' },
  ];

  return (
    <header className="h-auto px-[18px] py-[14px] border-b border-[var(--border)] bg-white/75 backdrop-blur-sm flex items-center justify-between gap-3">
      <div className="flex flex-col gap-[2px]">
        <div className="text-sm font-bold text-[var(--text)]">{title}</div>
        <div className="text-xs text-[var(--muted)]">{desc}</div>
      </div>

      <div className="flex items-center gap-[10px] flex-wrap">
        <div className="flex border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          {modes.map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className={`
                px-[10px] py-2 text-xs cursor-pointer border-none
                ${mode === m.key
                  ? 'bg-[var(--primary-50)] text-[var(--primary-600)] font-bold'
                  : 'text-[var(--muted)] bg-transparent'}
              `}
            >
              {m.label}
            </button>
          ))}
        </div>

        <button className="btn border border-[var(--border)] bg-[var(--surface)] text-[var(--text-2)] px-3 py-2 rounded-xl text-sm cursor-pointer hover:bg-[#fbfcfd]">
          <Plus size={16} className="mr-2" />
          新建任务
        </button>

        <button
          disabled={!canStart}
          className="btn primary bg-[var(--primary)] text-white px-3 py-2 rounded-xl text-sm cursor-pointer border border-blue-600/20 hover:bg-[var(--primary-600)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play size={16} className="mr-2" />
          开始推流
        </button>

        <button
          disabled={!canPause}
          className="btn border border-[var(--border)] bg-[var(--surface)] text-[var(--text-2)] px-3 py-2 rounded-xl text-sm cursor-pointer hover:bg-[#fbfcfd] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Pause size={16} className="mr-2" />
          暂停
        </button>

        <button
          disabled={!canStop}
          className="btn danger bg-[var(--danger)] text-white px-3 py-2 rounded-xl text-sm cursor-pointer border border-red-500/25 hover:brightness-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Square size={16} className="mr-2" />
          终止
        </button>
      </div>
    </header>
  );
}
