import { useAppStore, type Instance, type Task } from '@/stores/appStore';
import { ScreenshotViewer } from './ScreenshotViewer';
import { ActionCard } from './ActionCard';
import { LogPanel } from './LogPanel';
import { Timeline } from './Timeline';
import { MetricsSummary } from './MetricsSummary';

interface LiveConsoleProps {
  instance: Instance | undefined;
  task?: Task | undefined;
}

export function LiveConsole({ instance }: LiveConsoleProps) {
  const { logs, ui } = useAppStore();

  if (!instance) {
    return (
      <div className="h-full flex items-center justify-center text-[var(--muted)]">
        选择实例后开始推流
      </div>
    );
  }

  return (
    <div className="h-full grid grid-rows-[auto_1fr] min-h-0">
      <MetricsSummary instance={instance} />
      
      <div className="grid grid-cols-[1.35fr_0.65fr] gap-[14px] p-[14px] min-w-0 overflow-hidden">
        <ScreenshotViewer instance={instance} />
        
        <div className="grid grid-rows-[auto_1fr] gap-3 min-w-0 min-h-0">
          <ActionCard instance={instance} />
          
          <div className="grid grid-rows-[1fr_1.2fr] gap-3 min-h-0">
            <LogPanel logs={logs} page={ui.logPage} />
            <Timeline steps={instance.steps} activeStepNo={instance.activeStepNo} onStepClick={() => {}} />
          </div>
        </div>
      </div>
    </div>
  );
}
