# Groww RAG Bot

Class-demo RAG chatbot. Phase 1: corpus ingest into local Chroma. Phase 2: retrieve + generate + chat API. Phase 3: web chat UI. Phase 4: debug panel + demo questions.

## Setup

Install [Python 3.11+](https://www.python.org/downloads/) and tick **Add python.exe to PATH**.

```powershell
cd "C:\Users\Harshal Sarowar\OneDrive\Desktop\Groww Rag Bot"
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Leave `OPENAI_API_KEY` empty to embed with Sentence Transformers local model. Set the key (and optional `OPENAI_BASE_URL`) to use a hosted embedding model + LLM.

## Ingest (Phase 1)

```powershell
.\.venv\Scripts\python -m src.ingest
```

Rebuilds `data/chroma/` from `corpus/*.md` (full replace, not incremental).

Same rebuild via API (after starting server):
`POST http://127.0.0.1:8000/index`

## Run API (Phase 2)

```powershell
.\.venv\Scripts\uvicorn src.api:app --reload --port 8000
```

Endpoints:
- `GET  /health` — `{ "ok": true, "index_exists": true }`
- `POST /index` — rebuild vector store
- `POST /chat` — `{ "question": "...", "history": [] }` → `{ answer, citations, debug }`

## Run Web UI (Phase 3–4)

Open `web/index.html` directly in a browser (double-click), or serve it:

```powershell
cd web
.\.venv\Scripts\python -m http.server 5173
```

Then open `http://127.0.0.1:5173` in browser.

The UI calls the API at `http://127.0.0.1:8000` (CORS enabled).

## Demo Script (Phase 4) — 5–10 minutes

See `web/demo-questions.md` for full list.

1. **In-corpus**: "What is Groww?" → answer + citations. Open debug panel → `threshold_passed: true`, top match `overview-001` with score.
2. **Follow-up**: "What products does it offer?" → different chunk (`products-001`). Debug panel updates.
3. **Out-of-corpus**: "What is my portfolio value?" → refusal. Debug shows `threshold_passed: false`, no matches.
4. **Guardrail (advice)**: "Should I buy Groww stock?" → refusal. Debug shows `guardrail: advice`, no retrieval.
5. **Guardrail (secret)**: "My password is 123456" → refusal. Debug shows `guardrail: secret`.

## Test Checklist

- [ ] Start API: `.\.venv\Scripts\uvicorn src.api:app --reload --port 8000`
- [ ] Open `http://127.0.0.1:5173` (or double-click `web/index.html`)
- [ ] Ask "What is Groww?" → answer + citations + debug panel populated
- [ ] Ask "What is my portfolio value?" → refusal, debug shows threshold failed
- [ ] Click sample question chips → auto-fills input
- [ ] Stop API → UI shows error banner, last message remains
- [ ] Click "Rebuild Index" → index rebuilds via API