from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

from ..schemas import GradeResult


class KitPaths(BaseModel):
    master_key_path: str
    rubric_path: str


class TaskProgress(BaseModel):
    student_id: str
    task_id: str
    status: str
    error: Optional[str] = None


class FlaggedStudent(BaseModel):
    student_id: str
    overall_score: float
    reason: str = 'needs_human_review'


class AgentRunReport(BaseModel):
    run_id: str
    status: Literal['queued', 'running', 'completed', 'partial', 'failed']
    kit: KitPaths
    submitted_count: int
    completed_count: int
    failed_count: int
    pending_count: int = 0
    flagged_count: int
    average_score: Optional[float] = None
    tasks: List[TaskProgress]
    flagged_students: List[FlaggedStudent]
    results: List[GradeResult]
    summary: Optional[str] = None


class AgentRunConfig(BaseModel):
    poll_timeout_seconds: int = Field(default=300, ge=1)
    poll_interval_seconds: float = Field(default=2.0, ge=0.5)
    include_summary: bool = False


class AgentReportRequest(BaseModel):
    run_id: str
    kit: KitPaths
    tasks: List[TaskProgress]


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
