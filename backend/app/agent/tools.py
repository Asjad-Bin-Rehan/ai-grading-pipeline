import json
import time
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from fastapi import UploadFile

from ..config import settings
from ..extraction import save_uploaded_file
from ..schemas import GradeResult
from ..tasks import grade_task
from .schemas import KitPaths, TaskProgress


def store_upload(uploaded_file: UploadFile, prefix: str) -> Path:
    file_id = uuid4().hex
    extension = Path(uploaded_file.filename or '').suffix or '.pdf'
    destination = settings.uploads_dir / f'{prefix}_{file_id}{extension}'
    return save_uploaded_file(uploaded_file, destination)


def derive_student_id(filename: str, index: int) -> str:
    stem = Path(filename).stem
    return stem if stem else f'student_{index + 1}'


def upload_kit(master_key: UploadFile, rubric: UploadFile) -> KitPaths:
    master_path = store_upload(master_key, 'master_key')
    rubric_path = store_upload(rubric, 'rubric')
    return KitPaths(
        master_key_path=str(master_path),
        rubric_path=str(rubric_path),
    )


def batch_submit(
    student_ids: List[str],
    submissions: List[UploadFile],
    master_key_path: str,
    rubric_path: str,
) -> List[TaskProgress]:
    if len(student_ids) != len(submissions):
        raise ValueError('The number of student_ids must equal the number of submission files')

    tasks: List[TaskProgress] = []
    for student_id, upload in zip(student_ids, submissions):
        submission_path = store_upload(upload, f'submission_{student_id}')
        payload = {
            'student_id': student_id,
            'submission_filename': str(submission_path),
            'master_key_filename': master_key_path,
            'rubric_filename': rubric_path,
        }
        async_result = grade_task.apply_async(args=[payload])
        tasks.append(
            TaskProgress(
                student_id=student_id,
                task_id=async_result.id,
                status='PENDING',
            )
        )
    return tasks


def poll_task_status(task: TaskProgress) -> TaskProgress:
    async_result = grade_task.AsyncResult(task.task_id)
    status = async_result.status
    error = None
    if status == 'FAILURE':
        error = str(async_result.result) if async_result.result else 'Task failed'
    return TaskProgress(
        student_id=task.student_id,
        task_id=task.task_id,
        status=status,
        error=error,
    )


def poll_tasks_until_done(
    tasks: List[TaskProgress],
    timeout_seconds: int,
    interval_seconds: float,
) -> Tuple[List[TaskProgress], bool]:
    """Poll Celery tasks until all finish or timeout. Returns updated tasks and timed_out flag."""
    deadline = time.monotonic() + timeout_seconds
    current = list(tasks)

    while time.monotonic() < deadline:
        current = [poll_task_status(task) for task in current]
        if all(task.status in ('SUCCESS', 'FAILURE') for task in current):
            return current, False
        time.sleep(interval_seconds)

    current = [poll_task_status(task) for task in current]
    return current, True


def _find_result_path(student_id: str) -> Optional[Path]:
    results_dir = settings.results_dir
    candidates = [
        results_dir / f'{student_id}.json',
        results_dir / f'{student_id}_result.json',
    ]
    for path in candidates:
        if path.exists():
            return path

    matches = sorted(results_dir.glob(f'{student_id}*.json'))
    if matches:
        return matches[-1]
    return None


def load_grade_result(student_id: str) -> Optional[GradeResult]:
    path = _find_result_path(student_id)
    if not path:
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    return GradeResult.model_validate(data)


def collect_results(student_ids: List[str]) -> List[GradeResult]:
    results: List[GradeResult] = []
    for student_id in student_ids:
        grade = load_grade_result(student_id)
        if grade:
            results.append(grade)
    return results
