/**
 * 报告详情组件
 * 查看执行报告和步骤回放
 */

import React, { useState } from 'react';

interface Step {
  stepNumber: number;
  nodeName: string;
  actionType?: string;
  thought?: string;
  screenshotUrl?: string;
  error?: string;
  timestamp: string;
}

interface ReportSummary {
  totalSteps: number;
  successRate: number;
  totalDefects: number;
  hilCount: number;
  executionDurationSeconds: number;
}

interface Report {
  id: string;
  instanceId: string;
  summary: ReportSummary;
  steps: Step[];
}

interface ReportDetailProps {
  report: Report;
  onExport: (format: 'json' | 'html') => void;
}

export function ReportDetail({ report, onExport }: ReportDetailProps) {
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [view, setView] = useState<'steps' | 'screenshot'>('steps');

  return (
    <div className="report-detail">
      <div className="detail-header">
        <h2>报告详情</h2>
        <div className="actions">
          <button onClick={() => onExport('json')}>导出 JSON</button>
          <button onClick={() => onExport('html')}>导出 HTML</button>
        </div>
      </div>

      <div className="summary">
        <div className="metric">
          <span className="value">{report.summary.totalSteps}</span>
          <span className="label">总步骤</span>
        </div>
        <div className="metric">
          <span className="value">{(report.summary.successRate * 100).toFixed(0)}%</span>
          <span className="label">成功率</span>
        </div>
        <div className="metric">
          <span className="value">{report.summary.totalDefects}</span>
          <span className="label">缺陷</span>
        </div>
        <div className="metric">
          <span className="value">{report.summary.executionDurationSeconds.toFixed(1)}s</span>
          <span className="label">耗时</span>
        </div>
      </div>

      <div className="view-toggle">
        <button
          className={view === 'steps' ? 'active' : ''}
          onClick={() => setView('steps')}
        >
          步骤列表
        </button>
        <button
          className={view === 'screenshot' ? 'active' : ''}
          onClick={() => setView('screenshot')}
        >
          截图回放
        </button>
      </div>

      {view === 'steps' ? (
        <div className="steps-list">
          {report.steps.map((step) => (
            <div
              key={step.stepNumber}
              className={`step-item ${step.error ? 'has-error' : ''}`}
              onClick={() => setSelectedStep(step.stepNumber)}
            >
              <span className="step-no">#{step.stepNumber}</span>
              <span className="node">{step.nodeName}</span>
              <span className="action">{step.actionType || 'screenshot'}</span>
              {step.error && <span className="error-badge">错误</span>}
            </div>
          ))}
        </div>
      ) : (
        <div className="screenshot-view">
          <div className="timeline">
            {report.steps.map((step) => (
              <div
                key={step.stepNumber}
                className={`timeline-item ${step.screenshotUrl ? 'has-screenshot' : ''}`}
                onClick={() => step.screenshotUrl && setSelectedStep(step.stepNumber)}
              >
                <span>#{step.stepNumber}</span>
              </div>
            ))}
          </div>
          {selectedStep !== null && report.steps[selectedStep]?.screenshotUrl && (
            <img
              src={report.steps[selectedStep].screenshotUrl}
              alt={`步骤 ${selectedStep}`}
              className="screenshot"
            />
          )}
        </div>
      )}
    </div>
  );
}
