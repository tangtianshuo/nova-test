"""
报告类型定义
============

定义报告的数据结构
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ReportStatus(str, Enum):
    """报告状态"""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExportFormat(str, Enum):
    """导出格式"""
    JSON = "JSON"
    HTML = "HTML"
    PDF = "PDF"


class StepRecord(BaseModel):
    """步骤记录"""
    step_number: int
    node_name: str
    action_type: Optional[str] = None
    action_target: Optional[Dict[str, Any]] = None
    action_params: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None
    confidence: Optional[float] = None
    screenshot_url: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    is_defect: bool = False
    error: Optional[str] = None
    timestamp: Optional[str] = None


class HilRecord(BaseModel):
    """HIL 决策记录"""
    ticket_id: str
    step_number: int
    reason: str
    risk_level: str
    decision: str
    human_feedback: Optional[str] = None
    modified_action: Optional[Dict[str, Any]] = None
    resolved_at: Optional[str] = None


class ReportSummary(BaseModel):
    """报告摘要"""
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    total_defects: int = 0
    critical_defects: int = 0
    hil_count: int = 0
    execution_duration_seconds: float = 0.0
    success_rate: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class Report(BaseModel):
    """完整报告"""
    report_id: str
    instance_id: str
    tenant_id: str
    task_id: str
    status: ReportStatus
    summary: ReportSummary
    steps: List[StepRecord] = Field(default_factory=list)
    hil_records: List[HilRecord] = Field(default_factory=list)
    defects: List[Dict[str, Any]] = Field(default_factory=list)
    schema_version: str = "1.0.0"
    created_at: str = Field(default_factory=datetime.now)
    updated_at: str = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
