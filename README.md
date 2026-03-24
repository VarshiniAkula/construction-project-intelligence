# BuildDocs AI

**Role-aware construction document chatbot.** Upload project documents (drawings, specs, RFIs, submittals, daily reports, meeting minutes, safety docs, change orders), index them with AI, and chat with them. Every answer is grounded in your project documents with citations. Access control ensures each role sees only what they should.

---

## Architecture

```
apps/
  web/       Next.js 15 + Tailwind + shadcn/ui      (port 3000)
  api/       FastAPI + SQLAlchemy 2 + Alembic        (port 8000)
  worker/    Celery worker for document ingestion
packages/
  shared/    Shared types, RBAC definitions (TS + Python)
infra/       Dockerfiles, docker-compose, seed script
e2e/         Playwright end-to-end tests
```

**AI Stack (non-negotiable):**
- Final answers: `mistralai/Mistral-Small-3.2-24B-Instruct-2506`
- Ingestion VLM: `Qwen/Qwen2.5-VL-7B-Instruct`
- Embeddings: `BAAI/bge-m3` (1024-dim)
- Reranker: `BAAI/bge-reranker-v2-m3`

**Infrastructure:** PostgreSQL, Redis, Qdrant, MinIO

---

## Quick Start

### Prerequisites
- Docker & Docker Compose

### 1. Clone and configure
```bash
cd construction-project-intelligence
cp .env.example .env
# Edit .env to set AI model endpoints if you have them running
```

### 2. Start all services
```bash
docker compose up --build
```

This starts: PostgreSQL, Redis, Qdrant, MinIO, API, Worker, Web

### 3. Run database migrations and seed data
```bash
# Migrations run automatically on API startup

# Seed demo data
docker compose exec api python /app/../infra/scripts/seed.py
# Or run locally:
cd infra/scripts && python seed.py
```

### 4. Open the app
- **Web UI:** http://localhost:3000
- **API docs:** http://localhost:8000/docs
- **MinIO console:** http://localhost:9001 (minioadmin/minioadmin)
- **Qdrant dashboard:** http://localhost:6333/dashboard

---

## Demo Accounts

All passwords: `builddocs123`

| Email | Role | Access |
|-------|------|--------|
| `admin@builddocs.ai` | Admin | Full platform access |
| `sarah.pm@example.com` | Project Manager | Full project access |
| `mike.super@example.com` | Superintendent | Field docs, no management_only |
| `jose.electrical@example.com` | Subcontractor | Electrical trade docs only |
| `owner@riverside.com` | Owner / Viewer | Read-only, owner_shared docs only |

---

## MVP Roles & Access Control

| Role | Visibility Scopes | Upload | Chat | Manage Members |
|------|-------------------|--------|------|----------------|
| Admin | All | All types | All docs | Yes |
| Project Manager | All | All types | All docs | Yes |
| Superintendent | project_full, field_team, trade_scoped, owner_shared | Daily reports, safety, general | Accessible docs | No |
| Subcontractor | field_team, trade_scoped (own trade) | Submittals, RFIs, general | Own trade docs | No |
| Owner / Viewer | owner_shared | None | owner_shared docs | No |

**Critical rule:** Restricted documents are never leaked. If a user asks about content in inaccessible docs, the system responds that there is not enough accessible documentation.

---

## Document Ingestion Pipeline

1. Upload file to MinIO
2. Create document record (status: `processing`)
3. Render PDF pages to images (PyMuPDF)
4. Extract raw text
5. VLM page understanding (Qwen2.5-VL) for scanned pages, drawings, tables
6. Produce structured metadata (doc_type, title, revision, trade, etc.)
7. Type-aware chunking (drawings, specs, RFIs, reports, general)
8. Generate BGE-M3 embeddings
9. Upsert to Qdrant with metadata payload
10. Mark document as `ready`

## Chat / RAG Pipeline

1. Authenticate user, resolve project role + trade
2. Build Qdrant filter (project + allowed scopes + trade)
3. Embed query with BGE-M3
4. Hybrid search: dense retrieval, top-20 candidates
5. Rerank with BGE-reranker-v2-m3, top-5
6. Generate answer with Mistral-Small-3.2 (strict grounding prompt)
7. Return answer + citations + confidence

---

## AI Model Endpoints

All models use OpenAI-compatible endpoints. Configure in `.env`:

```env
LLM_BASE_URL=http://your-mistral-server:8081/v1
VLM_BASE_URL=http://your-qwen-vl-server:8082/v1
EMBEDDING_BASE_URL=http://your-embedding-server:8083/v1
RERANKER_BASE_URL=http://your-reranker-server:8084/v1
```

You can use vLLM, text-generation-inference, text-embeddings-inference, or any OpenAI-compatible server.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Project detail |
| GET | `/api/projects/{id}/members` | List members |
| POST | `/api/projects/{id}/members` | Add member |
| PATCH | `/api/projects/{id}/members/{mid}` | Update member |
| GET | `/api/projects/{id}/documents` | List documents (RBAC-filtered) |
| POST | `/api/projects/{id}/documents/upload` | Upload document |
| GET | `/api/projects/{id}/documents/{did}` | Document detail |
| GET | `/api/projects/{id}/documents/{did}/download` | Download |
| GET | `/api/projects/{id}/documents/{did}/pages/{pn}/image` | Page image |
| GET | `/api/projects/{id}/chat/sessions` | List chat sessions |
| POST | `/api/projects/{id}/chat/sessions` | Create session |
| GET | `/api/projects/{id}/chat/sessions/{sid}` | Session messages |
| POST | `/api/projects/{id}/chat/sessions/{sid}/messages` | Send message |
| GET | `/api/projects/{id}/audit` | Audit log |

---

## Testing

### Backend tests
```bash
cd apps/api
pip install -r requirements.txt
pytest tests/ -v
```

### E2E tests
```bash
cd e2e
npm install
npx playwright install
npx playwright test
```

---

## Project Structure

```
apps/api/
  app/
    main.py              FastAPI app
    config.py            Pydantic settings
    deps.py              Dependency injection
    models/              SQLAlchemy models
    schemas/             Pydantic schemas
    api/                 Route handlers
    services/            Business logic
    ai/                  AI provider adapters
    retrieval/           Qdrant + hybrid search
    rbac/                Role-based access control
  alembic/               Database migrations
  tests/                 Pytest tests

apps/worker/
  worker/
    celery_app.py        Celery configuration
    tasks/ingest.py      Document ingestion pipeline
    shared/              DB, MinIO, Qdrant clients

apps/web/
  src/
    app/                 Next.js App Router pages
    components/          React components
    lib/                 API client, auth, utils
    hooks/               TanStack Query hooks

packages/shared/
  python/roles.py        Shared role/visibility definitions
```

---

## Development

### Local development without Docker
```bash
# Start infrastructure
docker compose up postgres redis qdrant minio minio-init -d

# API
cd apps/api
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Worker
cd apps/worker
celery -A worker.celery_app worker --loglevel=info

# Frontend
cd apps/web
npm install
npm run dev
```
