# TouristAI Project Structure

This project now keeps the active app code in predictable top-level folders.

## Frontend

`frontend/`

Active React + TypeScript + Vite app.

Important folders:

- `frontend/src/pages` - route screens such as chat, home, planner, transport results.
- `frontend/src/context` - shared planner/chat state.
- `frontend/src/components/chat` - chat-specific UI pieces.
- `frontend/src/components/dialogs` - modals, drawers, copilot UI.
- `frontend/src/components/shared` - reusable trip, weather, crowd, nearby widgets.
- `frontend/src/api` - frontend API URL helpers and external API wrappers.
- `frontend/public` - static assets.

Common commands:

```powershell
cd frontend
npm run dev
npm run build
```

## Backend

`backend/`

FastAPI backend.

Important folders:

- `backend/main.py` - main FastAPI entry used by `uvicorn backend.main:app`.
- `backend/routers` - thin API routers exposed by the main backend.
- `backend/services` - backend-level services.
- `backend/AI/app.py` - stable compatibility import for existing code.
- `backend/AI/api/monolith.py` - large existing TouristAI API implementation moved out of `app.py`.
- `backend/AI/agents` - LangGraph/agent implementations.
- `backend/AI/services` - AI workflow services.
- `backend/AI/rag` - RAG search, vector store, official tourism ingestion.
- `backend/AI/routes` - travel/calendar route implementation used by the AI API.
- `backend/AI/repositories` - persistence/repository code.

Common command:

```powershell
python -m uvicorn backend.main:app --reload
```

## Archive

`archive/legacy-frontend-js/`

Old JSX frontend prototype moved here so it does not look like a second active frontend app.

## RAG Knowledge

Official tourism pages are listed in:

`backend/AI/rag/sources/official_tourism_sources.json`

Ingest them safely with:

```powershell
python backend\AI\rag\admin_ingest.py --sources backend\AI\rag\sources\official_tourism_sources.json
```

The ingestion script merges by default and does not replace the current FAISS store unless `--replace` is passed.
