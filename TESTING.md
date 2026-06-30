# AI Grading Pipeline - Testing Guide

## Prerequisites

1. Start the backend:
   ```powershell
   cd 'D:\Quiz Project'
   .venv\Scripts\Activate.ps1
   python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. In a separate terminal, start Redis and the worker (if using Docker):
   ```powershell
   docker compose up -d
   ```
   Or start Redis manually and then start the worker:
   ```powershell
   celery -A backend.app.tasks worker --loglevel=info
   ```

3. Create a `.env` file in the project root:
   ```env
   REDIS_URL=redis://localhost:6379/0
   MODEL_PROVIDER=groq
   GROQ_API_KEY=your-actual-groq-api-key
   ```

---

## API Endpoints

### 1. **POST /upload-kit**
Uploads the Master Answer Key and Evaluation Rubric (required once per grading session).

**Purpose**: Store the answer key and rubric files that will be used to grade all student submissions.

**Parameters**:
- `master_key` (file, required) — PDF or DOCX containing the correct answers
- `rubric` (file, required) — PDF or DOCX containing the grading criteria

**Response**:
```json
{
  "master_key_path": "/absolute/path/to/master_key_abc123.pdf",
  "rubric_path": "/absolute/path/to/rubric_def456.pdf"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/upload-kit" \
  -F "master_key=@master_key.pdf" \
  -F "rubric=@rubric.pdf"
```

**PowerShell Example**:
```powershell
$masterKey = @{master_key = Get-Item "C:\path\to\master_key.pdf"}
$rubric = @{rubric = Get-Item "C:\path\to\rubric.pdf"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/upload-kit" `
  -Method Post `
  -Form @{master_key = $masterKey['master_key']; rubric = $rubric['rubric']}
$response
```

---

### 2. **POST /grade/submit**
Submit a single student quiz for grading.

**Purpose**: Queue one student's submission for AI grading.

**Parameters**:
- `student_id` (string, required) — Unique identifier for the student
- `master_key_path` (string, required) — Path returned from `/upload-kit`
- `rubric_path` (string, required) — Path returned from `/upload-kit`
- `submission` (file, required) — Student's quiz file (PDF or DOCX)

**Response**:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/grade/submit" \
  -F "student_id=STU001" \
  -F "master_key_path=/absolute/path/to/master_key_abc123.pdf" \
  -F "rubric_path=/absolute/path/to/rubric_def456.pdf" \
  -F "submission=@student_quiz_001.pdf"
```

**PowerShell Example**:
```powershell
$submission = Get-Item "C:\path\to\student_001.pdf"
$response = Invoke-RestMethod -Uri "http://localhost:8000/grade/submit" `
  -Method Post `
  -Form @{
    student_id = "STU001"
    master_key_path = "D:\Quiz Project\uploads\master_key_abc123.pdf"
    rubric_path = "D:\Quiz Project\uploads\rubric_def456.pdf"
    submission = $submission
  }
$response
```

---

### 3. **POST /grade/batch**
Submit multiple student quizzes at once (recommended for ~1,000 submissions).

**Purpose**: Queue many submissions efficiently in one request.

**Parameters**:
- `student_ids` (list of strings, required) — Array of student IDs
- `master_key_path` (string, required) — Path returned from `/upload-kit`
- `rubric_path` (string, required) — Path returned from `/upload-kit`
- `submissions` (list of files, required) — Array of student quiz files (order must match `student_ids`)

**Response**:
```json
{
  "status": "queued",
  "tasks": [
    {"student_id": "STU001", "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"},
    {"student_id": "STU002", "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"},
    {"student_id": "STU003", "task_id": "c3d4e5f6-a7b8-9012-cdef-123456789012"}
  ]
}
```

**PowerShell Example** (batch of 3 students):
```powershell
$files = @(
  Get-Item "C:\path\to\student_001.pdf",
  Get-Item "C:\path\to\student_002.pdf",
  Get-Item "C:\path\to\student_003.pdf"
)
$form = @{
  student_ids = "STU001", "STU002", "STU003"
  master_key_path = "D:\Quiz Project\uploads\master_key_abc123.pdf"
  rubric_path = "D:\Quiz Project\uploads\rubric_def456.pdf"
}
$files | ForEach-Object { $form["submissions"] = $_ }
$response = Invoke-RestMethod -Uri "http://localhost:8000/grade/batch" `
  -Method Post `
  -Form $form
$response.tasks | ForEach-Object { Write-Host "$($_.student_id): $($_.task_id)" }
```

---

### 4. **GET /grade/status/{task_id}**
Check the status of a grading task.

**Purpose**: Poll the grading queue to see if a submission has been graded.

**Parameters**:
- `task_id` (string, path parameter) — Task ID returned from `/grade/submit` or `/grade/batch`

**Response** (while processing):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "result": null
}
```

**Response** (after grading):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "result": {
    "status": "completed",
    "output_file": "D:\\Quiz Project\\results\\STU001.json",
    "student_id": "STU001"
  }
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/grade/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**PowerShell Example**:
```powershell
$taskId = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
$status = Invoke-RestMethod -Uri "http://localhost:8000/grade/status/$taskId"
Write-Host "Status: $($status.status)"
if ($status.result) {
  Write-Host "Result: $($status.result | ConvertTo-Json)"
}
```

---

### 5. **GET /results**
Retrieve all graded results.

**Purpose**: List all completed grades (returns all JSON result files).

**Parameters**: None

**Response**:
```json
[
  {
    "student_id": "STU001",
    "overall_score": 85.5,
    "question_evaluations": [
      {
        "question_number": 1,
        "step_by_step_analysis": "Student correctly identified the concept...",
        "points_awarded": 10
      }
    ],
    "needs_human_review": false
  },
  {
    "student_id": "STU002",
    "overall_score": 72.0,
    "question_evaluations": [...],
    "needs_human_review": true
  }
]
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/results"
```

**PowerShell Example**:
```powershell
$allResults = Invoke-RestMethod -Uri "http://localhost:8000/results"
$needsReview = $allResults | Where-Object { $_.needs_human_review -eq $true }
Write-Host "Grades needing human review: $($needsReview.Count)"
$needsReview | ForEach-Object { Write-Host "  - $($_.student_id): Score=$($_.overall_score)" }
```

---

### 6. **GET /results/{student_id}**
Retrieve the grade for a specific student.

**Purpose**: Get the detailed grading result for one student.

**Parameters**:
- `student_id` (string, path parameter) — Student ID

**Response**:
```json
{
  "student_id": "STU001",
  "overall_score": 85.5,
  "question_evaluations": [
    {
      "question_number": 1,
      "step_by_step_analysis": "The student correctly identified the main concept...",
      "points_awarded": 10
    },
    {
      "question_number": 2,
      "step_by_step_analysis": "Partial understanding shown, but missing key details...",
      "points_awarded": 7
    }
  ],
  "needs_human_review": false
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/results/STU001"
```

**PowerShell Example**:
```powershell
$studentId = "STU001"
$result = Invoke-RestMethod -Uri "http://localhost:8000/results/$studentId"
Write-Host "Student: $($result.student_id)"
Write-Host "Score: $($result.overall_score)"
Write-Host "Needs Review: $($result.needs_human_review)"
$result.question_evaluations | ForEach-Object {
  Write-Host "  Q$($_.question_number): $($_.points_awarded) points"
  Write-Host "    Analysis: $($_.step_by_step_analysis)"
}
```

---

## Complete Testing Workflow

### Step 1: Upload the evaluation kit
```powershell
$masterKey = Get-Item "C:\path\to\master_key.pdf"
$rubric = Get-Item "C:\path\to\rubric.pdf"
$kitResponse = Invoke-RestMethod -Uri "http://localhost:8000/upload-kit" `
  -Method Post `
  -Form @{master_key = $masterKey; rubric = $rubric}

$masterKeyPath = $kitResponse.master_key_path
$rubricPath = $kitResponse.rubric_path
Write-Host "Master Key: $masterKeyPath"
Write-Host "Rubric: $rubricPath"
```

### Step 2: Submit a single student
```powershell
$studentFile = Get-Item "C:\path\to\student_001.pdf"
$submitResponse = Invoke-RestMethod -Uri "http://localhost:8000/grade/submit" `
  -Method Post `
  -Form @{
    student_id = "STU001"
    master_key_path = $masterKeyPath
    rubric_path = $rubricPath
    submission = $studentFile
  }

$taskId = $submitResponse.task_id
Write-Host "Task ID: $taskId (Status: $($submitResponse.status))"
```

### Step 3: Check grading status
```powershell
Start-Sleep -Seconds 5  # Wait a bit for processing
$statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/grade/status/$taskId"
Write-Host "Status: $($statusResponse.status)"
```

### Step 4: Retrieve the grade
```powershell
$result = Invoke-RestMethod -Uri "http://localhost:8000/results/STU001"
Write-Host "Grade: $($result.overall_score)"
Write-Host "Review Needed: $($result.needs_human_review)"
```

### Step 5: Batch submit 1,000 students (optional)
```powershell
$studentIds = @()
$studentFiles = @()
for ($i = 1; $i -le 1000; $i++) {
  $studentIds += "STU$($i.ToString('D4'))"
  $studentFiles += Get-Item "C:\path\to\student_$($i.ToString('D4')).pdf"
}

$batchResponse = Invoke-RestMethod -Uri "http://localhost:8000/grade/batch" `
  -Method Post `
  -Form @{
    student_ids = $studentIds
    master_key_path = $masterKeyPath
    rubric_path = $rubricPath
    submissions = $studentFiles
  }

Write-Host "Queued $($batchResponse.tasks.Count) tasks"
```

---

## Monitoring

Check the Celery worker logs to see grading progress:
```powershell
# In the worker terminal, you'll see:
# [2026-06-23 10:15:30,123: INFO/MainProcess] Received task: app.tasks.grade_task
# [2026-06-23 10:15:35,456: INFO/ForkPoolWorker-1] Task app.tasks.grade_task succeeded
```

Check the results directory:
```powershell
Get-ChildItem "D:\Quiz Project\results" -Filter "*.json" | Measure-Object
```

---

## Response Schema

All graded results follow this schema:

```json
{
  "student_id": "string",
  "overall_score": "float (0-100)",
  "question_evaluations": [
    {
      "question_number": "integer",
      "step_by_step_analysis": "string (reasoning before scoring)",
      "points_awarded": "float"
    }
  ],
  "needs_human_review": "boolean"
}
```

The `needs_human_review` flag is `true` when:
- AI confidence is low
- Answer is ambiguous
- Submission was partially unreadable
- Formatting was problematic
