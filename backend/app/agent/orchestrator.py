from typing import List, Optional
from uuid import uuid4

from fastapi import UploadFile

from .schemas import AgentRunConfig, AgentRunReport, FlaggedStudent, KitPaths, TaskProgress
from .tools import (
    batch_submit,
    collect_results,
    derive_student_id,
    poll_task_status,
    poll_tasks_until_done,
    upload_kit,
)


def _build_summary(report: AgentRunReport) -> str:
    lines = [
        f'Run {report.run_id}: {report.status}.',
        f'Submitted {report.submitted_count}, completed {report.completed_count}, '
        f'failed {report.failed_count}, pending {report.pending_count}.',
    ]
    if report.average_score is not None:
        lines.append(f'Average score: {report.average_score:.1f}.')
    if report.flagged_count:
        flagged_ids = ', '.join(item.student_id for item in report.flagged_students)
        lines.append(f'Flagged for review ({report.flagged_count}): {flagged_ids}.')
    failed_tasks = [task for task in report.tasks if task.status == 'FAILURE' and task.error]
    if failed_tasks:
        lines.append(f'First error: {failed_tasks[0].error}')
    return ' '.join(lines)


def _resolve_student_ids(
    submissions: List[UploadFile],
    student_ids: Optional[List[str]],
) -> List[str]:
    resolved = student_ids or [
        derive_student_id(upload.filename or '', index)
        for index, upload in enumerate(submissions)
    ]
    if len(resolved) != len(submissions):
        raise ValueError('The number of student_ids must equal the number of submission files')
    return resolved


def submit_grading_workflow(
    master_key: UploadFile,
    rubric: UploadFile,
    submissions: List[UploadFile],
    student_ids: Optional[List[str]] = None,
) -> AgentRunReport:
    if not submissions:
        raise ValueError('At least one submission file is required')

    run_id = uuid4().hex
    kit = upload_kit(master_key, rubric)
    resolved_student_ids = _resolve_student_ids(submissions, student_ids)

    tasks = batch_submit(
        student_ids=resolved_student_ids,
        submissions=submissions,
        master_key_path=kit.master_key_path,
        rubric_path=kit.rubric_path,
    )

    report = build_agent_report(
        run_id=run_id,
        kit=kit,
        tasks=tasks,
        student_ids=resolved_student_ids,
    )
    report.status = 'queued'
    report.summary = _build_summary(report)
    return report


def build_agent_report(
    run_id: str,
    kit: KitPaths,
    tasks: List[TaskProgress],
    student_ids: List[str],
) -> AgentRunReport:
    refreshed_tasks = [poll_task_status(task) for task in tasks]

    completed_count = sum(1 for task in refreshed_tasks if task.status == 'SUCCESS')
    failed_count = sum(1 for task in refreshed_tasks if task.status == 'FAILURE')
    pending_count = len(refreshed_tasks) - completed_count - failed_count

    if pending_count == len(refreshed_tasks):
        status = 'queued'
    elif pending_count > 0:
        status = 'running'
    elif completed_count == len(refreshed_tasks):
        status = 'completed'
    elif completed_count == 0 and failed_count == len(refreshed_tasks):
        status = 'failed'
    else:
        status = 'partial'

    results = collect_results(student_ids)
    flagged_students = [
        FlaggedStudent(
            student_id=result.student_id,
            overall_score=result.overall_score,
        )
        for result in results
        if result.needs_human_review
    ]

    average_score = None
    if results:
        average_score = sum(result.overall_score for result in results) / len(results)

    report = AgentRunReport(
        run_id=run_id,
        status=status,
        kit=kit,
        submitted_count=len(refreshed_tasks),
        completed_count=completed_count,
        failed_count=failed_count,
        pending_count=pending_count,
        flagged_count=len(flagged_students),
        average_score=average_score,
        tasks=refreshed_tasks,
        flagged_students=flagged_students,
        results=results,
    )
    report.summary = _build_summary(report)
    return report


def run_grading_workflow(
    master_key: UploadFile,
    rubric: UploadFile,
    submissions: List[UploadFile],
    student_ids: Optional[List[str]] = None,
    config: Optional[AgentRunConfig] = None,
) -> AgentRunReport:
    """Blocking workflow used by scripts; the API uses submit + poll instead."""
    config = config or AgentRunConfig()
    report = submit_grading_workflow(master_key, rubric, submissions, student_ids)

    tasks, _timed_out = poll_tasks_until_done(
        tasks=report.tasks,
        timeout_seconds=config.poll_timeout_seconds,
        interval_seconds=config.poll_interval_seconds,
    )

    return build_agent_report(
        run_id=report.run_id,
        kit=report.kit,
        tasks=tasks,
        student_ids=[task.student_id for task in tasks],
    )
