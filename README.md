# BuildDocs AI

**Role-aware construction document intelligence platform.** Upload project documents (drawings, specs, RFIs, submittals, daily reports, meeting minutes, safety docs, change orders), process them automatically, and chat with them. Every answer is grounded in your project documents with citations. Role-based access control ensures each team member sees only what they should.

**Live:** [constructionrag.vercel.app](https://constructionrag.vercel.app) | **API:** [builddocs-api.vercel.app](https://builddocs-api.vercel.app)

---

## Tech Stack

### Frontend
- **Next.js 15** with App Router
- **React 19** + TypeScript
- **Tailwind CSS** + **shadcn/ui** (Radix UI primitives)
- **TanStack Query v5** for server state management
- **React Hook Form** + **Zod** for form validation
- **react-pdf** for in-browser PDF viewing
- **react-dropzone** for drag-and-drop document uploads

### Backend
- **FastAPI** (Python) — async REST API
- **Supabase** — PostgreSQL database + file storage + auth via PostgREST
- **Pydantic v2** + **pydantic-settings** for config and validation
- **pypdf** for lightweight PDF text extraction (serverless-compatible)
- **python-docx** / **openpyxl** for Word and Excel parsing
- **httpx** for async HTTP

### AI & RAG Pipeline
- **Groq** (free-tier LLM) — `llama-3.1-8b-instant` for chat answers
- **Smart Extractive Q&A** — TF-IDF sentence scoring fallback (no API key needed)
- **Keyword-based retrieval** with multi-term search and relevance scoring
- **Keyword reranker** with position-aware scoring
- Supports **Anthropic Claude** and **OpenAI-compatible** endpoints as alternatives

### Deployment
- **Vercel** — serverless deployment for both frontend and Python API
- **Supabase** — managed PostgreSQL + object storage (no self-hosted infra needed)

---

## Architecture

```
apps/
  web/          Next.js 15 + Tailwind + shadcn/ui        (Vercel)
  api/          FastAPI + Supabase + RAG pipeline         (Vercel Python)
```

```
Browser  -->  Next.js (Vercel)  --rewrites-->  FastAPI (Vercel Serverless)
                                                   |
                                               Supabase
                                            (PostgreSQL + Storage)
                                                   |
                                            Groq / Extractive Q&A
```

---

## Quick Start

### Option 1: Use the deployed app

1. Go to [constructionrag.vercel.app](https://constructionrag.vercel.app)
2. Register an account
3. Create a project
4. Upload construction documents (PDF, DOCX, XLSX, CSV)
5. Chat with your documents

### Option 2: Local development

#### Prerequisites
- Python 3.12+
- Node.js 20+
- A Supabase project (free tier works)

#### 1. Clone and configure
```bash
git clone <repo-url>
cd construction-project-intelligence
cp .env.example .env
# Edit .env with your Supabase credentials
```

#### 2. Start the API
```bash
cd apps/api
pip install -r requirements.txt -r requirements-local.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Start the frontend
```bash
cd apps/web
npm install
npm run dev
```

#### 4. Open the app
- **Web UI:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

---

## Environment Variables

### Required (API)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `SECRET_KEY` | JWT signing secret (random 64-char string) |

### Optional (AI)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | LLM provider: `groq`, `anthropic`, or `openai` |
| `GROQ_API_KEY` | — | Free API key from [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model to use |
| `EMBEDDING_PROVIDER` | `local` | `local` (fastembed) or `api` |

> Without a `GROQ_API_KEY`, chat uses smart extractive Q&A — TF-IDF sentence scoring that extracts and ranks the most relevant sentences from your documents. It works well for factual lookups.

---

## Document Ingestion Pipeline

1. Upload file to Supabase Storage
2. Create document record (status: `processing`)
3. Extract text — **pypdf** for PDFs, **python-docx** for Word, **openpyxl** for Excel
4. Create document pages with extracted text
5. Type-aware chunking (drawings, specs, RFIs, daily reports, general)
6. Store chunks in PostgreSQL with metadata (batch inserts for speed)
7. Mark document as `ready`

Optimized for Vercel's 10-second serverless limit with batch inserts (50 at a time) and lightweight dependencies (~15MB bundle vs 350MB+ with ML libraries).

## Chat / RAG Pipeline

1. Authenticate user, resolve project role + trade scope
2. Build keyword search filters (project + allowed visibility scopes)
3. Multi-keyword search across document chunks (top 3 longest query terms)
4. Falls back to document pages if no chunks exist
5. Rerank candidates with position-aware keyword scoring
6. Generate answer with Groq LLM or extractive Q&A fallback
7. Return answer + citations + confidence score

---

## Roles & Access Control

| Role | Visibility Scopes | Upload | Chat | Manage Members |
|------|-------------------|--------|------|----------------|
| Admin | All | All types | All docs | Yes |
| Project Manager | All | All types | All docs | Yes |
| Superintendent | project_full, field_team, trade_scoped, owner_shared | Daily reports, safety, general | Accessible docs | No |
| Subcontractor | field_team, trade_scoped (own trade) | Submittals, RFIs, general | Own trade docs | No |
| Owner / Viewer | owner_shared | None | owner_shared docs | No |

Restricted documents are never leaked. If a user asks about content in inaccessible docs, the system responds that there is not enough accessible documentation.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login (sets httponly cookies) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Project detail |
| GET | `/api/projects/{id}/members` | List members |
| POST | `/api/projects/{id}/members` | Add member |
| PATCH | `/api/projects/{id}/members/{mid}` | Update member role |
| GET | `/api/projects/{id}/documents` | List documents (RBAC-filtered) |
| POST | `/api/projects/{id}/documents/upload` | Upload document |
| GET | `/api/projects/{id}/documents/{did}` | Document detail + pages |
| GET | `/api/projects/{id}/documents/{did}/download` | Download original file |
| POST | `/api/projects/{id}/documents/{did}/reprocess` | Reprocess stuck document |
| GET | `/api/projects/{id}/chat/sessions` | List chat sessions |
| POST | `/api/projects/{id}/chat/sessions` | Create chat session |
| GET | `/api/projects/{id}/chat/sessions/{sid}` | Session messages |
| POST | `/api/projects/{id}/chat/sessions/{sid}/messages` | Send message (RAG) |
| GET | `/api/projects/{id}/audit` | Audit log |

---

## Project Structure

```
apps/api/
  api/index.py               Vercel serverless entry point
  app/
    main.py                  FastAPI app + CORS
    config.py                Pydantic settings
    deps.py                  Dependency injection (Supabase client, auth)
    api/                     Route handlers (auth, projects, documents, chat)
    schemas/                 Pydantic request/response models
    services/                Business logic (ingestion, chat, storage, audit)
    ai/                      LLM providers, embeddings, reranker, generator
    retrieval/               Hybrid search (keyword + vector)
    rbac/                    Role-based access control filters
    shared_roles.py          Role/permission definitions
  requirements.txt           Lightweight deps for Vercel (<50MB)
  requirements-local.txt     Heavy ML deps for local dev (fastembed, pymupdf)
  vercel.json                Vercel build config

apps/web/
  src/
    app/                     Next.js App Router pages
    components/              React + shadcn/ui components
    lib/                     API client, auth helpers, utils
    hooks/                   TanStack Query data-fetching hooks
  next.config.ts             API rewrites to backend
```

---

## Development Notes

### Requirements split
- `requirements.txt` — lightweight for Vercel serverless (pypdf, ~15MB bundle)
- `requirements-local.txt` — full-featured local dev (pymupdf, fastembed, uvicorn, pytest)

### Auth
- Cookie-based JWT with `httponly`, `samesite=lax`, `secure=true` in production
- Access tokens (12h) + refresh tokens (7d)

### Supported file types
PDF, DOCX, XLSX, CSV, PNG, JPG
