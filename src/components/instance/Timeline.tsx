import type { Step } from '@/stores/appStore';

interface TimelineProps {
  steps: Step[];
  activeStepNo?: number;
  onStepClick: (stepNo: number) => void;
}

export function Timeline({ steps, activeStepNo, onStepClick }: TimelineProps) {
  return (
    <div className="flex flex-col gap-2 overflow-hidden h-full">
      {steps.length === 0 ? (
        <div className="text-xs text-[var(--muted)] text-center py-4">暂无步骤</div>
      ) : (
        <div className="flex flex-col gap-2">
          {steps.slice(-6).map((step) => (
            <div
              key={step.no}
              onClick={() => onStepClick(step.no)}
              className={`
                border rounded-xl p-[10px] flex gap-[10px] cursor-pointer transition-all
                ${activeStepNo === step.no
                  ? 'border-blue-500/55 bg-blue-50/55'
                  : 'border-[var(--border)] hover:bg-gray-50'}
              `}
            >
              <div className="w-10 h-10 rounded-xl bg-[var(--surface-2)] flex items-center justify-center font-black text-[var(--text)]">
                {step.no}
              </div>
              <div className="flex-1 min-w-0 flex flex-col gap-1">
                <div className="text-xs font-bold truncate">
                  step {step.no} &#183; {step.action.action_type}
                </div>
                <div className="text-xs text-[var(--muted)] truncate">
                  {step.action.expected_result || '-'}
                </div>
              </div>
              <div
                className={`text-xs font-bold px-2 py-1 rounded-full border ${
                  step.verify?.isSuccess
                    ? 'bg-[var(--success-bg)] text-green-700 border-green-500/25'
                    : step.verify?.isDefect
                      ? 'bg-[var(--danger-bg)] text-red-700 border-red-500/25'
                      : 'bg-[var(--info-bg)] text-cyan-700 border-cyan-500/25'
                }`}
              >
                {step.verify?.isSuccess ? 'PASS' : step.verify?.isDefect ? 'FAIL' : 'INFO'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
