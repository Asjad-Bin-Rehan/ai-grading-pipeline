import json
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .agent.chat_agent import run_chat
from .agent.orchestrator import build_agent_report, submit_grading_workflow
from .agent.schemas import AgentReportRequest, AgentRunReport, ChatRequest, ChatResponse
from .extraction import save_uploaded_file
from .tasks import grade_task

app = FastAPI(title='AI Grading Pipeline')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def store_file(uploaded_file: UploadFile, prefix: str) -> Path:
    file_id = uuid4().hex
    extension = Path(uploaded_file.filename).suffix or '.pdf'
    destination = settings.uploads_dir / f'{prefix}_{file_id}{extension}'
    return save_uploaded_file(uploaded_file, destination)


@app.post('/upload-kit')
def upload_evaluation_kit(
    master_key: UploadFile = File(...),
    rubric: UploadFile = File(...),
):
    master_path = store_file(master_key, 'master_key')
    rubric_path = store_file(rubric, 'rubric')
    return {'master_key_path': str(master_path), 'rubric_path': str(rubric_path)}


@app.post('/grade/submit')
def submit_for_grading(
    student_id: str = Form(...),
    master_key_path: str = Form(...),
    rubric_path: str = Form(...),
    submission: UploadFile = File(...),
):
    if not Path(master_key_path).exists() or not Path(rubric_path).exists():
        raise HTTPException(status_code=400, detail='Master key or rubric file not found')
    submission_path = store_file(submission, f'submission_{student_id}')
    payload = {
        'student_id': student_id,
        'submission_filename': str(submission_path),
        'master_key_filename': master_key_path,
        'rubric_filename': rubric_path,
    }
    task = grade_task.apply_async(args=[payload])
    return {'task_id': task.id, 'status': 'queued'}


@app.post('/grade/batch')
def submit_batch_for_grading(
    student_ids: List[str] = Form(...),
    master_key_path: str = Form(...),
    rubric_path: str = Form(...),
    submissions: List[UploadFile] = File(...),
):
    if not Path(master_key_path).exists() or not Path(rubric_path).exists():
        raise HTTPException(status_code=400, detail='Master key or rubric file not found')
    if len(student_ids) != len(submissions):
        raise HTTPException(
            status_code=400,
            detail='The number of student_ids must equal the number of submission files',
        )

    queued_tasks = []
    for student_id, upload in zip(student_ids, submissions):
        submission_path = store_file(upload, f'submission_{student_id}')
        payload = {
            'student_id': student_id,
            'submission_filename': str(submission_path),
            'master_key_filename': master_key_path,
            'rubric_filename': rubric_path,
        }
        task = grade_task.apply_async(args=[payload])
        queued_tasks.append({'student_id': student_id, 'task_id': task.id})

    return {'status': 'queued', 'tasks': queued_tasks}


@app.post('/agent/run', response_model=AgentRunReport)
def run_agent_grading_workflow(
    master_key: UploadFile = File(...),
    rubric: UploadFile = File(...),
    submissions: List[UploadFile] = File(...),
    student_ids: Optional[List[str]] = Form(None),
):
    if not submissions:
        raise HTTPException(status_code=400, detail='At least one submission file is required')
    if student_ids is not None and len(student_ids) != len(submissions):
        raise HTTPException(
            status_code=400,
            detail='The number of student_ids must equal the number of submission files',
        )

    try:
        return submit_grading_workflow(
            master_key=master_key,
            rubric=rubric,
            submissions=submissions,
            student_ids=student_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/agent/report', response_model=AgentRunReport)
def get_agent_report(request: AgentReportRequest):
    student_ids = [task.student_id for task in request.tasks]
    if len(request.tasks) == 0:
        raise HTTPException(status_code=400, detail='At least one task is required')

    return build_agent_report(
        run_id=request.run_id,
        kit=request.kit,
        tasks=request.tasks,
        student_ids=student_ids,
    )


@app.post('/agent/chat', response_model=ChatResponse)
def agent_chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail='Message cannot be empty')
    try:
        reply = run_chat(
            message=request.message.strip(),
            history=[item.model_dump() for item in request.history],
        )
        return ChatResponse(reply=reply)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Chat agent error: {exc}') from exc


@app.get('/grade/status/{task_id}')
def grade_status(task_id: str):
    async_result = grade_task.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': async_result.status,
        'result': async_result.result if async_result.ready() else None,
    }


@app.get('/results')
def list_results():
    files = sorted(settings.results_dir.glob('*.json'))
    results = []
    for path in files:
        data = json.loads(path.read_text(encoding='utf-8'))
        data['result_id'] = path.stem
        results.append(data)
    return results


@app.get('/results/{student_id}')
def get_result(student_id: str):
    result_file = settings.results_dir / f'{student_id}.json'
    if not result_file.exists():
        raise HTTPException(status_code=404, detail='Result not found')
    return JSONResponse(content=json.loads(result_file.read_text(encoding='utf-8')))
