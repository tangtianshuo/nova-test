/**
 * 报告列表组件
 */

import React from 'react';

interface Report {
  id: string;
  instanceId: string;
  status: string;
  summary: {
    totalSteps: number;
    successRate: number;
    totalDefects: number;
    hilCount: number;
    executionDurationSeconds: number;
  };
  createdAt: string;
}

interface ReportListProps {
  reports: Report[];
  onView: (reportId: string) => void;
  onExport: (reportId: string, format: 'json' | 'html') => void;
}

export function ReportList({ reports, onView, onExport }: ReportListProps) {
  return (
    <div className="report-list">
      <div className="report-header">
        <h2>测试报告</h2>
        <span className="count">{reports.length} 个报告</span>
      </div>

      <div className="report-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>状态</th>
              <th>步骤</th>
              <th>成功率</th>
              <th>缺陷</th>
              <th>耗时</th>
              <th>时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td className="id-cell">{report.id.slice(0, 8)}...</td>
                <td>
                  <span className={`status ${report.status.toLowerCase()}`}>
                    {report.status}
                  </span>
                </td>
                <td>{report.summary.totalSteps}</td>
                <td>{(report.summary.successRate * 100).toFixed(1)}%</td>
                <td className={report.summary.totalDefects > 0 ? 'has-defects' : ''}>
                  {report.summary.totalDefects}
                </td>
                <td>{report.summary.executionDurationSeconds.toFixed(1)}s</td>
                <td>{new Date(report.createdAt).toLocaleString('zh-CN')}</td>
                <td className="actions">
                  <button onClick={() => onView(report.id)}>查看</button>
                  <button onClick={() => onExport(report.id, 'json')}>JSON</button>
                  <button onClick={() => onExport(report.id, 'html')}>HTML</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ReportList;
