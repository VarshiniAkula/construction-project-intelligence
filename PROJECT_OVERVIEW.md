# Construction Project Intelligence — Project Overview

A role-aware Retrieval-Augmented Generation (RAG) platform for construction projects. Teams upload drawings, specifications, RFIs, submittals, daily reports, and other project documents. A chat assistant answers questions grounded in those documents with page-level citations, while role-based visibility ensures subcontractors only see what their trade is scoped to and owners only see what's been shared with them.

> **Repo:** [VarshiniAkula/construction-project-intelligence](https://github.com/VarshiniAkula/construction-project-intelligence)
> **Live:** https://constructionrag.vercel.app

---

## 1. TL;DR

| | |
|---|---|
| **Frontend** | Next.js 15 (App Router) + React 19 + TanStack Query + Tailwind, deployed to Vercel (`web` project) at Root Directory `apps/web` |
| **Backend API** | FastAPI on Vercel Serverless (`builddocs-api` project), entrypoint `apps/api/api/index.py`, 60s function timeout, slimmed deps to fit the 250 MB lambda budget |
| **Database** | Supabase Postgres (project `dnyrppnwrclstexjlwpk` aka `builddocs-ai`); accessed from the API via the Supabase async PostgREST client (SQLAlchemy at runtime was removed; Alembic still defines the schema) |
| **Storage** | Supabase Storage, bucket `documents` |
| **Auth** | JWT (HS256) in HttpOnly cookies, bcrypt for passwords, application-layer RBAC (RLS is disabled) |
| **Ingestion** | Two paths: a **lightweight** in-process path on Vercel (text-only, no embeddings, ≤10 s) and a **full** Celery worker path for local/Docker (PDF rendering, VLM, embeddings → Qdrant) |
| **RAG** | Hybrid retrieval — pgvector dense search when embeddings exist + keyword fallback + cross-encoder reranking; LLM provider is pluggable (Groq, Anthropic, OpenAI-compatible) |
| **Worker** | `apps/worker` exists with full Celery + Qdrant + MinIO pipeline but is **not deployed in production** — only used in local Docker compose |
| **Demo data** | Seeded project `RCC-2025` (Riverside Commercial Complex, Portland OR) with 5 users covering each role and a small `test_doc.pdf` fixture |

---

## 2. System Architecture

```
                      ┌──────────────────────────────────────────────────┐
                      │  Browser                                          │
                      │  https://constructionrag.vercel.app               │
                      └──────────────────┬───────────────────────────────┘
                                         │ cookies (access_token, refresh_token)
                                         ▼
                  ┌─────────────────────────────────────────────────┐
                  │  Vercel — project: web (Next.js 15, App Router) │
                  │  Root Directory: apps/web                       │
                  │                                                  │
                  │  next.config.ts rewrites:                        │
                  │    /api/:path*  → ${API_BACKEND_URL}/api/:path*  │
                  │    /health      → ${API_BACKEND_URL}/health      │
                  └──────────────────┬───────────────────────────────┘
                                     │  HTTPS, credentials: include
                                     ▼
                  ┌─────────────────────────────────────────────────┐
                  │  Vercel — project: builddocs-api (FastAPI)      │
                  │  Entrypoint: apps/api/api/index.py              │
                  │  All requests rewritten to api/index.py         │
                  │  maxDuration: 60s, single serverless function   │
                  │                                                  │
                  │  ┌─────────────────────────────────────────────┐│
                  │  │ Routers (mounted under /api):                ││
                  │  │  auth, projects, documents, chat,            ││
                  │  │  members, audit                              ││
                  │  └─────────────────────────────────────────────┘│
                  │                                                  │
                  │  Lightweight ingestion runs in-process here     │
                  │  (text extract → chunk → insert; no embeddings) │
                  └────────┬───────────────────────────┬────────────┘
                           │                           │
                           ▼                           ▼
              ┌─────────────────────────┐   ┌────────────────────────────┐
              │ Supabase Postgres        │   │ Supabase Storage           │
              │ (project: builddocs-ai)  │   │ bucket: documents          │
              │                          │   │                            │
              │ users, projects,         │   │ projects/{pid}/documents/  │
              │ project_memberships,     │   │   {doc_id}/original{ext}   │
              │ documents, document_pages│   │   {doc_id}/page-N.png      │
              │ document_chunks (+vec),  │   └────────────────────────────┘
              │ chat_sessions,           │
              │ chat_messages, audit_logs│
              └──────────────────────────┘

                  ┌─────────────────────────────────────────────────┐
                  │  External LLM / VLM (one of):                   │
                  │   • Groq          llama-3.1-8b-instant (default)│
                  │   • Anthropic     claude-sonnet-4-20250514      │
                  │   • OpenAI-compat (LLM_BASE_URL / LLM_API_KEY)  │
                  └─────────────────────────────────────────────────┘

   ── Local docker-compose only (NOT in production) ──────────────────
   ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐
   │ apps/worker      │  │ Redis        │  │ Qdrant       │  │ MinIO  │
   │ (Celery + fast-  │◀─┤ broker       │  │ vector store │  │ S3-API │
   │ embed + pymupdf) │  │              │  │              │  │        │
   └──────────────────┘  └──────────────┘  └──────────────┘  └────────┘
```

Two execution profiles run the same FastAPI codebase against different ingestion paths. On Vercel the API runs `ingest_document_lightweight` synchronously in-request; in Docker compose the API enqueues a Celery task that runs the full pipeline (PDF rendering at 150 DPI, optional vision model, fastembed embeddings, Qdrant upsert) on `apps/worker`.

---

## 3. Repository Layout

```
construction-project-intelligence/
├── apps/
│   ├── web/                       Next.js 15 frontend (deployed to Vercel)
│   │   ├── src/app/
│   │   │   ├── page.tsx           Landing page
│   │   │   ├── (auth)/login,
│   │   │   │       /register      Public auth pages
│   │   │   └── (dashboard)/
│   │   │       ├── layout.tsx     Auth-guarded shell with sidebar
│   │   │       ├── dashboard/     Project list + create modal
│   │   │       └── projects/[projectId]/
│   │   │            ├── page.tsx          Project hub (5 link cards)
│   │   │            ├── documents/        Library + viewer + upload
│   │   │            ├── chat/             RAG chat with citations
│   │   │            ├── members/          Team management
│   │   │            └── audit/            Audit log
│   │   ├── src/lib/
│   │   │   ├── api-client.ts      fetch wrapper, 401 → /login redirect
│   │   │   ├── auth-context.tsx   useAuth() provider, /auth/me on mount
│   │   │   └── utils.ts           cn(), formatters, ROLE/DOC/STATUS labels
│   │   ├── next.config.ts         /api/* rewrite to API_BACKEND_URL
│   │   └── tailwind.config.ts     Construction palette (hard-hat orange…)
│   │
│   ├── api/                       FastAPI backend (deployed to Vercel)
│   │   ├── api/index.py           Vercel serverless entrypoint
│   │   ├── app/
│   │   │   ├── main.py            FastAPI() + CORS + /api router
│   │   │   ├── config.py          Pydantic Settings, env vars
│   │   │   ├── deps.py            get_current_user, get_membership
│   │   │   ├── supabase_client.py async Supabase client singleton
│   │   │   ├── shared_roles.py    RBAC: roles, scopes, permission maps
│   │   │   ├── api/
│   │   │   │   ├── router.py      Mounts auth/projects/documents/...
│   │   │   │   ├── auth.py        register, login, logout, me
│   │   │   │   ├── projects.py    list, create, get
│   │   │   │   ├── documents.py   list, upload, get, download, reprocess,
│   │   │   │   │                   page image
│   │   │   │   ├── chat.py        sessions CRUD, send message
│   │   │   │   ├── members.py     list, add, update role
│   │   │   │   └── audit.py       list logs (admin/PM only)
│   │   │   ├── services/
│   │   │   │   ├── ingestion.py   Lightweight + full ingestion logic
│   │   │   │   ├── chat_service.py RAG orchestration
│   │   │   │   └── audit_service.py log_action()
│   │   │   ├── retrieval/
│   │   │   │   └── hybrid_search.py pgvector + keyword + reranker
│   │   │   ├── security/jwt.py    HS256 sign/verify, bcrypt
│   │   │   ├── schemas/           Pydantic request/response models
│   │   │   └── models/            Legacy SQLAlchemy ORM (Alembic only)
│   │   ├── alembic/               One migration: 001_initial_schema.py
│   │   ├── tests/                 RBAC, permissions, upload, retrieval
│   │   ├── requirements.txt       Vercel slim build (pypdf, no fastembed)
│   │   ├── requirements-full.txt  Local dev (pymupdf, fastembed, uvicorn)
│   │   └── vercel.json            Rewrites /(.*) → api/index.py, 60 s
│   │
│   └── worker/                    Celery worker (LOCAL DOCKER ONLY)
│       ├── celery_app.py          Redis broker/backend, JSON serializer
│       ├── tasks/ingest.py        Full ingestion: PDF render → VLM →
│       │                          embed → Qdrant upsert
│       ├── shared/
│       │   ├── db.py              Sync SQLAlchemy session (psycopg)
│       │   ├── minio_client.py    S3-compatible storage abstraction
│       │   └── qdrant_client.py   Vector DB client + collection setup
│       └── requirements.txt
│
├── packages/shared/               Cross-language constants
│   ├── python/roles.py            Source of truth for RBAC enums + maps
│   └── src/                       TypeScript mirrors (currently unused
│                                  by the web app — labels are duplicated
│                                  in apps/web/src/lib/utils.ts)
│
├── e2e/                           Playwright tests
│   ├── playwright.config.ts       Local config (localhost:3000)
│   ├── playwright.config.demo.ts  Production video config (slowMo + on-trace)
│   └── tests/
│       ├── admin-flow.spec.ts                Admin happy path
│       ├── subcontractor-restriction.spec.ts RBAC visibility checks
│       └── full-flow-demo.spec.ts            9-step video demo (sign-in →
│                                              project → docs → chat → audit)
│
├── infra/scripts/seed.py          Seeds 5 demo users + RCC-2025 project
├── docker-compose.yml             Local stack: postgres, redis, qdrant,
│                                   minio, api, worker, web
├── render.yaml                    Render service def (API only;
│                                   currently unused — deploys are on Vercel)
├── apps/api/render.yaml           Duplicate of the above (legacy)
├── pnpm-workspace.yaml            Workspace: apps/web + e2e
├── package.json                   Root manifest, packageManager pnpm@10.33.0
├── .env.example                   Documented env var template
├── README.md                      Top-level setup + tech stack
└── PROJECT_OVERVIEW.md            (this file)
```

---

## 4. Tech Stack

### Frontend (`apps/web`)

| Layer | Choice | Why / Notes |
|---|---|---|
| Framework | Next.js 15 (App Router) | Server components, route groups (`(auth)`, `(dashboard)`) |
| UI runtime | React 19 | Latest JSX runtime |
| Data | TanStack React Query 5 | Caching, auto-refetch every 3 s while a doc is processing |
| Forms | react-hook-form + zod | Resolver in `@hookform/resolvers` |
| Styling | Tailwind 3.4 | Custom palette (`hard-hat`, `hard-steel`, `hard-beam`, `surface-*`) |
| Components | Radix UI primitives + lucide-react | Headless, themed via Tailwind |
| File upload | react-dropzone | Multi-file, max 100 MB each, accepts PDF/DOCX/XLSX/CSV/PNG/JPG |
| PDF preview | react-pdf + pdfjs-dist | Per-page navigation with `?page=N` |
| Build | pnpm 10.33.0, Node ≥20 | Vercel runs Node 24.x |

### Backend (`apps/api`)

| Layer | Choice |
|---|---|
| Language | Python 3.10+ |
| Framework | FastAPI 0.115+ (Starlette under the hood) |
| Validation | Pydantic v2 |
| DB client | `supabase` async client → PostgREST |
| Auth | `passlib[bcrypt]` + `python-jose` (JWT HS256) |
| HTTP | `httpx` async client (LLM calls, Storage downloads) |
| PDF (slim) | `pypdf` 4 |
| PDF (full / worker) | `pymupdf` (fitz) — renders pages at 150 DPI |
| Office docs | `python-docx`, `openpyxl` |
| Embeddings (full) | `fastembed` (ONNX, BAAI/bge-small-en-v1.5, 384-dim) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Migrations | Alembic (one migration; SQLAlchemy is **not** used at runtime) |

### Worker (`apps/worker`, local only)

Celery 5 + Redis broker, Qdrant vector store, MinIO object storage, fastembed for embeddings. Concurrency 2 in Dockerfile.

### Datastores

| Store | Used for | Where |
|---|---|---|
| Supabase Postgres | All relational data + `pgvector` for chunk vectors when present | Production |
| Supabase Storage | Original files + rendered page images | Production |
| Qdrant | Vector store (worker path only) | Local Docker only |
| MinIO | S3-compatible object store for the worker path | Local Docker only |

---

## 5. Data Model

The schema is bootstrapped by a single Alembic migration: `apps/api/alembic/versions/001_initial_schema.py`. Nine tables:

```
                 ┌────────────┐
                 │  users     │
                 │  ────────  │
                 │ id (PK)    │◀─────────────────────────────────────┐
                 │ email (uq) │                                       │
                 │ password_  │                                       │
                 │   hash     │                                       │
                 │ full_name  │                                       │
                 │ company_   │                                       │
                 │   name     │                                       │
                 │ is_active  │                                       │
                 │ is_super-  │                                       │
                 │   admin    │                                       │
                 └─────┬──────┘                                       │
                       │                                              │
        ┌──────────────┴──────────────┐                              │
        ▼                             ▼                              │
┌────────────────────┐      ┌─────────────────┐                     │
│ project_memberships│      │ chat_sessions   │                     │
│ ──────────────     │      │ ─────────────── │                     │
│ user_id (FK)       │      │ user_id (FK)    │                     │
│ project_id (FK)    │      │ project_id (FK) │                     │
│ role               │      │ title           │                     │
│ assigned_trade     │      └────────┬────────┘                     │
│ UNIQUE(user, proj) │               │                              │
└──────────┬─────────┘               ▼                              │
           │                ┌────────────────────┐                  │
           ▼                │ chat_messages      │                  │
   ┌────────────────┐       │ ──────────────     │                  │
   │ projects       │       │ session_id (FK)    │                  │
   │ ────────────   │       │ role (user|asst)   │                  │
   │ id (PK)        │       │ content            │                  │
   │ name           │       │ citations_json     │                  │
   │ code (uq)      │       │ model_metadata_json│                  │
   │ location       │       └────────────────────┘                  │
   │ description    │                                                │
   └────────┬───────┘                                                │
            │                                                        │
            ▼                                                        │
   ┌─────────────────────┐         ┌──────────────────────┐         │
   │ documents           │         │ audit_logs           │         │
   │ ─────────────       │         │ ─────────────────    │         │
   │ id (PK)             │         │ user_id (FK)─────────┘
   │ project_id (FK)     │         │ project_id (FK)
   │ uploaded_by (FK)    │         │ action      (indexed)
   │ file_name           │         │ entity_type, entity_id
   │ storage_key         │         │ details_json
   │ doc_type    (idx)   │         │ created_at
   │ visibility_scope    │         └──────────────────────┘
   │ trade_scope (idx)   │
   │ revision            │
   │ status      (idx)   │ ← 'processing' | 'rendering_pages' |
   │ page_count          │   'chunking' | 'embedding' | 'ready' | 'error'
   │ processing_error    │
   │ metadata_json       │
   └────┬───────────┬────┘
        │           │
        ▼           ▼
┌───────────────┐  ┌─────────────────────────────────┐
│ document_pages│  │ document_chunks                 │
│ ────────────  │  │ ─────────────                   │
│ document_id FK│  │ document_id (FK)                │
│ page_number   │  │ page_number, chunk_index        │
│ raw_text      │  │ chunk_text                      │
│ cleaned_text  │  │ visibility_scope (idx)          │
│ page_summary  │  │ trade_scope     (idx)           │
│ image_storage_│  │ vector_id  ← FK to pgvector col │
│   key         │  │ metadata_json                   │
│ extracted_json│  └─────────────────────────────────┘
│   (VLM result)│
└───────────────┘
```

Notes:

- `documents.visibility_scope` is one of `project_full`, `field_team`, `trade_scoped`, `owner_shared`, `management_only`. RBAC uses these to filter every list/detail/retrieval query.
- `document_chunks` carries its own `visibility_scope` and `trade_scope` so the retrieval query can filter at the chunk level (a project-full document could in theory have trade-scoped chunks, though current ingestion just inherits from the parent).
- RLS is **disabled** on these tables — RBAC is purely application-layer.
- `file_size` exists on the `documents` table but is not populated at upload time today (visible bug — every row reads `0 bytes`).

---

## 6. Authentication & Authorization

### Sign-in / sign-out

```
Browser                    Next.js (web)            FastAPI (api)
   │  POST /api/auth/login      │                        │
   │  { email, password }       │ rewrite to             │
   │ ──────────────────────────▶│  ${API_BACKEND_URL}    │
   │                            │ ──────────────────────▶│
   │                            │                        │ verify bcrypt
   │                            │                        │ create JWT (HS256)
   │                            │ ◀──────────────────────│ Set-Cookie:
   │                            │                        │   access_token
   │                            │                        │   refresh_token
   │ ◀──────────────────────────│                        │   HttpOnly, Secure*,
   │                            │                        │   SameSite=Lax
   │                            │                        │   Max-Age 12h / 7d
```

`*` `Secure` flag is set automatically when `VERCEL` or `RENDER` env var is present (`apps/api/app/api/auth.py:14`).

On every subsequent request the cookie is sent (`credentials: "include"` in `apps/web/src/lib/api-client.ts:30`). The `get_current_user` dependency (`apps/api/app/deps.py:33-54`) accepts either the `access_token` cookie or an `Authorization: Bearer …` header, decodes the JWT, asserts `type=="access"`, looks up the user, and rejects inactive accounts.

On client-side mount, `AuthProvider` calls `GET /api/auth/me` to rehydrate the user; if it returns 401, the provider sets `user = null` and the `(dashboard)` layout's effect pushes the visitor back to `/login`.

### Role-based access control

There are five roles, defined in `packages/shared/python/roles.py` and mirrored in `apps/api/app/shared_roles.py` and `apps/web/src/lib/utils.ts`:

| Role | Purpose | Visibility scopes they can see |
|---|---|---|
| `admin` | Account/project administrator | All scopes |
| `project_manager` | Construction PM | All except `management_only` |
| `superintendent` | Field operations lead | `project_full`, `field_team`, `trade_scoped`, `owner_shared` |
| `subcontractor` | Trade-specific contributor | `field_team`, `trade_scoped` (filtered by `assigned_trade`) |
| `owner_viewer` | Project owner / client | `owner_shared` only |

Visibility scopes:

- `project_full` — visible to everyone on the project
- `field_team` — superintendents + subcontractors
- `trade_scoped` — subcontractors whose `assigned_trade` matches the doc's `trade_scope`
- `owner_shared` — owners + management
- `management_only` — admin + project_manager

Enforcement points:

- **`get_membership`** dependency (`apps/api/app/deps.py:57-75`) attaches role + assigned_trade to every project-scoped request and 403s non-members.
- **Document list** (`documents.py:32`) and **document fetch** (`documents.py:176`) filter by `in_("visibility_scope", allowed_scopes)`. Subcontractors get an additional in-Python pass to filter `trade_scope` against `assigned_trade`.
- **Chat retrieval** (`chat_service.py:42`) passes `allowed_scopes` and `trade_scope` into `hybrid_retrieve` so the LLM only ever sees chunks the user is entitled to.
- **Audit log** is gated by the `audit.view` permission (admin / project_manager only).

Note on superadmin: a user with `is_superadmin=true` is treated as an admin on every project regardless of `project_memberships`.

---

## 7. Document Ingestion Pipeline

The same FastAPI endpoint (`POST /api/projects/{project_id}/documents/upload`) handles uploads in both deployment modes; the difference is what runs after the file is in storage.

### Upload (common to both modes)

1. **Authorize** — RBAC permission `document.upload` checked.
2. **Validate** — extension allowed (PDF, DOCX, XLSX, CSV, PNG, JPG).
3. **Store** — file uploaded to Supabase Storage at `projects/{project_id}/documents/{doc_id}/original{ext}`.
4. **Insert** `documents` row with `status = "processing"`.
5. **Audit** — `document.upload` action logged.
6. **Dispatch** — branch on environment.

### Vercel (production) — lightweight in-process

`apps/api/app/services/ingestion.py:ingest_document_lightweight()` runs synchronously in the request that uploaded the file. To fit the 60 s function timeout and the 250 MB lambda budget:

- **No page rendering** (PIL / pymupdf are excluded from the slim build).
- **No embeddings** (fastembed is too large to bundle).
- Text extraction uses `pypdf`; DOCX/XLSX/CSV use `python-docx` / `openpyxl` / stdlib `csv`.
- Chunks are inserted into `document_chunks` with `vector_id = NULL`.
- Status transitions: `processing → chunking → ready` (no `embedding` or `rendering_pages` step).

This is why retrieval on Vercel falls back to keyword search — there are no vectors to query.

### Local Docker — full Celery pipeline

The API instead enqueues a Celery task (`apps/worker/tasks/ingest.py:ingest_document`) and the worker picks it up. The full state machine:

```
processing  ─────▶ rendering_pages  ─────▶  chunking  ─────▶  embedding  ─────▶  ready
                                                                                  │
                                       (any exception)                            │
                                              │                                   │
                                              ▼                                   │
                                            error  ◀─ processing_error stored ────┘
```

| Step | Detail |
|---|---|
| `rendering_pages` | PyMuPDF renders each PDF page to PNG at 150 DPI; uploaded to MinIO/Storage at `…/page-N.png`. Optional VLM call (`claude-sonnet-4-20250514` or OpenAI-compatible vision endpoint) extracts structured JSON describing the page. |
| `chunking` | Type-aware splitter: drawings → 1 chunk per page; specifications → split on numbered sections (regex `\n(?=\d+\.\d+[\s.])`); RFIs/submittals → single chunk (≤3000 chars); daily reports → paragraph-based, 800 char max; general → 800 chars / 100 char overlap. |
| `embedding` | `fastembed` produces 384-dim vectors (BAAI/bge-small-en-v1.5). Batched insert into `document_chunks` (50 at a time); vectors are written to the pgvector column via the `update_chunk_embedding` RPC, and a copy is upserted into Qdrant. |
| `ready` | Final state; UI auto-refetch (every 3 s while processing) settles. |

### Reprocess endpoint

`POST /api/projects/{pid}/documents/{did}/reprocess` exists to re-run chunking against already-extracted pages. It was specifically tuned to fit Vercel's previous 10 s timeout (commit `b50eebd0`); the function-level `maxDuration` is now 60 s.

---

## 8. RAG / Chat Pipeline

`POST /api/projects/{pid}/chat/sessions/{sid}/messages` orchestrates a single turn:

```
1.  Save user message            chat_messages INSERT (role='user')

2.  Compute allowed scopes       get_allowed_scopes(role)
                                 → e.g. subcontractor →
                                   ['field_team','trade_scoped']

3.  Hybrid retrieval             retrieval/hybrid_search.py
    ├─ embed_query(query)        skipped on Vercel
    ├─ pgvector dense search     filter by allowed_scopes + trade_scope
    │                            top-K = 20
    ├─ keyword fallback          ilike on chunk_text (or document_pages
    │                            if chunks unavailable); top-3 longest
    │                            non-stopword tokens
    └─ rerank top 5              cross-encoder/ms-marco-MiniLM-L-6-v2
                                 (silently returns unranked top-5 if the
                                  reranker is unavailable)

4.  Enrich with metadata         join doc.file_name onto each chunk

5.  Get conversation history     last 6 messages from this session

6.  Generate answer              services/chat_service.generate_answer
                                 → LLM provider per LLM_PROVIDER env:
                                    groq | anthropic | openai-compatible
                                 → prompt includes role hint, context
                                   chunks, history

7.  Build citations              [{ document_id, file_name, page_number,
                                    snippet (first 200 chars),
                                    relevance_score }]

8.  Save assistant reply         chat_messages INSERT
                                 (role='assistant', citations_json=…)

9.  Title the session            if first turn, set title = first 80
                                 chars of the user's question

10. Audit log                    log_action('chat.query', …)
```

The frontend chat page (`apps/web/src/app/(dashboard)/projects/[projectId]/chat/page.tsx`) shows citations as clickable chips that open a modal with the snippet and relevance score, and a "Sources" panel.

There's also a smart **extractive Q&A fallback** (commit `25e22646`): when the LLM call fails or returns an unusable response, the API stitches the top-ranked chunk text directly into the answer with `[Source N]` citations so the user always gets a grounded reply.

---

## 9. Frontend Architecture

### Routing

```
(public)
  /                                      Landing
  /login                                 Auth — login form
  /register                              Auth — sign-up form

(dashboard) — auth guard, sidebar shell
  /dashboard                             Project list + create modal
  /projects/[projectId]/                 Project hub (5 link cards)
              ├─ documents/              Library (search + filters)
              │   ├─ [docId]             Single-doc viewer (?page=N)
              │   └─ upload              react-dropzone + form
              ├─ chat/                   RAG chat with citations
              ├─ members/                Team management
              └─ audit/                  Audit log
```

### Key client primitives

- **`AuthProvider`** (`src/lib/auth-context.tsx`) — calls `/auth/me` on mount, exposes `user`, `loading`, `login`, `register`, `logout`.
- **`api`** (`src/lib/api-client.ts`) — fetch wrapper with `credentials: "include"`. Throws a typed `ApiError(message, status)`. **Globally redirects to `/login` on 401** unless the request was an `/auth/*` endpoint.
- **`(dashboard)/layout.tsx`** — auth guard + dark sidebar with logo, nav, and a sign-out button at the bottom (`useAuth().logout`). Note: the sidebar does not contain per-project nav; sub-pages reach each other by URL (the project hub is the central hub).

### Auto-refetch for processing docs

The library page (`documents/page.tsx`) and the single-doc viewer (`documents/[docId]/page.tsx`) re-run their queries every 3 s as long as any visible doc has `status` in `{processing, chunking, embedding, rendering_pages, extracting_text, vlm_processing}`. This delivers a near-real-time feel without a websocket.

### Theming

Tailwind palette in `tailwind.config.ts` defines a construction-themed palette:

- `hard-hat #E87722` (safety orange — primary CTAs)
- `hard-steel #4A6FA5` (secondary accents)
- `hard-concrete #8B8B8B`
- `hard-slate #2D3748`
- `hard-beam #1A202C` (sidebar / nav background)
- `surface-{paper,muted,border}` for content surfaces
- `status-{approved,pending,rejected,processing}` for badges

Component classes (`.btn-primary`, `.card`, `.input-field`, `.badge-*`) are defined in `globals.css`.

---

## 10. Backend API Reference

All endpoints are mounted at `/api`. CORS allows `localhost:3000`, `127.0.0.1:3000`, and any `*.vercel.app` origin (regex), with credentials enabled.

### Auth — `app/api/auth.py`

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create user; sets cookies; returns `TokenResponse` |
| POST | `/api/auth/login` | Verify bcrypt password; sets cookies |
| POST | `/api/auth/logout` | Clears cookies |
| GET | `/api/auth/me` | Current user profile (requires cookie) |

> Refresh-token rotation is not currently implemented as an explicit endpoint; the access token simply expires after 12 h and the user re-logs in.

### Projects — `app/api/projects.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects` | Projects the caller is a member of |
| POST | `/api/projects` | Create project; caller becomes admin member |
| GET | `/api/projects/{id}` | Project + member/doc counts |

### Documents — `app/api/documents.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects/{pid}/documents` | List with `search`, `doc_type`, `status` filters; RBAC-filtered |
| POST | `/api/projects/{pid}/documents/upload` | Multipart upload + start ingestion |
| GET | `/api/projects/{pid}/documents/{did}` | Doc + all `document_pages` |
| GET | `/api/projects/{pid}/documents/{did}/download` | Stream the original file |
| GET | `/api/projects/{pid}/documents/{did}/pages/{n}/image` | Stream rendered PNG |
| POST | `/api/projects/{pid}/documents/{did}/reprocess` | Re-chunk from existing pages |

### Chat — `app/api/chat.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects/{pid}/chat/sessions` | Caller's sessions in this project |
| POST | `/api/projects/{pid}/chat/sessions` | Create session |
| GET | `/api/projects/{pid}/chat/sessions/{sid}` | All messages in session |
| POST | `/api/projects/{pid}/chat/sessions/{sid}/messages` | Send a question; returns assistant reply + citations |

### Members — `app/api/members.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects/{pid}/members` | List members |
| POST | `/api/projects/{pid}/members` | Add member by email; assign role + trade |
| PATCH | `/api/projects/{pid}/members/{mid}` | Update role / trade |

### Audit — `app/api/audit.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects/{pid}/audit` | Filterable audit log (admin / PM only) |

Tracked actions today: `auth.register`, `auth.login`, `project.create`, `document.upload`, `document.view`, `member.add`, `member.update`, `chat.query`.

### Health

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | `{"status":"ok"}` (also rewritten through the web project) |

---

## 11. Deployment Topology

There are three operational modes:

### A. Production — Vercel + Supabase (the live app)

| Component | Where |
|---|---|
| Frontend `web` | Vercel project `web`, Root Directory `apps/web`, framework Next.js, Node 24.x |
| Backend `builddocs-api` | Vercel project `builddocs-api`, single serverless function `api/index.py`, `maxDuration: 60` |
| Postgres + pgvector | Supabase project `dnyrppnwrclstexjlwpk` (`builddocs-ai`) |
| Storage | Supabase bucket `documents` |
| Worker | **Not deployed** — the lightweight in-process pipeline runs in the same Vercel function as the upload endpoint |
| LLM | Groq by default; Anthropic available via env var |

The frontend is a pnpm workspace. The repo root has `package.json`, `pnpm-workspace.yaml`, and `pnpm-lock.yaml` so Vercel's monorepo install works (`cd ../.. && pnpm install --frozen-lockfile`). The web project's Root Directory is `apps/web`.

### B. Local development — Docker compose

`docker-compose.yml` brings up the full stack including the worker:

| Service | Image | Port |
|---|---|---|
| postgres | postgres:16-alpine | 5432 |
| redis | redis:7-alpine | 6379 |
| qdrant | qdrant/qdrant:v1.12.6 | 6333, 6334 |
| minio | minio/minio | 9000, 9001 |
| minio-init | minio/mc | — (creates the bucket) |
| api | Dockerfile.api | 8000 (runs `alembic upgrade head` then uvicorn) |
| worker | Dockerfile.worker | — (Celery, concurrency 2) |
| web | Dockerfile.web | 3000 |

Local dev gets the **full** ingestion pipeline (rendering + VLM + embeddings + Qdrant) because all the heavy deps are available outside Vercel's lambda budget.

### C. Render — declared but unused

Both `render.yaml` and `apps/api/render.yaml` define a single `builddocs-api` Python web service. Neither is currently the live deployment; they're vestigial from an earlier plan. The README still mentions Render as one option for the API.

### CI/CD

There is no `.github/workflows/` directory. Deploys today rely on Vercel's GitHub integration (push to `main` → auto-deploy of both projects); tests are run manually with `pnpm test:demo` against production.

---

## 12. Configuration

The full template lives in `.env.example`. Key variables grouped by service:

### Backend API (`apps/api`)

```
APP_ENV=production
SECRET_KEY=<random 64-char>           JWT signing key
DATABASE_URL=postgresql+asyncpg://…   Supabase pooler URL
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service role>   server-only, all-access
SUPABASE_STORAGE_BUCKET=documents
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://<frontend>"]

# LLM provider selection
LLM_PROVIDER=groq                     groq | anthropic | openai-compatible
GROQ_API_KEY=…
GROQ_MODEL=llama-3.1-8b-instant
ANTHROPIC_API_KEY=…                   optional
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_VISION_MODEL=claude-sonnet-4-20250514

EMBEDDING_PROVIDER=local              local | openai-compatible
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384

RERANKER_PROVIDER=local
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Auto-set on Vercel/Render → makes cookies Secure
VERCEL=1                              (set by Vercel runtime)
```

### Frontend (`apps/web`)

```
API_BACKEND_URL=https://builddocs-api.vercel.app   server-side rewrite target
NEXT_PUBLIC_API_URL=                               (optional; usually empty so
                                                    fetch hits same-origin /api/*)
```

### Worker (`apps/worker`, local Docker only)

```
REDIS_URL=redis://redis:6379/0
DATABASE_URL_SYNC=postgresql+psycopg://…
STORAGE_BACKEND=minio                  local | minio
MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
QDRANT_MODE=host                       memory | host
QDRANT_HOST=qdrant
QDRANT_PORT=6333
ANTHROPIC_API_KEY                      optional, for VLM
VLM_BASE_URL, VLM_API_KEY, VLM_MODEL   alternate VLM endpoint
```

### E2E (`e2e/`)

```
E2E_BASE_URL=https://constructionrag.vercel.app
E2E_ADMIN_EMAIL=admin@builddocs.ai
E2E_ADMIN_PASSWORD=builddocs123
E2E_PROJECT_NAME="Riverside Commercial Complex"
E2E_PROJECT_CODE=RCC-2025
E2E_DEMO_QUESTION="What documents are in this project…"
```

---

## 13. Local Development

```bash
# 1. Bring up the full stack
cp .env.example .env
docker compose up --build

# 2. Seed demo users + the RCC-2025 project
docker compose exec api python -m infra.scripts.seed

# 3. Open the apps
open http://localhost:3000          # Next.js
open http://localhost:8000/docs     # FastAPI Swagger
```

Demo accounts (all use password `builddocs123`):

| Email | Role | Trade |
|---|---|---|
| admin@builddocs.ai | admin | — |
| sarah.pm@example.com | project_manager | — |
| mike.super@example.com | superintendent | — |
| jose.electrical@example.com | subcontractor | electrical |
| owner@riverside.com | owner_viewer | — |

---

## 14. Testing

### Backend (`apps/api/tests/`)

| File | Coverage |
|---|---|
| `test_rbac.py` | `ROLE_VISIBILITY_MAP`, `ROLE_PERMISSIONS` lookups |
| `test_permissions_filter.py` | Document visibility filtering by role |
| `test_upload_states.py` | Document status state machine |
| `test_chat_retrieval.py` | Hybrid search + retrieval pipeline |

Run with `pytest` from `apps/api` after installing `requirements-full.txt`.

### End-to-end (`e2e/`)

Three Playwright specs:

1. **`admin-flow.spec.ts`** — login → project → docs / members / audit / chat (smoke).
2. **`subcontractor-restriction.spec.ts`** — confirms a subcontractor login cannot see a `management_only` document and an `owner_viewer` cannot see field-only docs.
3. **`full-flow-demo.spec.ts`** — 9-step happy-path that records a video; targets production by default. Run via:

   ```bash
   pnpm --filter builddocs-e2e install-browsers   # one-time
   pnpm --filter builddocs-e2e test:demo
   pnpm --filter builddocs-e2e show-report
   ```

   The demo config (`e2e/playwright.config.demo.ts`) records `video.webm` + `trace.zip` at 1280×800 with `slowMo: 250` for human-watchable pacing. Convert to MP4 with:

   ```bash
   ffmpeg -i e2e/test-results/*/video.webm -c:v libx264 -crf 23 -preset slow \
     -pix_fmt yuv420p -movflags +faststart demo-flow.mp4
   ```

### CI

There is currently **no CI**. Tests are run manually.

---

## 15. Known Issues & Tech Debt

These are real things to be aware of when working on the codebase:

1. **Vercel deploys keyword-only RAG.** `fastembed` is excluded to fit the lambda budget; on production every chunk has `vector_id = NULL`, so retrieval falls back to keyword `ilike` over `chunk_text`. Quality on complex queries is weaker than the local Docker stack would deliver. Mitigation options: switch to a hosted embedding API (OpenAI, Voyage), or move ingestion off Vercel onto a long-running worker (Render Background Worker, Fly Machines, Cloud Run).
2. **`document.file_size` is not populated.** Every row reads `0 bytes`. The upload handler doesn't set it.
3. **Many uploaded documents are stuck in `chunking`.** Looking at the live DB, several user-uploaded files in non-seeded projects never advanced past `chunking`. This is from earlier ingestion runs that errored without writing to `processing_error`. Reprocess via `POST /api/projects/{pid}/documents/{did}/reprocess` to clear them.
4. **No refresh-token endpoint.** The 12-hour access token expiry just kicks the user back to `/login`. Either implement `/api/auth/refresh` or extend `ACCESS_TOKEN_EXPIRE_MINUTES`.
5. **Trade-scope filtering happens in Python, not SQL.** `apps/api/app/api/documents.py:54-61` post-filters subcontractor results in-process. Fine for small projects, won't scale to thousands of docs per project.
6. **Project name uniqueness is not enforced.** Two projects named "Riverside Commercial Complex" exist in the live DB (codes `RCC-2025` and `RVSD-COMM`). The Playwright demo had to disambiguate by code.
7. **The worker is undeployed.** `apps/worker` is fully implemented but has no production target. Either wire it up (Render Background Worker is the natural fit given `render.yaml` already exists) or delete it to reduce confusion.
8. **`render.yaml` is duplicated** at the repo root and at `apps/api/render.yaml` with slightly different `PYTHONPATH`s. Pick one.
9. **Two `.vercel/` artifacts** in the repo (one at root from an earlier link, one we created at `apps/web`). Both are gitignored, but local `vercel pull` can drift from production env vars.
10. **The seeded admin password hash needed manual reset.** A bcrypt hash mismatch (almost certainly from a SECRET_KEY rotation interacting with an older hash format) made the `seed.py` admin unable to log in until reset directly via SQL. Future seed runs should be idempotent and use a fresh hash each time.
11. **RLS is disabled** on every public table. If any other system gets direct DB access (Supabase Studio, an MCP client, a misconfigured anon key), it can read everything. RBAC is purely application-layer right now. Worth turning on RLS with a service-role bypass policy if you ever expose anon credentials.
12. **TypeScript `packages/shared/src/`** mirrors the Python role/scope enums but is **not** imported by `apps/web` — the web app duplicates the labels in `src/lib/utils.ts`. Wire it up or delete it.
13. **No `.github/workflows/`.** No automated lint, test, or deploy. Worth adding at minimum a Playwright run on PRs.
14. **Reranker failure is silent.** `apps/api/app/retrieval/hybrid_search.py:175` swallows reranker exceptions and returns the raw top-5. There's no telemetry indicating the reranker was bypassed.

---

## 16. Operational Runbook

### "Deployment failed on Vercel"

Recent classes of failure encountered in this repo:

- **`ERR_PNPM_NO_PKG_MANIFEST  No package.json found in /`** — the root needs `package.json` + `pnpm-workspace.yaml`. Already fixed; do not delete those files.
- **"No Next.js version detected"** — the web project's Root Directory in Vercel must be set to `apps/web`. Check Project Settings → Build & Deployment.
- **Auto-deploys not firing** — verify Settings → Git is connected and the production branch is `main`. Empty commits won't trigger when the change is outside the Root Directory; touch a file under `apps/web/`.

### "Login returns 500 Internal Server Error"

The Supabase project paused (free-tier inactivity → DNS doesn't resolve). Restore from the Supabase dashboard or via MCP `restore_project`. The `/health` endpoint stays green even when the DB is paused, so check `POST /api/auth/login` instead.

### "Login returns 401 with the documented seed password"

The bcrypt hash for the seeded admin doesn't match. Reset via SQL:

```sql
UPDATE users
SET password_hash = crypt('builddocs123', gen_salt('bf', 12)),
    updated_at = NOW()
WHERE email = 'admin@builddocs.ai';
```

(Or compute a hash with `python -c "import bcrypt; print(bcrypt.hashpw(b'builddocs123', bcrypt.gensalt(rounds=12)).decode())"` and update that.)

### "A document is stuck in `chunking` forever"

Either the original ingestion crashed before writing `processing_error`, or it succeeded but the status update silently failed. Hit `POST /api/projects/{pid}/documents/{did}/reprocess` to retry from existing pages.

### "Chat returns garbage / empty answers"

Likely the LLM provider isn't configured. Verify `LLM_PROVIDER` and the matching `*_API_KEY` env var are set in the `builddocs-api` Vercel project. The extractive Q&A fallback should keep answers grounded even on LLM failure, but if no chunks are retrieved (keyword-only on Vercel + no matching tokens) the response will be sparse.

---

## 17. Glossary

| Term | Meaning |
|---|---|
| **RBAC** | Role-Based Access Control. Implemented in `app/shared_roles.py` + `packages/shared/python/roles.py` |
| **Visibility scope** | Per-document tag controlling who sees it: `project_full`, `field_team`, `trade_scoped`, `owner_shared`, `management_only` |
| **Trade scope** | The trade (e.g. `electrical`, `concrete`) a `trade_scoped` doc is restricted to |
| **VLM** | Vision Language Model. Used in the worker pipeline to parse rendered PDF page images into structured JSON |
| **Reranker** | A cross-encoder that re-orders the top-K retrieved chunks by relevance to the query |
| **Lightweight ingestion** | Vercel-only path: text-only, no embeddings, no page rendering |
| **Full ingestion** | Worker path: full PDF render, optional VLM, embeddings + Qdrant |
| **Hybrid retrieval** | Vector (pgvector) + keyword (`ilike`) + reranker pipeline in `app/retrieval/hybrid_search.py` |
