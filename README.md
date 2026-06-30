# AI Grading Pipeline

This scaffold implements a scalable AI-powered grading pipeline for quiz submissions.

## Components

- `backend/` — FastAPI app, extraction services, AI wrapper, Celery queue worker.
- `frontend/` — conceptual React dashboard component for professor review.
- `docker-compose.yml` — Redis queue and backend worker.

## Key features

- PDF / DOCX extraction with digital text fallback and OCR fallback.
- Async batch grading through Celery + Redis.
- Modular LLM wrapper for OpenAI / Anthropic / Groq.
- Strict JSON schema output and human-review flagging.

## Getting Started

1. Install Python dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. Copy the example environment file:
   ```powershell
   copy .env.example .env
   ```
3. Add your API key to `.env`.
   - For Groq, set `MODEL_PROVIDER=groq` and `GROQ_API_KEY=your-groq-key`
   - For OpenAI, set `MODEL_PROVIDER=openai` and `OPENAI_API_KEY=your-openai-key`
   - For Anthropic, set `MODEL_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=your-anthropic-api-key`
4. Start Redis, backend, and worker:
   ```powershell
   docker compose up -d
   ```

## Batch grading

The backend supports a batch grading endpoint:

- `POST /grade/batch`
  - accepts repeated `student_ids` and `submissions` fields
  - requires `master_key_path` and `rubric_path` from `/upload-kit`
  - returns queued task IDs for each student

## Sample files

Sample chartered accountancy test material is available in the `samples/` folder:

- `samples/chartered_accountancy_master_key.docx`
- `samples/chartered_accountancy_rubric.docx`
- `samples/student_quiz_001.docx`
- `samples/student_quiz_002.docx`
- `samples/student_quiz_003.pdf`

Use the master key and rubric paths returned from `/upload-kit` when you submit student quizzes.

## Frontend

The frontend is located in `frontend/`. To run it:

1. Install Node dependencies:
   ```powershell
   cd frontend
   npm install
   ```
2. Start the React dev server:
   ```powershell
   npm run dev
   ```
3. Open the local Vite URL shown in the terminal (default `http://localhost:4173`).

The React app fetches grade results from the backend at `http://localhost:8000/results`.

If you are running the backend on a different host or port, update `frontend/src/App.jsx`.

## Environment

Create a `.env` file with keys like:

```env
REDIS_URL=redis://redis:6379/0
MODEL_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GROQ_API_KEY=your-groq-api-key
```

To use Groq, set:

```env
MODEL_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
```
