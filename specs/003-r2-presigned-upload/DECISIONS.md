# Architecture Decision Record: Cloudflare R2 Presigned Uploads

**Document**: Architecture Decision Record (ADR-003)  
**Status**: Accepted & Implemented  
**Date**: 2026-10-21  
**Feature**: Cloudflare R2 Presigned Direct Upload  
**Relevant Code**:
- [`apps/rag/services/StorageService.py`](../../apps/rag/services/StorageService.py)
- [`apps/rag/views/PresignedUrlAPI.py`](../../apps/rag/views/PresignedUrlAPI.py)
- [`apps/rag/urls.py`](../../apps/rag/urls.py)
- [`apps/rag/tests/test_StorageService.py`](../../apps/rag/tests/test_StorageService.py)

---

## 1. Context & Problem Statement

The Knowledge RAG platform accepts large enterprise media files (multi-page PDF documents and high-definition video walkthroughs) to parse and generate vector embeddings.

Streaming multi-megabyte and multi-gigabyte binary files through the Django application server introduces serious production hazards:
1. **Gunicorn Worker Starvation**: Synchronous web workers remain blocked while receiving slow uploads, causing HTTP `504 Gateway Timeout` for all other API consumers.
2. **Memory & CPU Spikes**: Buffering large binary streams inside the Django container risks out-of-memory crashes (`OOMKilled`).
3. **Double Bandwidth Costs**: Server incurs egress/ingress network transfer costs twice (client $\to$ Django, Django $\to$ cloud storage).

---

## 2. Decision: Direct-to-Storage Upload with Presigned URLs

We decided to implement the **Presigned Upload URL** pattern using **Cloudflare R2** and Python `boto3`.

### The Handshake Workflow:
```
1. Frontend requests upload ticket:
   GET /api/rag/storage/presigned-url/?filename=guide.pdf&file_type=application/pdf

2. Backend validates file type, blocks dangerous files (.exe), and returns:
   {
     "upload_url": "https://<account>.r2.cloudflarestorage.com/...",
     "file_url": "https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev/documents/<uuid>.pdf",
     "key": "documents/<uuid>.pdf",
     "expires_in": 600
   }

3. Frontend sends binary directly to R2:
   PUT [upload_url] (Body: raw File binary)

4. Frontend submits knowledge metadata & file_url to RAG ingestion:
   POST /api/rag/knowledge/
```

---

## 3. Key Architectural Decisions Made

### Decision 1: Use HTTP `PUT` over HTTP `POST`
- **Chosen**: S3 Presigned `PUT` (`ClientMethod="put_object"`).
- **Rationale**: `PUT` allows the frontend (Web/Mobile) to upload the raw binary payload directly in the HTTP request body (`fetch(upload_url, { method: 'PUT', body: file })`). Presigned `POST` requires complex multi-part form field ordering which increases frontend integration friction.

### Decision 2: UUID Object Keying (Zero Collision & Anti-Traversal)
- **Chosen**: Store objects under `{folder}/{uuid4}{ext}` (e.g. `documents/3c7b2a51-....pdf`).
- **Rationale**: User-supplied filenames are never used as storage keys. This completely eliminates:
  - File overwrites when two users upload `handbook.pdf`.
  - Directory traversal attacks (`../../etc/passwd`).

### Decision 3: Defense-in-Depth Security (Pre-Upload Gate)
- **Chosen**: Block malicious extensions (`.exe`, `.bat`, `.cmd`, `.sh`, `.php`, `.py`, `.bin`, `.dll`, `.apk`, etc.) at the presigned URL endpoint.
- **Rationale**: Untrusted clients are prevented from even obtaining an upload ticket to the bucket. Combined with the post-upload validation in `KnowledgeInputSerializer` (domain whitelist + remote magic byte sniffing), the platform achieves two independent security checkpoints.

### Decision 4: Constitution Compliance (One Class Per File & Service Layer)
- **Chosen**:
  - `StorageService.py`: Encapsulates pure Cloudflare R2 / S3 client operations and URL signing.
  - `PresignedUrlAPI.py`: Dedicated APIView handling HTTP parameters, status codes, and error formatting.
- **Rationale**: Adheres to Constitution Principle I. Business logic never leaks into views, and `StorageService` can be reused in Celery workers, scripts, or test fixtures.

### Decision 5: Deterministic Offline Testing
- **Chosen**: Mock `boto3.client` using `unittest.mock.patch` in `test_StorageService.py`.
- **Rationale**: Tests run completely offline in $< 20\text{ms}$ without requiring live Cloudflare network calls or credentials, satisfying Constitution Principle IV.

---

## 4. Configuration Reference

In `myproject/settings.py` and `.env`:

| Setting | Value / Fallback | Purpose |
| :--- | :--- | :--- |
| `R2_ACCOUNT_ID` | `os.environ` | Cloudflare Account Identifier |
| `R2_ACCESS_KEY_ID` | `os.environ` | R2 API Token Access Key |
| `R2_SECRET_ACCESS_KEY` | `os.environ` | R2 API Token Secret Key |
| `R2_BUCKET_NAME` | `"my-khemra-bucket"` | Target R2 Storage Bucket |
| `R2_PUBLIC_DOMAIN` | `"pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev"` | Public CDN / R2.dev access host |
| `R2_ENDPOINT_URL` | `https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com` | S3 API endpoint for boto3 |
