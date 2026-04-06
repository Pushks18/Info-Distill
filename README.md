# Info-Distill

AI-powered article discovery, relevance scoring, summarization, and report generation.

## Main Setup Guide

Run backend and frontend in separate terminals.

## Prerequisites

- Python 3.9+
- Node.js 18+
- npm

## 1) Backend setup and run

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
OPENAI_API_KEY=your_openai_api_key
ARCADE_API_KEY=your_arcade_api_key
ARCADE_USER_ID=your_arcade_user_id
OPENAI_MODEL=gpt-4o-mini
```

Start backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 2) Frontend setup and run

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in terminal (usually `http://localhost:5173`).

## API Endpoints

- `POST /api/process`
- `GET /api/stream-newsletter`
- `POST /api/create-doc`
- `POST /api/article-detail`

## Troubleshooting

- `401 invalid_api_key` means `OPENAI_API_KEY` is invalid or expired.
- If summaries/relevance look weak, verify backend logs show OpenAI success rather than fallback messages.
- If docs/emails fail, check `ARCADE_API_KEY` and `ARCADE_USER_ID`.
