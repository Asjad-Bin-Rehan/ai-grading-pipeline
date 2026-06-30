#!/usr/bin/env python
"""
Process pending grading tasks synchronously for demo.
This bypasses Celery and processes tasks directly.
"""
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.config import settings
from app.grader import grade_submission

# Get sample files
samples_dir = Path(__file__).parent / 'samples'
uploads_dir = settings.uploads_dir
results_dir = settings.results_dir

print(f"📋 Synchronous Grading Demo")
print(f"   Uploads: {uploads_dir}")
print(f"   Results: {results_dir}\n")

# Find the latest kit files
kit_files = sorted(uploads_dir.glob('master_key_*.docx'), key=lambda p: p.stat().st_mtime)
rubric_files = sorted(uploads_dir.glob('rubric_*.docx'), key=lambda p: p.stat().st_mtime)

if not kit_files or not rubric_files:
    print("❌ No kit files found. Upload a kit first.")
    sys.exit(1)

master_key_path = kit_files[-1]
rubric_path = rubric_files[-1]

print(f"📚 Using Kit:")
print(f"   Master: {master_key_path.name}")
print(f"   Rubric: {rubric_path.name}\n")

# Find submission files
submission_files = list(uploads_dir.glob('submission_*'))
print(f"📝 Processing {len(submission_files)} submissions...\n")

for submission_file in submission_files:
    student_id = submission_file.stem.replace('submission_', '')
    print(f"   Grading {student_id}...")
    
    # Grade using files directly
    result = grade_submission(
        student_id=student_id,
        submission_file=submission_file,
        master_key_file=master_key_path,
        rubric_file=rubric_path,
    )
    
    # Write result
    result_file = results_dir / f"{student_id}_result.json"
    with open(result_file, "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    
    score = result.overall_score
    max_score = 25  # Total possible score
    needs_review = "[REVIEW]" if result.needs_human_review else "[OK]"
    print(f"      {needs_review} Score: {score}/{max_score}")

print("\n✨ All submissions graded!")
print(f"   Results written to: {results_dir}")
