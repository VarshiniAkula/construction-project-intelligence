# Construction Project Intelligence (Local MVP)

This repo is a **local-run, full‑stack MVP** for a Construction Project Intelligence web app:
- **Multi-project workspaces** (each project is isolated via membership + project_id scoping)
- **Role-based access control (RBAC)** (PM, Architect, Engineer, Subcontractor, Owner, Inspector)
- **Document upload + versioning**
- **Searchable document library** (TF‑IDF semantic-ish search by default; optional OpenAI/embedding upgrades)
- **AI Assistant (RAG-style)**: asks questions, retrieves relevant document snippets, and answers with citations
- **RFI Intelligence (starter)**: CSV import, simple phase/issue classification, entity extraction (heuristics)
- **Analytics dashboard (starter)**: RFI aging, recurring issues, trade risk indicators

> This MVP implements the foundation described in the provided spec (construction-specific AI agent, project workspaces, RFI intelligence, analytics, RBAC). It is designed so you can extend the NLP models, BIM/clash detection, schedule/budget engines, and add real-time updates later.

---

## 1) Easiest way (recommended): Run with Docker

### Prereqs
- Docker Desktop (Mac/Windows) or Docker Engine (Linux)

### Steps
```bash
# 1) unzip the project
cd construction-project-intelligence

# 2) create env file
cp .env.example .env

# 3) (optional) put your OpenAI key in .env
# OPENAI_API_KEY=...

# 4) start everything
docker compose up --build
```

### Open the app
- Frontend (website): http://localhost:5173
- Backend API docs (Swagger): http://localhost:8000/docs

---

## 2) Run without Docker (developer mode)

### Backend (FastAPI)
```bash
cd backend

python -m venv .venv
# mac/linux:
source .venv/bin/activate
# windows (powershell):
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# uses SQLite by default if DATABASE_URL is not set
uvicorn app.main:app --reload --port 8000
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Open: http://localhost:5173

---

## 3) Default accounts & data
- Create your own user via **Register**.
- Create a project, upload documents, then use the **Assistant** tab.
- Sample CSVs exist in `scripts/sample_data/`.

---

## 4) Notes on “AI”
The assistant works in two modes:
1. **OpenAI mode (recommended)**: set `OPENAI_API_KEY` in `.env`.
2. **Local fallback**: if no key is set, the assistant returns an answer derived from retrieved document snippets (no external API calls).

---

## 5) Folder structure
- `backend/` FastAPI + SQLAlchemy + JWT + ingestion + analytics
- `frontend/` React + Vite dashboard UI
- `scripts/sample_data/` example CSVs

---

## 6) Next upgrades (already scaffolded)
- Replace heuristic RFI classification with a fine‑tuned transformer classifier
- Replace heuristic NER with a spaCy custom NER pipeline
- Add BERTopic topic modeling for RFIs
- Add schedule critical path parsing & forecasting
- Add BIM/IFC clash detection rules
