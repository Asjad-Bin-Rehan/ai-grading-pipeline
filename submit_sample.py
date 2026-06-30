#!/usr/bin/env python
"""
Submit sample student quizzes for grading.
"""
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
SAMPLES_DIR = Path("samples")

# First, upload the grading kit
print("📤 Uploading grading kit...")
with open(SAMPLES_DIR / "chartered_accountancy_master_key.docx", "rb") as mk, \
     open(SAMPLES_DIR / "chartered_accountancy_rubric.docx", "rb") as rb:
    kit_response = requests.post(
        f"{BASE_URL}/upload-kit",
        files={"master_key": mk, "rubric": rb}
    )
    if kit_response.status_code == 200:
        kit_data = kit_response.json()
        master_key_path = kit_data["master_key_path"]
        rubric_path = kit_data["rubric_path"]
        print(f"✅ Kit uploaded!")
        print(f"   Master key: {master_key_path}")
        print(f"   Rubric: {rubric_path}")
    else:
        print(f"❌ Failed to upload kit: {kit_response.text}")
        exit(1)

# Submit student quizzes
student_files = list(SAMPLES_DIR.glob("student_quiz_*.docx")) + list(SAMPLES_DIR.glob("student_quiz_*.pdf"))
print(f"\n📝 Submitting {len(student_files)} student quizzes for grading...\n")

for i, student_file in enumerate(sorted(student_files), 1):
    student_id = f"student_{i:03d}"
    print(f"   Submitting {student_file.name} as {student_id}...")
    
    with open(student_file, "rb") as sf:
        response = requests.post(
            f"{BASE_URL}/grade/submit",
            files={"submission": sf},
            data={
                "student_id": student_id,
                "master_key_path": master_key_path,
                "rubric_path": rubric_path,
            }
        )
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id", "?")
            print(f"      ✅ Task enqueued: {task_id}")
        else:
            print(f"      ❌ Error: {response.text}")

print("\n✨ All submissions queued! Check the Celery worker logs for grading progress.")
print(f"   Backend: {BASE_URL}/results")
print(f"   Frontend: http://localhost:4173")
