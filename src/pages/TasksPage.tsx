import { useState } from 'react';
import { useAppStore, currentTask, currentInstance, mkInstance } from '@/stores/appStore';
import { TaskList } from '@/components/task/TaskList';
import { InstanceList } from '@/components/task/InstanceList';
import { LiveConsole } from '@/components/instance/LiveConsole';

export function TasksPage() {
  const { tasks, selectedTaskId, selectedInstanceId, selectTask, selectInstance, addInstance, instances } = useAppStore();
  const [leftMode, setLeftMode] = useState<'tasks' | 'instances'>('tasks');

  const task = currentTask(useAppStore.getState());
  const instance = currentInstance(useAppStore.getState());

  const handleTaskClick = (taskId: string) => {
    selectTask(taskId);
    const existingInstance = instances.find((x) => x.taskId === taskId);
    if (!existingInstance) {
      const newInstance = mkInstance(taskId);
      addInstance(newInstance);
      selectInstance(newInstance.id);
    } else {
      selectInstance(existingInstance.id);
    }
  };

  const handleInstanceClick = (instanceId: string) => {
    selectInstance(instanceId);
  };

  return (
    <div className="h-full grid grid-cols-[420px_1fr] gap-[14px] min-w-0">
      <section className="panel bg-[var(--surface)] border border-[var(--border)] rounded-[var(--radius)] shadow-[var(--shadow)] overflow-hidden flex flex-col min-w-0">
        <div className="px-[14px] py-[12px] border-b border-[var(--border)] flex items-center justify-between gap-[10px]">
          <div>
            <div className="font-bold text-sm">任务列表</div>
            <div className="text-xs text-[var(--muted)]">Workspace: Nova · {tasks.length} 个任务</div>
          </div>
          <div className="flex border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
            <button
              onClick={() => setLeftMode('tasks')}
              className={`px-[10px] py-2 text-xs cursor-pointer ${leftMode === 'tasks' ? 'bg-[var(--primary-50)] text-[var(--primary-600)] font-bold' : 'text-[var(--muted)]'}`}
            >
              任务
            </button>
            <button
              onClick={() => setLeftMode('instances')}
              className={`px-[10px] py-2 text-xs cursor-pointer ${leftMode === 'instances' ? 'bg-[var(--primary-50)] text-[var(--primary-600)] font-bold' : 'text-[var(--muted)]'}`}
            >
              实例
            </button>
          </div>
        </div>
        <div className="flex-1 p-[12px_14px] overflow-hidden flex flex-col gap-[10px]">
          {leftMode === 'tasks' ? (
            <TaskList
              tasks={tasks}
              selectedTaskId={selectedTaskId}
              onTaskClick={handleTaskClick}
            />
          ) : (
            <InstanceList
              instances={instances.filter((x) => (selectedTaskId ? x.taskId === selectedTaskId : true))}
              selectedInstanceId={selectedInstanceId}
              onInstanceClick={handleInstanceClick}
            />
          )}
        </div>
      </section>

      <section className="panel bg-[var(--surface)] border border-[var(--border)] rounded-[var(--radius)] shadow-[var(--shadow)] overflow-hidden flex flex-col min-w-0">
        <LiveConsole instance={instance} task={task} />
      </section>
    </div>
  );
}
