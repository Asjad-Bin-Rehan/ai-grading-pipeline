import json
from pathlib import Path
from typing import Dict

from .ai_client import get_llm_client, parse_json_response
from .config import settings
from .extraction import extract_text
from .schemas import GradeResult, QuestionEvaluation

PROMPT_TEMPLATE = '''
You are grading a single student quiz submission with deterministic precision.

Master Answer Key:
{master_key}

Evaluation Rubric:
{rubric}

Student submission:
{submission}

Instructions:
1. Compare the student's answer directly against the master answer key and rubric.
2. Use a chain-of-thought reasoning style. First explain your reasoning in detail.
3. Then assign points per question and calculate overall score.
4. Output only valid JSON matching the schema.

Required JSON schema:
{{
  "student_id": "string",
  "overall_score": number,
  "question_evaluations": [
    {{
      "question_number": number,
      "step_by_step_analysis": "string",
      "points_awarded": number
    }}
  ],
  "needs_human_review": boolean
}}

Guidance:
- Set `needs_human_review` to true if the answer is ambiguous, the submission is partially unreadable, or confidence is low.
- Do not include any extra text or markdown.
- Keep output as a single top-level JSON object.
'''


def build_prompt(submission_text: str, master_key_text: str, rubric_text: str, student_id: str) -> str:
    return PROMPT_TEMPLATE.format(
        master_key=master_key_text,
        rubric=rubric_text,
        submission=submission_text,
        student_id=student_id,
    )


def normalize_grade_payload(payload: Dict) -> GradeResult:
    questions = [
        QuestionEvaluation(
            question_number=int(item['question_number']),
            step_by_step_analysis=str(item['step_by_step_analysis']).strip(),
            points_awarded=float(item['points_awarded']),
        )
        for item in payload['question_evaluations']
    ]
    return GradeResult(
        student_id=str(payload['student_id']),
        overall_score=float(payload['overall_score']),
        question_evaluations=questions,
        needs_human_review=bool(payload['needs_human_review']),
    )


def grade_submission(student_id: str, submission_file: Path, master_key_file: Path, rubric_file: Path) -> GradeResult:
    submission_text = extract_text(submission_file)
    master_key_text = extract_text(master_key_file)
    rubric_text = extract_text(rubric_file)
    prompt = build_prompt(submission_text, master_key_text, rubric_text, student_id)
    llm = get_llm_client()
    raw_response = llm.grade(prompt)
    parsed = parse_json_response(raw_response)

    if str(parsed.get('student_id')).strip() == '':
        parsed['student_id'] = student_id

    return normalize_grade_payload(parsed)


def serialize_grade_result(result: GradeResult) -> str:
    return result.model_dump_json(indent=2)
