import json
import shutil
from pathlib import Path
from typing import List
from uuid import uuid4

from langchain_core.tools import tool

from ..config import settings
from ..tasks import grade_task
from .tools import derive_student_id, load_grade_result

PROJECT_ROOT = Path(__file__).resolve().parents[3]

def _load_all_result_summaries() -> List[dict]:
    summaries = []
    for path in sorted(settings.results_dir.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        summaries.append({
            'student_id': data.get('student_id'),
            'overall_score': data.get('overall_score'),
            'needs_human_review': data.get('needs_human_review'),
            'question_count': len(data.get('question_evaluations', [])),
            'result_file': path.name,
        })
    return summaries


@tool
def list_grading_results() -> str:
    """List all completed grading results with student ID, score, and review status."""
    summaries = _load_all_result_summaries()
    if not summaries:
        return 'No grading results found yet. Use the Auto Grade panel to submit quizzes.'
    return json.dumps(summaries, indent=2)


@tool
def get_flagged_students() -> str:
    """List students flagged for human review (ambiguous or low-confidence answers)."""
    flagged = [
        item for item in _load_all_result_summaries()
        if item.get('needs_human_review')
    ]
    if not flagged:
        return 'No students are currently flagged for human review.'
    return json.dumps(flagged, indent=2)


@tool
def get_student_grade(student_id: str) -> str:
    """Get detailed grade for one student, including per-question analysis and points."""
    result = load_grade_result(student_id)
    if not result:
        return f'No grade found for student_id="{student_id}".'
    return result.model_dump_json(indent=2)


@tool
def get_grading_statistics() -> str:
    """Return aggregate stats: total submissions, average score, flagged count, pass count."""
    summaries = _load_all_result_summaries()
    if not summaries:
        return 'No results available for statistics.'

    scores = [item['overall_score'] for item in summaries if item.get('overall_score') is not None]
    flagged = sum(1 for item in summaries if item.get('needs_human_review'))
    stats = {
        'total_submissions': len(summaries),
        'flagged_count': flagged,
        'passed_count': len(summaries) - flagged,
        'average_score': round(sum(scores) / len(scores), 2) if scores else None,
        'min_score': min(scores) if scores else None,
        'max_score': max(scores) if scores else None,
    }
    return json.dumps(stats, indent=2)


@tool
def check_grading_task_status(task_id: str) -> str:
    """Check Celery grading task status by task_id. Returns PENDING, SUCCESS, FAILURE, etc."""
    async_result = grade_task.AsyncResult(task_id)
    payload = {
        'task_id': task_id,
        'status': async_result.status,
    }
    if async_result.ready():
        if async_result.successful():
            payload['result'] = async_result.result
        else:
            payload['error'] = str(async_result.result)
    return json.dumps(payload, indent=2)


@tool
def list_recent_uploads() -> str:
    """List recently uploaded master keys, rubrics, and student submissions on the server."""
    uploads_dir = settings.uploads_dir
    if not uploads_dir.exists():
        return 'No uploads directory found.'

    files = sorted(uploads_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    listing = [
        {'name': path.name, 'type': path.suffix, 'size_bytes': path.stat().st_size}
        for path in files
        if path.is_file()
    ]
    if not listing:
        return 'No uploaded files found.'
    return json.dumps(listing, indent=2)


def _resolve_folder(folder_path: str) -> Path:
    path = Path(folder_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / folder_path
    return path.resolve()


def _resolve_kit_paths() -> tuple[str, str]:
    samples_master = PROJECT_ROOT / 'samples' / 'chartered_accountancy_master_key.docx'
    samples_rubric = PROJECT_ROOT / 'samples' / 'chartered_accountancy_rubric.docx'
    if samples_master.exists() and samples_rubric.exists():
        return str(samples_master), str(samples_rubric)

    master_files = sorted(settings.uploads_dir.glob('master_key_*'), key=lambda p: p.stat().st_mtime)
    rubric_files = sorted(settings.uploads_dir.glob('rubric_*'), key=lambda p: p.stat().st_mtime)
    if master_files and rubric_files:
        return str(master_files[-1]), str(rubric_files[-1])

    raise FileNotFoundError(
        'No grading kit found. Add samples/chartered_accountancy_master_key.docx and rubric, '
        'or upload a kit via the UI first.'
    )


@tool
def list_quizzes_in_folder(folder_path: str) -> str:
    """List quiz files (docx/pdf) in a project folder. Example: samples/generated"""
    folder = _resolve_folder(folder_path)
    if not folder.exists():
        return f'Folder not found: {folder}'
    if not folder.is_dir():
        return f'Path is not a folder: {folder}'

    files = sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {'.docx', '.pdf'}]
    )
    if not files:
        return f'No .docx or .pdf quiz files found in {folder}.'

    return json.dumps([{'filename': path.name, 'student_id': path.stem} for path in files], indent=2)


@tool
def grade_quizzes_from_folder(folder_path: str) -> str:
    """Queue all quiz files in a folder for AI grading using the sample or latest uploaded kit.
    Example folder_path: samples/generated. Returns task IDs to track progress."""
    folder = _resolve_folder(folder_path)
    if not folder.exists() or not folder.is_dir():
        return f'Folder not found: {folder}'

    quiz_files = sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {'.docx', '.pdf'}]
    )
    if not quiz_files:
        return f'No quiz files found in {folder}.'

    try:
        master_key_path, rubric_path = _resolve_kit_paths()
    except FileNotFoundError as exc:
        return str(exc)

    queued = []
    for index, quiz_file in enumerate(quiz_files):
        student_id = derive_student_id(quiz_file.name, index)
        submission_copy = settings.uploads_dir / f'submission_{student_id}_{uuid4().hex}{quiz_file.suffix}'
        shutil.copy2(quiz_file, submission_copy)
        payload = {
            'student_id': student_id,
            'submission_filename': str(submission_copy),
            'master_key_filename': master_key_path,
            'rubric_filename': rubric_path,
        }
        async_result = grade_task.apply_async(args=[payload])
        queued.append({
            'student_id': student_id,
            'task_id': async_result.id,
            'source_file': quiz_file.name,
            'status': 'queued',
        })

    return json.dumps({
        'message': f'Queued {len(queued)} quizzes for grading from {folder}.',
        'master_key_path': master_key_path,
        'rubric_path': rubric_path,
        'tasks': queued,
        'hint': 'Use check_grading_task_status with a task_id, or refresh the Results dashboard in a minute.',
    }, indent=2)


CHAT_TOOLS = [
    list_grading_results,
    get_flagged_students,
    get_student_grade,
    get_grading_statistics,
    check_grading_task_status,
    list_recent_uploads,
    list_quizzes_in_folder,
    grade_quizzes_from_folder,
]