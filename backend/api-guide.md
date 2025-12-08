# Jalsetu Backend API Guide

Base URL prefix: `/api/`

Auth: JWT (SimpleJWT). Send `Authorization: Bearer <access_token>` on all protected routes (DRF default trailing slash is enabled).

Modules covered:
- Accounts (`/api/auth/`)
- Ingestion (`/api/ingestion/`)
- Indexing (`/api/indexes/`)
- Chats (`/api/` -> projects, chat-sessions, chat-messages)

---

## Accounts (`/api/auth/`)

- `POST /api/auth/login/`
  - Body: `{ "username": "...", "password": "..." }`
  - Response: `{ "access": "...", "refresh": "...", "must_change_password": bool, "user": { id, username, email, role, login_count } }`
- `POST /api/auth/token/refresh/`
  - Body: `{ "refresh": "..." }`
  - Response: `{ "access": "..." }`
- `GET /api/auth/me/`
  - Auth: required.
  - Response: user profile fields (id, username, email, first_name, last_name, role, department, access_expires_at, login_count).
- `PATCH /api/auth/me/`
  - Auth: required.
  - Body: `{ "first_name": "...", "last_name": "...", "department": "..." }`
- `POST /api/auth/change-password/`
  - Auth: required.
  - Body: `{ "old_password": "...", "new_password": "..." }`
- Onboarding requests (`/api/auth/onboarding-requests/`)
  - `POST /` - Auth required. Body: `{ "email": "...", "full_name": "...", "requested_role": "...", "department": "..." }`
  - `GET /` - SUPER_ADMIN only. Lists all requests.
  - `GET /{id}/` - SUPER_ADMIN only. Detail.
  - `POST /{id}/decide/` - SUPER_ADMIN only. Body: `{ "action": "APPROVE"|"REJECT", "remark": "..." }`; approval creates the user and emails a temp password (console backend in dev).

---

## Ingestion (`/api/ingestion/`)

- `POST /api/ingestion/upload/`
  - Roles: `SENIOR_ANALYST` or `SUPER_ADMIN`.
  - Content-Type: `multipart/form-data`.
  - Fields: `title` (required), `description` (optional), `classification` (`PUBLIC|RESTRICTED|CONFIDENTIAL|TOP_SECRET`), `file` (pdf, docx, txt, jpg/jpeg/png, audio: wav/mp3/m4a/flac/ogg/aac/wma/opus/webm/mp4). Unsupported types return a 400 validation error.
  - Response 201: `{ document_id, version_id, job_id, job_status, doc_status }`
  - Notes: Processing runs inline; expect longer latency. OCR/Whisper/CLIP applied when available; audio uses Whisper when present and stores chunks/segments, otherwise a placeholder message is saved.
- `GET /api/ingestion/jobs/{job_id}/`
  - Auth: required.
  - Response: `{ id, status (PENDING|RUNNING|COMPLETED|FAILED), error_message, created_at, started_at, finished_at }`

---

## Indexing (`/api/indexes/`)

- `POST /api/indexes/rebuild/`
  - Roles: `SUPER_ADMIN` or `IT_ADMIN`.
  - Body: `{ "modality": "text"|"image"|"audio", "mode": "full"|"incremental" (default "full"), "notes": "..." }`
  - Response 201: `{ "message": "...", "snapshot": { id, name, modality, version, index_path, id_mapping_path, doc_count, is_active, built_at, built_by, notes } }`
- `GET /api/indexes/snapshots/`
  - Auth: required.
  - Query: optional `?modality=text|image|audio`.
  - Response: list of snapshot objects (same fields as above), newest first.

---

## Chats (`/api/`)

All routes require authentication; querysets are scoped to projects where the user is a member.

- Projects (`/api/projects/`)
  - CRUD via DRF router.
  - Fields: `name`, `description`, `members` (list of user IDs), `is_archived`. `owner` auto-set to the creator and added to `members`.
- Chat sessions (`/api/chat-sessions/`)
  - CRUD within accessible projects.
  - Fields: `project`, `title`, `status` (`ACTIVE|CLOSED`). `created_by` auto-set; `last_activity_at` updates on new messages.
- Chat messages (`/api/chat-messages/`)
  - CRUD within sessions the user can see.
  - Fields: `session`, `role` (`USER|ASSISTANT|SYSTEM`), `content`, `metadata` (JSON, optional). `sender` auto-set for USER messages; assistant/system messages keep `sender=null`.
