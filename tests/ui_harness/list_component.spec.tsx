import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TaskList } from '../../src/components/task/TaskList';
import { InstanceList } from '../../src/components/task/InstanceList';

describe('TaskList Component Tests', () => {
  const mockTasks = [
    {
      id: 'task_1',
      name: 'Task 1',
      url: 'https://example.com/1',
      objective: 'Test objective 1',
      updatedAt: new Date('2024-01-01'),
    },
    {
      id: 'task_2',
      name: 'Task 2',
      url: 'https://example.com/2',
      objective: 'Test objective 2',
      updatedAt: new Date('2024-01-02'),
    },
    {
      id: 'task_3',
      name: 'Task 3',
      url: 'https://example.com/3',
      objective: 'Test objective 3',
      updatedAt: new Date('2024-01-03'),
    },
  ];

  it('should render tasks without pagination when showPagination is false', () => {
    render(
      <TaskList
        tasks={mockTasks}
        selectedTaskId={null}
        onTaskClick={() => {}}
        showPagination={false}
      />
    );

    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.getByText('Task 3')).toBeInTheDocument();
  });

  it('should render tasks with pagination', () => {
    render(
      <TaskList
        tasks={mockTasks}
        selectedTaskId={null}
        onTaskClick={() => {}}
        pageSize={2}
        showPagination={true}
      />
    );

    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.queryByText('Task 3')).not.toBeInTheDocument();
    expect(screen.getByText('第 1/2 页')).toBeInTheDocument();
    expect(screen.getByText('共 3 个任务')).toBeInTheDocument();
  });

  it('should navigate to next page', async () => {
    const user = userEvent.setup();
    render(
      <TaskList
        tasks={mockTasks}
        selectedTaskId={null}
        onTaskClick={() => {}}
        pageSize={2}
        showPagination={true}
      />
    );

    expect(screen.queryByText('Task 3')).not.toBeInTheDocument();

    await user.click(screen.getByText('下一页'));

    expect(screen.getByText('Task 3')).toBeInTheDocument();
    expect(screen.getByText('第 2/2 页')).toBeInTheDocument();
  });

  it('should handle empty task list', () => {
    render(
      <TaskList
        tasks={[]}
        selectedTaskId={null}
        onTaskClick={() => {}}
        showPagination={true}
      />
    );

    expect(screen.getByText('暂无任务')).toBeInTheDocument();
  });

  it('should call onTaskClick when clicking a task', async () => {
    const user = userEvent.setup();
    const onTaskClick = vi.fn();

    render(
      <TaskList
        tasks={mockTasks}
        selectedTaskId={null}
        onTaskClick={onTaskClick}
        showPagination={false}
      />
    );

    await user.click(screen.getByText('Task 1'));

    expect(onTaskClick).toHaveBeenCalledWith('task_1');
  });

  it('should highlight selected task', () => {
    render(
      <TaskList
        tasks={mockTasks}
        selectedTaskId="task_2"
        onTaskClick={() => {}}
        showPagination={false}
      />
    );

    const taskElements = screen.getAllByText(/Task \d/);
    expect(taskElements[1]).toHaveClass(/border-blue-500/);
  });

  it('should sort tasks by updatedAt descending', () => {
    render(
      <TaskList
        tasks={mockTasks}
        selectedTaskId={null}
        onTaskClick={() => {}}
        showPagination={false}
      />
    );

    const taskNames = screen.getAllByText(/Task \d/).map(el => el.textContent);
    expect(taskNames).toEqual(['Task 3', 'Task 2', 'Task 1']);
  });
});

describe('InstanceList Component Tests', () => {
  const mockInstances = [
    {
      id: 'inst_1',
      taskId: 'task_1',
      status: 'RUNNING' as const,
      createdAt: new Date('2024-01-01'),
      startedAt: new Date('2024-01-01'),
      completedAt: null,
      steps: [],
      hilCount: 0,
      defects: [],
    },
    {
      id: 'inst_2',
      taskId: 'task_2',
      status: 'SUCCESS' as const,
      createdAt: new Date('2024-01-02'),
      startedAt: new Date('2024-01-02'),
      completedAt: new Date('2024-01-02'),
      steps: [],
      hilCount: 2,
      defects: [],
    },
    {
      id: 'inst_3',
      taskId: 'task_3',
      status: 'FAILED' as const,
      createdAt: new Date('2024-01-03'),
      startedAt: new Date('2024-01-03'),
      completedAt: new Date('2024-01-03'),
      steps: [],
      hilCount: 5,
      defects: [],
    },
  ];

  it('should render instances without pagination', () => {
    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        showPagination={false}
      />
    );

    expect(screen.getByText('inst_1')).toBeInTheDocument();
    expect(screen.getByText('inst_2')).toBeInTheDocument();
    expect(screen.getByText('inst_3')).toBeInTheDocument();
  });

  it('should render instances with pagination', () => {
    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        pageSize={2}
        showPagination={true}
      />
    );

    expect(screen.getByText('inst_1')).toBeInTheDocument();
    expect(screen.getByText('inst_2')).toBeInTheDocument();
    expect(screen.queryByText('inst_3')).not.toBeInTheDocument();
    expect(screen.getByText('第 1/2 页')).toBeInTheDocument();
    expect(screen.getByText('共 3 个实例')).toBeInTheDocument();
  });

  it('should navigate between pages', async () => {
    const user = userEvent.setup();
    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        pageSize={2}
        showPagination={true}
      />
    );

    await user.click(screen.getByText('下一页'));

    expect(screen.getByText('inst_3')).toBeInTheDocument();
    expect(screen.getByText('第 2/2 页')).toBeInTheDocument();

    await user.click(screen.getByText('上一页'));

    expect(screen.getByText('inst_1')).toBeInTheDocument();
    expect(screen.getByText('第 1/2 页')).toBeInTheDocument();
  });

  it('should handle empty instance list', () => {
    render(
      <InstanceList
        instances={[]}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        showPagination={true}
      />
    );

    expect(screen.getByText('暂无实例')).toBeInTheDocument();
  });

  it('should call onInstanceClick when clicking an instance', async () => {
    const user = userEvent.setup();
    const onInstanceClick = vi.fn();

    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={onInstanceClick}
        showPagination={false}
      />
    );

    await user.click(screen.getByText('inst_1'));

    expect(onInstanceClick).toHaveBeenCalledWith('inst_1');
  });

  it('should display instance status badges', () => {
    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        showPagination={false}
      />
    );

    expect(screen.getAllByText('RUNNING').length).toBeGreaterThan(0);
    expect(screen.getAllByText('SUCCESS').length).toBeGreaterThan(0);
    expect(screen.getAllByText('FAILED').length).toBeGreaterThan(0);
  });

  it('should sort instances by createdAt descending', () => {
    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        showPagination={false}
      />
    );

    const instanceIds = screen.getAllByText(/inst_\d/).map(el => el.textContent);
    expect(instanceIds).toEqual(['inst_3', 'inst_2', 'inst_1']);
  });

  it('should display step count and hil count', () => {
    render(
      <InstanceList
        instances={mockInstances}
        selectedInstanceId={null}
        onInstanceClick={() => {}}
        showPagination={false}
      />
    );

    expect(screen.getByText(/步数 0/)).toBeInTheDocument();
    expect(screen.getByText(/HIL 5/)).toBeInTheDocument();
  });
});
