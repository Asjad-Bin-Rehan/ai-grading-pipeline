# Deployment Guide — Vercel (frontend) + Render (API + worker)

This project cannot run **entirely** on Vercel because it needs:

- A **long-running FastAPI** server
- A **Celery worker** for background grading
- **Redis** (use Upstash — you already have this)

**Split:**

| What | Where |
|------|--------|
| React UI | **Vercel** |
| FastAPI API | **Render** (or Railway / Fly.io) |
| Celery worker | **Render** (background worker) |
| Redis | **Upstash** |

---

## Part A — Push code to GitHub

**Where:** Your computer + GitHub

1. Commit the latest code (if not already pushed):

   ```powershell
   cd "D:\Quiz Project"
   git add .
   git status
   git commit -m "Prepare deployment: API URL env, CORS, Render and Vercel config"
   git push origin main
   ```

2. Confirm the repo is on GitHub (e.g. `https://github.com/Asjad-Bin-Rehan/ai-grading-pipeline`).

---

## Part B — Deploy backend + worker on Render

**Where:** [https://dashboard.render.com](https://dashboard.render.com)

### B1. Create account and connect GitHub

1. Sign up / log in to Render.
2. **Account Settings → Connect GitHub** and authorize your repo.

### B2. Deploy with Blueprint (recommended)

1. Click **New → Blueprint**.
2. Select your **ai-grading-pipeline** repository.
3. Render reads `render.yaml` at the repo root and proposes:
   - **ai-grading-api** (web)
   - **ai-grading-worker** (worker)
4. Click **Apply**.

### B3. Set environment variables (both web + worker)

**Where:** Each service → **Environment** tab

Add the same keys you use locally (from `.env`), **never commit real keys**:

| Key | Example / notes |
|-----|------------------|
| `REDIS_URL` | Your Upstash URL (`rediss://...`) |
| `MODEL_PROVIDER` | `groq` |
| `GROQ_API_KEY` | Your Groq key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `CORS_ORIGINS` | `http://localhost:4173` (add Vercel URL in Part C) |

Optional: `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.

5. **Save** — Render redeploys automatically.

### B4. Copy your API URL

**Where:** Web service **ai-grading-api** → top of page

Example: `https://ai-grading-api.onrender.com`

Test in browser: `https://YOUR-API.onrender.com/docs` — you should see FastAPI Swagger.

### B5. Confirm worker is running

**Where:** **ai-grading-worker** → **Logs**

You should see: `celery@... ready.`

### Manual deploy (without Blueprint)

If Blueprint fails, create two services manually from the same repo:

**Web service**

- Root directory: (repo root)
- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

**Background worker**

- Start: `celery -A backend.app.tasks worker --loglevel=info --concurrency=2`
- Same env vars as the web service

### Render limitations (important)

- **Free tier** services spin down when idle; first request may be slow.
- **OCR (Tesseract)** is not installed on default Python runtime — scanned PDFs may fail unless you deploy with **Docker** (`Dockerfile` in repo).
- **Uploads/results** on Render free disk are ephemeral — redeploys can wipe files. For production, use S3 or a database later.

---

## Part C — Deploy frontend on Vercel

**Where:** [https://vercel.com](https://vercel.com)

### C1. Import project

1. **Add New → Project**.
2. Import your GitHub repo.

### C2. Configure build (critical)

**Where:** Vercel import screen → **Configure Project**

| Setting | Value |
|---------|--------|
| **Root Directory** | `frontend` |
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

### C3. Environment variable

**Where:** **Environment Variables** (before or after first deploy)

| Name | Value |
|------|--------|
| `VITE_API_URL` | `https://ai-grading-api.onrender.com` (your Render URL, **no** trailing slash) |

Apply to **Production** (and Preview if you want).

### C4. Deploy

Click **Deploy**. When finished, Vercel gives you a URL like:

`https://ai-grading-pipeline.vercel.app`

### C5. Update CORS on Render

**Where:** Render → **ai-grading-api** → **Environment**

Edit `CORS_ORIGINS`:

```
http://localhost:4173,https://ai-grading-pipeline.vercel.app
```

Use your **exact** Vercel URL. Save and wait for redeploy.

---

## Part D — End-to-end test

**Where:** Browser

1. Open your Vercel URL.
2. Open **DevTools → Network**.
3. Upload a kit or run **Auto Grade** — requests should go to `https://....onrender.com`, not `localhost`.
4. After grading, check **Results** and **Chat assistant**.

If you see **CORS errors**: fix `CORS_ORIGINS` on Render (must match Vercel origin exactly, including `https`).

If grading stays **queued**: check **worker logs** on Render and `REDIS_URL`.

---

## Part E — Local development (unchanged)

**Where:** Your PC

```powershell
cd "D:\Quiz Project"
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
# separate terminal: celery worker
cd frontend && npm run dev
```

Frontend uses `http://localhost:8000` when `VITE_API_URL` is not set.

Optional: `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

---

## Quick reference — what lives where

```
GitHub repo
├── frontend/          → Vercel (Root Directory = frontend)
├── backend/           → Render web + worker
├── render.yaml        → Render Blueprint
├── requirements.txt   → Render build
└── .env               → LOCAL ONLY (never commit)
```

---

## Optional: custom domain

**Vercel:** Project → Settings → Domains  
**Render:** Web service → Settings → Custom Domain  

Add the custom frontend domain to `CORS_ORIGINS` on Render.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| CORS blocked | Add Vercel URL to `CORS_ORIGINS` on Render |
| API 404 from Vercel | Check `VITE_API_URL` in Vercel env vars; redeploy frontend |
| Grading never completes | Worker not running or wrong `REDIS_URL` |
| 502 on Render | Service waking from sleep; wait and retry |
| Chat timeout | Groq rate limits; check worker/API logs |

---

## Checklist

- [ ] Code pushed to GitHub  
- [ ] Render web + worker deployed with env vars  
- [ ] `/docs` works on Render URL  
- [ ] Vercel project root = `frontend`  
- [ ] `VITE_API_URL` set on Vercel  
- [ ] `CORS_ORIGINS` includes Vercel URL on Render  
- [ ] Full grading test on production URLs  
