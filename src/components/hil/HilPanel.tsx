import { useState, useMemo } from 'react';

interface PlannedAction {
  actionType: string;
  selector?: string;
  value?: string;
}

interface HilTicket {
  id: string;
  status: string;
  riskLevel: string;
  stepNo: number;
  reason: string;
  plannedAction?: PlannedAction;
  createdAt: string;
  expiresAt?: string;
  screenshot?: string;
}

interface HilPanelProps {
  tickets: HilTicket[];
  selected: HilTicket | null;
  onDecision: (
    ticketId: string,
    decision: string,
    feedback?: string,
    modifiedAction?: PlannedAction
  ) => void;
}

export default function HilPanel({ tickets, selected, onDecision }: HilPanelProps) {
  const [feedback, setFeedback] = useState('');
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [modifiedAction, setModifiedAction] = useState<PlannedAction>({
    actionType: 'click',
    selector: '',
    value: '',
  });

  const pendingCount = useMemo(() => {
    return tickets.filter((t) => t.status === 'WAITING').length;
  }, [tickets]);

  const handleDecision = (decision: string) => {
    if (selected && onDecision) {
      onDecision(
        selected.id,
        decision,
        feedback,
        decision === 'MODIFIED' ? modifiedAction : undefined
      );
      setFeedback('');
    }
  };

  const openModifyModal = () => {
    setShowModifyModal(true);
    if (selected?.plannedAction) {
      setModifiedAction({ ...selected.plannedAction });
    }
  };

  const closeModifyModal = () => {
    setShowModifyModal(false);
  };

  const submitModified = () => {
    handleDecision('MODIFIED');
    closeModifyModal();
  };

  const formatTime = (ts: string) => {
    return new Date(ts).toLocaleString('zh-CN');
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeModifyModal();
    }
  };

  return (
    <div className="hil-panel">
      <div className="hil-header">
        <h2>HIL 工单列表</h2>
        <span className="badge">{pendingCount} 待处理</span>
      </div>

      <div className="hil-list">
        {tickets.length > 0 ? (
          tickets.map((ticket) => (
            <div
              key={ticket.id}
              className={`hil-ticket ${selected?.id === ticket.id ? 'selected' : ''}`}
            >
              <div className="ticket-header">
                <span className={`risk-badge ${ticket.riskLevel}`}>{ticket.riskLevel}</span>
                <span className="step-no">步骤 {ticket.stepNo}</span>
              </div>
              <p className="reason">{ticket.reason}</p>
              {ticket.plannedAction && (
                <div className="planned-action">
                  <strong>建议动作:</strong>
                  <code>
                    {ticket.plannedAction.actionType}{' '}
                    {ticket.plannedAction.selector || ticket.plannedAction.value || ''}
                  </code>
                </div>
              )}
              <div className="ticket-meta">
                <span className="time">{formatTime(ticket.createdAt)}</span>
                {ticket.expiresAt && (
                  <span className="expires">超时: {formatTime(ticket.expiresAt)}</span>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty">暂无待处理的 HIL 工单</div>
        )}
      </div>

      {selected && (
        <div className="hil-detail">
          <h3>处理工单 #{selected.id}</h3>

          {selected.screenshot && (
            <img src={selected.screenshot} alt="工单截图" className="screenshot" />
          )}

          <div className="action-buttons">
            <button onClick={() => handleDecision('APPROVED')} className="btn-approve">
              ✅ 批准执行
            </button>
            <button onClick={() => handleDecision('REJECTED')} className="btn-reject">
              ❌ 拒绝
            </button>
            <button onClick={openModifyModal} className="btn-modify">
              ✏️ 修改动作
            </button>
          </div>

          <div className="feedback-form">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="添加反馈意见..."
              rows={3}
            />
          </div>
        </div>
      )}

      {showModifyModal && (
        <div className="modal-overlay" onClick={handleOverlayClick}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>修改动作参数</h3>
            <div className="form-group">
              <label>动作类型</label>
              <select
                value={modifiedAction.actionType}
                onChange={(e) =>
                  setModifiedAction({ ...modifiedAction, actionType: e.target.value })
                }
              >
                <option value="click">点击</option>
                <option value="type">输入</option>
                <option value="navigate">导航</option>
              </select>
            </div>
            <div className="form-group">
              <label>选择器/目标</label>
              <input
                value={modifiedAction.selector}
                onChange={(e) =>
                  setModifiedAction({ ...modifiedAction, selector: e.target.value })
                }
                placeholder="CSS 选择器或 URL"
              />
            </div>
            <div className="form-group">
              <label>输入值 (可选)</label>
              <input
                value={modifiedAction.value}
                onChange={(e) =>
                  setModifiedAction({ ...modifiedAction, value: e.target.value })
                }
                placeholder="输入值"
              />
            </div>
            <div className="modal-actions">
              <button onClick={closeModifyModal}>取消</button>
              <button onClick={submitModified} className="btn-primary">
                提交修改
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .hil-panel {
          background: white;
          border-radius: 8px;
          padding: 16px;
        }

        .hil-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .badge {
          background: #ed8936;
          color: white;
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
        }

        .hil-ticket {
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 8px;
          cursor: pointer;
        }

        .hil-ticket.selected {
          border-color: #667eea;
          background: #f7fafc;
        }

        .risk-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .risk-badge.HIGH {
          background: #fed7d7;
          color: #c53030;
        }

        .risk-badge.MEDIUM {
          background: #feebc8;
          color: #c05621;
        }

        .btn-approve { background: #48bb78; color: white; }
        .btn-reject { background: #f56565; color: white; }
        .btn-modify { background: #667eea; color: white; }

        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .modal {
          background: white;
          padding: 24px;
          border-radius: 12px;
          max-width: 500px;
          width: 100%;
        }
      `}</style>
    </div>
  );
}
