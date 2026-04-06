# Backend Setup

This backend runs a FastAPI service used by the React frontend.

## Prerequisites

- Python 3.9+
- `pip`

## 1) Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

## 3) Configure environment variables

Create `backend/.env` with:

```env
OPENAI_API_KEY=your_openai_api_key
ARCADE_API_KEY=your_arcade_api_key
ARCADE_USER_ID=your_arcade_user_id
# Optional: override model used for all LLM tasks
OPENAI_MODEL=gpt-4o-mini
```

Notes:
- `OPENAI_API_KEY` is required for relevance scoring and summaries.
- `ARCADE_API_KEY` and `ARCADE_USER_ID` are required for Google Docs/Gmail integration.

## 4) Run the API server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: `http://localhost:8000`
