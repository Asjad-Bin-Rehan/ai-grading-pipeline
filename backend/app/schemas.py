from typing import List
from pydantic import BaseModel

class QuestionEvaluation(BaseModel):
    question_number: int
    step_by_step_analysis: str
    points_awarded: float

class GradeResult(BaseModel):
    student_id: str
    overall_score: float
    question_evaluations: List[QuestionEvaluation]
    needs_human_review: bool

class GradeRequest(BaseModel):
    student_id: str
    submission_filename: str
    master_key_filename: str
    rubric_filename: str
