import { LayoutDashboard, AlertCircle, FileText } from 'lucide-react';
import { useAppStore, type ViewType } from '@/stores/appStore';

const navItems: { key: ViewType; label: string; icon: typeof LayoutDashboard }[] = [
  { key: 'tasks', label: '任务', icon: LayoutDashboard },
  { key: 'live', label: '实例 Live Console', icon: LayoutDashboard },
  { key: 'hil', label: 'HIL 工单', icon: AlertCircle },
  { key: 'report', label: '报告回放', icon: FileText },
];

export function Sidebar() {
  const { view, setView, tasks, instances, hilTicket, report } = useAppStore();

  const liveCount = instances.filter(
    (x) => x.status === 'RUNNING' || x.status === 'PAUSED_HIL'
  ).length;
  const hilCount = hilTicket ? 1 : 0;
  const reportCount = report ? 1 : 1;

  const getPillCount = (key: ViewType) => {
    if (key === 'tasks') return tasks.length;
    if (key === 'live') return liveCount;
    if (key === 'hil') return hilCount;
    if (key === 'report') return reportCount;
    return 0;
  };

  return (
    <aside className="w-[260px] h-full bg-[#0b1220] text-gray-200 p-[18px_14px] flex flex-col gap-[14px] border-r border-white/[0.06]">
      <div className="p-[10px] rounded-xl bg-white/[0.04]">
        <div className="font-bold text-sm tracking-wide">黑盒自动化测试工具</div>
        <div className="mt-1 text-xs text-gray-300/90">静态Demo · SaaS + AaaS · SDD</div>
      </div>

      <nav className="flex flex-col gap-[6px]">
        {navItems.map((item) => {
          const isActive = view === item.key;
          const count = getPillCount(item.key);
          const isHilWarn = item.key === 'hil' && count > 0;

          return (
            <button
              key={item.key}
              onClick={() => setView(item.key)}
              className={`
                w-full text-left border rounded-xl px-[10px] py-[10px] cursor-pointer text-sm
                flex items-center justify-between transition-all
                ${isActive
                  ? 'bg-blue-500/20 border-blue-500/40 text-white'
                  : 'border-transparent hover:bg-white/5'}
              `}
            >
              <span>{item.label}</span>
              <span
                className={`
                  text-xs px-2 py-[2px] rounded-full
                  ${isHilWarn ? 'bg-amber-500/20 text-amber-200' : 'bg-white/10 text-gray-300'}
                `}
              >
                {count}
              </span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto p-[10px] rounded-xl bg-white/[0.04] text-gray-300 text-xs leading-relaxed">
        <div>Mock 推流： 截图、 标注层、 Thought、 日志、 时间线</div>
        <div>HIL: 批准 / 修改 / 拒绝</div>
      </div>
    </aside>
  );
}
