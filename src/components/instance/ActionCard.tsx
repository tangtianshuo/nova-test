import type { Instance } from '@/stores/appStore';

interface ActionCardProps {
  instance: Instance | null;
}

export function ActionCard({ instance }: ActionCardProps) {
  const currentStep = instance?.steps.find(
    (s) => s.no === instance?.activeStepNo
  ) || instance?.steps[instance.steps.length - 1];

  if (!currentStep) {
    return (
      <div className="border border-[var(--border)] rounded-[var(--radius-sm)] p-3 bg-[var(--surface)]">
        <div className="text-sm font-bold mb-2">当前动作</div>
        <div className="text-xs text-[var(--muted)]">暂无动作数据</div>
      </div>
    );
  }

  const { action } = currentStep;

  return (
    <div className="border border-[var(--border)] rounded-[var(--radius-sm)] p-3 bg-[var(--surface)] overflow-hidden">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-bold">当前动作</div>
        <div className="text-xs font-mono bg-[var(--primary-50)] text-[var(--primary-600)] px-2 py-1 rounded-full">
          {action.action_type}
        </div>
      </div>
      <div className="space-y-2">
        <div>
          <div className="text-xs text-[var(--muted)] mb-1">Thought</div>
          <div className="text-xs bg-[var(--surface-2)] p-2 rounded-lg font-mono">
            {action.thought || '-'}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-xs text-[var(--muted)]">置信度</div>
            <div className="text-sm font-bold">
              {action.confidence ? `${(action.confidence * 100).toFixed(1)}%` : '-'}
            </div>
          </div>
          <div>
            <div className="text-xs text-[var(--muted)]">预期结果</div>
            <div className="text-xs truncate">{action.expected_result || '-'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
