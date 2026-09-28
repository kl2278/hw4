# Campus Customs

A Yale merch storefront (React + Vite frontend, FastAPI backend, SQLite) with a PydanticAI chat assistant, Boola.

## Setup

1. **Add the data pack.** This repo doesn't include the database or product photos (they're gitignored). Place them at:
   - `data/campus_customs.db`
   - `data/products/`
   - `data/products_transparent/` — optional; if it's missing, product cards just fall back to the original photos in `data/products/`.
2. **Create a virtual environment and install Python dependencies**, from the project root:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Set up the API key:**
   ```
   cp .env.example .env
   ```
   Then edit `.env` and set `PORTKEY_API_KEY` to a real key. `.env` is gitignored — never commit it.

## Running it

**Backend** (from `backend/`):
```
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend**, in a separate terminal (from `frontend/`):
```
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`. Log in with the seeded test account: `test@campuscustoms.yale.edu` / `password`.

## The chat agent

Boola is a PydanticAI agent split across four files in `backend/`: `prompts/prompt.md` (the system prompt), `agent.py` (sets up the agent and tools), `tools.py` (the tools themselves), and `models.py` (the Pydantic types they share). `backend/audit.py` is a supporting helper, not part of the agent itself — it's what writes every agent run to the append-only `output/audit_trail.json` log.

## More detail

See [`output/harness.md`](output/harness.md) for the full system writeup — database schema, every model and tool, all the safety rules (in the prompt and in code), specs (call limits, caps, which model), and more.
