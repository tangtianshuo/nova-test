import { create } from 'zustand';

export type ViewType = 'tasks' | 'live' | 'hil' | 'report';
export type ModeType = 'auto' | 'hil' | 'safe';
export type StatusType = 'PENDING' | 'RUNNING' | 'PAUSED_HIL' | 'SUCCESS' | 'FAILED';

export interface Task {
  id: string;
  name: string;
  url: string;
  objective: string;
  constraints: {
    max_steps: number;
    forbidden_domains: string[];
  };
  updatedAt: Date;
}

export interface Step {
  no: number;
  node: string;
  screenshot: string;
  overlay: {
    baseW: number;
    baseH: number;
    boxes: Array<{ x: number; y: number; w: number; h: number }>;
    point?: { x: number; y: number };
  } | null;
  action: {
    thought: string;
    action_type: string;
    target: Record<string, unknown>;
    params: Record<string, unknown>;
    confidence: number;
    expected_result: string;
  };
  verify: {
    isSuccess: boolean;
    isDefect: boolean;
    msg: string;
  } | null;
}

export interface Instance {
  id: string;
  taskId: string;
  status: StatusType;
  createdAt: Date;
  startedAt: Date | null;
  completedAt: Date | null;
  steps: Step[];
  hilCount: number;
  defects: Array<{ stepNo: number; title: string; detail: string }>;
  activeStepNo?: number;
}

export interface HilTicket {
  ticketId: string;
  status: 'WAITING' | 'APPROVED' | 'REJECTED' | 'MODIFIED' | 'EXPIRED';
  instanceId: string;
  reason: string;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  plannedAction: Record<string, unknown>;
  screenshot: string;
  overlay: Step['overlay'];
}

export interface LogEntry {
  lvl: 'INFO' | 'WARN' | 'ERROR';
  msg: string;
}

export interface Report {
  reportId: string;
  instanceId: string;
  verdict: 'SUCCESS' | 'FAILED' | 'PARTIAL' | 'DRAFT';
  hilCount: number;
  defects: Array<{ stepNo: number; title: string; detail: string }>;
  steps: Step[];
  activeStepNo?: number;
}

interface AppState {
  view: ViewType;
  mode: ModeType;
  wsConnected: boolean;
  tasks: Task[];
  instances: Instance[];
  selectedTaskId: string | null;
  selectedInstanceId: string | null;
  hilTicket: HilTicket | null;
  hilDrawerOpen: boolean;
  report: Report | null;
  logs: LogEntry[];
  ui: {
    leftPage: number;
    logPage: number;
    tlPage: number;
    defPage: number;
    repTlPage: number;
  };
  running: {
    timer: ReturnType<typeof setInterval> | null;
  };

  setView: (view: ViewType) => void;
  setMode: (mode: ModeType) => void;
  setWsConnected: (connected: boolean) => void;
  selectTask: (taskId: string) => void;
  selectInstance: (instanceId: string) => void;
  addTask: (task: Task) => void;
  addInstance: (instance: Instance) => void;
  updateInstance: (instanceId: string, updates: Partial<Instance>) => void;
  setHilTicket: (ticket: HilTicket | null) => void;
  setHilDrawerOpen: (open: boolean) => void;
  setReport: (report: Report | null) => void;
  pushLog: (lvl: LogEntry['lvl'], msg: string) => void;
  clearLogs: () => void;
  setUiPage: (key: keyof AppState['ui'], page: number) => void;
  setRunningTimer: (timer: ReturnType<typeof setInterval> | null) => void;
}

const uid = () => Math.random().toString(16).slice(2, 10);

export const useAppStore = create<AppState>((set) => ({
  view: 'tasks',
  mode: 'auto',
  wsConnected: false,
  tasks: [
    {
      id: 'task_' + uid(),
      name: '电商核心购买流程测试',
      url: 'https://shop.example.com',
      objective: '搜索MacBook，加入购物车并结算，不进行最终付款',
      constraints: { max_steps: 18, forbidden_domains: ['stripe.com', 'alipay.com'] },
      updatedAt: new Date(Date.now() - 1000 * 60 * 18),
    },
    {
      id: 'task_' + uid(),
      name: 'B2B 登录与搜索验证',
      url: 'https://b2b.example.com',
      objective: '登录后搜索订单，验证列表展示与筛选可用',
      constraints: { max_steps: 14, forbidden_domains: ['prod.internal'] },
      updatedAt: new Date(Date.now() - 1000 * 60 * 62),
    },
  ],
  instances: [],
  selectedTaskId: null,
  selectedInstanceId: null,
  hilTicket: null,
  hilDrawerOpen: false,
  report: null,
  logs: [],
  ui: {
    leftPage: 0,
    logPage: 0,
    tlPage: 0,
    defPage: 0,
    repTlPage: 0,
  },
  running: {
    timer: null,
  },

  setView: (view) => set({ view }),
  setMode: (mode) => set({ mode }),
  setWsConnected: (wsConnected) => set({ wsConnected }),
  selectTask: (taskId) => set({ selectedTaskId: taskId }),
  selectInstance: (instanceId) => set({ selectedInstanceId: instanceId }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  addInstance: (instance) => set((state) => ({ instances: [instance, ...state.instances] })),
  updateInstance: (instanceId, updates) =>
    set((state) => ({
      instances: state.instances.map((inst) =>
        inst.id === instanceId ? { ...inst, ...updates } : inst
      ),
    })),
  setHilTicket: (ticket) => set({ hilTicket: ticket }),
  setHilDrawerOpen: (open) => set({ hilDrawerOpen: open }),
  setReport: (report) => set({ report }),
  pushLog: (lvl, msg) =>
    set((state) => ({
      logs: [...state.logs, { lvl, msg: `[${new Date().toLocaleTimeString()}] ${msg}` }],
    })),
  clearLogs: () => set({ logs: [] }),
  setUiPage: (key, page) =>
    set((state) => ({
      ui: { ...state.ui, [key]: page },
    })),
  setRunningTimer: (timer) =>
    set((state) => ({
      running: { ...state.running, timer },
    })),
}));

export const mkInstance = (taskId: string): Instance => ({
  id: 'inst_' + uid(),
  taskId,
  status: 'PENDING',
  createdAt: new Date(),
  startedAt: null,
  completedAt: null,
  steps: [],
  hilCount: 0,
  defects: [],
});

export const currentTask = (state: AppState) =>
  state.tasks.find((t) => t.id === state.selectedTaskId);

export const currentInstance = (state: AppState) =>
  state.instances.find((i) => i.id === state.selectedInstanceId);
