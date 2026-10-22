# Phase 1 Data Model & Schemas: Cloudflare R2 Presigned Direct Upload

**Feature**: Cloudflare R2 Presigned Direct Upload  
**Date**: 2026-10-21  

---

## 1. Entities & Data Structures

Because this feature provides a stateless signature gateway for object storage, no new database tables or database migrations are required. The state is represented in request and response schemas and configuration models.

### A. PresignedUploadRequest (Inbound Query Parameters)
Passed via HTTP query parameters to `GET /api/rag/storage/presigned-url/`.

| Field | Type | Required | Description | Example |
| :--- | :--- | :---: | :--- | :--- |
| `filename` | `string` | **Yes** | Original filename including extension. Must have an extension. | `"employee_handbook.pdf"` |
| `file_type` | `string` | **Yes** | MIME type of the file. | `"application/pdf"` |
| `folder` | `string` | No | Target folder prefix in bucket. Defaults to `"documents"`. | `"documents"`, `"videos"` |

#### Validation Rules:
- `filename`:
  - Must not be empty.
  - Extension must be extracted via `os.path.splitext(filename)[1].lower()`.
  - Must NOT be in `DANGEROUS_EXTENSIONS`.
  - Allowed extensions are restricted to:
    - PDF: `.pdf`
    - Video: `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`, `.m4v`, `.mpeg`, `.mpg`
    - Text: `.txt`, `.md`, `.json`, `.csv`, `.log`
- `file_type`:
  - Must not be empty.
  - Cannot contain newline or control characters.

---

### B. PresignedUploadResponse (Outbound JSON Payload)
Returned by `GET /api/rag/storage/presigned-url/` upon successful generation.

```json
{
  "upload_url": "https://<account-id>.r2.cloudflarestorage.com/<bucket>/documents/<uuid>.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&...",
  "file_url": "https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev/documents/<uuid>.pdf",
  "key": "documents/<uuid>.pdf",
  "expires_in": 600
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `upload_url` | `string` | Temporary S3/R2 presigned HTTP PUT URL signed with AWS SigV4. Valid for 600 seconds. |
| `file_url` | `string` | Permanent public or CDN read URL for the object. This is passed to `POST /api/rag/knowledge/`. |
| `key` | `string` | Unique storage object key in Cloudflare R2 bucket. Format: `{folder}/{uuid4}{ext}`. |
| `expires_in` | `integer` | Number of seconds until `upload_url` expires (default: `600`). |

---

## 2. Configuration Model (`settings.py` / `.env`)

```python
R2_ACCOUNT_ID: str           # Cloudflare Account ID (32 hex chars)
R2_ACCESS_KEY_ID: str       # R2 API Token Access Key ID
R2_SECRET_ACCESS_KEY: str   # R2 API Token Secret Access Key
R2_BUCKET_NAME: str         # Cloudflare R2 Bucket name
R2_PUBLIC_DOMAIN: str       # Custom domain or pub-*.r2.dev domain
R2_ENDPOINT_URL: str        # Formatted: https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com
```

---

## 3. Storage Object Key Structure

```
<bucket_root>/
└── <folder>/                      # e.g., "documents" or "videos"
    └── <uuid4>.<extension>         # e.g., "7d5e4b2a-19c8-4f70-9b36-1e646271a39f.pdf"
```

- Guarantees zero collisions between different files uploaded with the same base name.
- Eliminates directory traversal risk by ignoring path segments in user-supplied `filename`.
