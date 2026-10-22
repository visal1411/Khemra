# Quickstart & Validation Guide: Cloudflare R2 Presigned Direct Upload

**Feature**: Cloudflare R2 Presigned Direct Upload  
**Date**: 2026-10-21  

This guide provides end-to-end validation scenarios for testing the presigned URL workflow locally and against live Cloudflare R2 storage.

---

## 1. Automated Offline Test Suite

Run the isolated test suite inside Docker:

```bash
docker compose exec -T web python manage.py test apps.rag.tests.test_StorageService
```

Expected output:
```text
Found 5 test(s).
Creating test database for alias 'default'...
.....
----------------------------------------------------------------------
Ran 5 tests in 0.350s

OK
Destroying test database for alias 'default'...
```

---

## 2. Manual Verification Scenarios (cURL / Postman)

### Scenario A: Request Presigned URL for PDF (Happy Path)

```bash
curl -X GET "http://localhost:8000/api/rag/storage/presigned-url/?filename=handbook.pdf&file_type=application/pdf"
```

**Expected Response (`200 OK`)**:
```json
{
  "upload_url": "https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.cloudflarestorage.com/my-bucket/documents/3c7b2a51-....pdf?X-Amz-...",
  "file_url": "https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev/documents/3c7b2a51-....pdf",
  "key": "documents/3c7b2a51-....pdf",
  "expires_in": 600
}
```

---

### Scenario B: Upload File to Cloudflare R2 via Presigned URL

Using the `upload_url` returned from Scenario A:

```bash
curl -X PUT "<upload_url>" \
  -H "Content-Type: application/pdf" \
  --data-binary "@test_document.pdf"
```

**Expected Response**: `HTTP/1.1 200 OK` (Empty body from Cloudflare R2).

---

### Scenario C: Complete Ingestion with Existing RAG API

Now submit the `file_url` to the Knowledge upload endpoint:

```bash
curl -X POST "http://localhost:8000/api/rag/knowledge/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Employee Handbook 2026",
    "source_type": "pdf",
    "sources": [
      {
        "language": "en",
        "file_url": "https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev/documents/3c7b2a51-....pdf"
      }
    ],
    "segments": [
      {
        "segment_index": 0,
        "title": "Welcome and Overview",
        "page_start": 1,
        "page_end": 2
      }
    ]
  }'
```

**Expected Response**: `HTTP/1.1 201 Created`

---

### Scenario D: Security Rejections (Negative Tests)

#### 1. Dangerous Executable Rejection:
```bash
curl -X GET "http://localhost:8000/api/rag/storage/presigned-url/?filename=virus.exe&file_type=application/x-msdownload"
```
**Expected Response**: `400 Bad Request`
```json
{
  "error": "Forbidden file extension '.exe'. Executable and script files are strictly blocked."
}
```

#### 2. Missing Parameters:
```bash
curl -X GET "http://localhost:8000/api/rag/storage/presigned-url/"
```
**Expected Response**: `400 Bad Request`
```json
{
  "error": "Both 'filename' and 'file_type' query parameters are required."
}
```
