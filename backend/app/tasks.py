import json
import asyncio
from pathlib import Path
from celery import Celery

from .config import settings
from .grader import grade_submission, serialize_grade_result
from .schemas import GradeRequest

celery_app = Celery(
    'grading_pipeline',
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']


@celery_app.task(name='app.tasks.grade_task', bind=True)
def grade_task(self, payload: dict) -> dict:
    request = GradeRequest.model_validate(payload)
    grade_result = grade_submission(
        student_id=request.student_id,
        submission_file=Path(request.submission_filename),
        master_key_file=Path(request.master_key_filename),
        rubric_file=Path(request.rubric_filename),
    )
    result_json = serialize_grade_result(grade_result)
    output_path = settings.results_dir / f'{request.student_id}.json'
    output_path.write_text(result_json, encoding='utf-8')
    return {
        'status': 'completed',
        'output_file': str(output_path),
        'student_id': request.student_id,
    }
