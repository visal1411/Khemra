# Implementation Plan: Cloudflare R2 Presigned Direct Upload

**Branch**: `003-r2-presigned-upload` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/003-r2-presigned-upload/spec.md`  

---

## 1. Summary

Implement a presigned URL generation gateway for direct client-to-storage uploads using Cloudflare R2 and Python `boto3`. 

The architecture strictly follows Constitution Principle I (Single Responsibility & Strict File Layout) by dividing responsibilities cleanly:
- `apps/rag/services/StorageService.py`: Handles S3-compatible client initialization, AWS SigV4 presigned PUT generation, and collision-proof object key assignment.
- `apps/rag/views/PresignedUrlAPI.py`: The HTTP API controller that validates query parameters, executes malware extension filtering, and returns JSON.
- `apps/rag/tests/test_StorageService.py`: Isolated unit test suite mocking `boto3` for fast, offline verification.

---

## 2. Technical Context

- **Language/Version**: Python 3.11+, Django 5.1.3, Django REST Framework 3.15.2.
- **Primary Dependencies**: `boto3==1.35.0`, `botocore==1.35.0`.
- **Cloud Storage**: Cloudflare R2 (S3-compatible API with AWS Signature Version 4).
- **Target Protocol**: HTTP GET for presigned URL issuance; HTTP PUT for direct browser-to-R2 upload.
- **Testing**: Django test runner (`python manage.py test`) with `unittest.mock` for offline execution.
- **Performance Goals**: Presigned URL generation response time $< 50\text{ms}$; 0 bytes of binary media buffered in Django RAM.
- **Security Constraints**: Strict rejection of executable and dangerous extensions (`.exe`, `.bat`, `.cmd`, `.sh`, `.php`, `.py`, `.bin`, etc.).

---

## 3. Constitution Check

*GATE: Must pass before implementation.*

| Principle | Compliance Assessment | Status |
| :--- | :--- | :---: |
| **I. Single Responsibility & Strict File Layout (One Class Per File)** | `StorageService` lives in `apps/rag/services/StorageService.py`. `PresignedUrlAPI` lives in `apps/rag/views/PresignedUrlAPI.py`. No business logic in views. No mixing of concerns. | **PASSED** |
| **II. Lightweight & Deterministic ML Runtime** | No ML frameworks or PyTorch touched. `fastembed` remains untouched. | **PASSED** |
| **III. Multi-Signal & Granular Embedding Strategy** | Existing embedding strategy unaffected. Ingests URL into `KnowledgeSource`. | **PASSED** |
| **IV. Test-Driven & Isolated Test Double Coverage** | Complete test double coverage using `unittest.mock.patch` for `boto3`. Zero live network calls during tests. Runs in $< 1\text{s}$. | **PASSED** |
| **V. Relational & Vector Hybrid Rigor** | No database changes needed. Preserved UUID and relational constraints in `Knowledge` models. | **PASSED** |

---

## 4. Project Structure & Code Layout

```text
d:\Khemra Backend\my-django-dockerv2\
├── requirements.txt                              # Add boto3==1.35.0
├── myproject/
│   └── settings.py                               # Add R2 configuration keys
├── apps/
│   └── rag/
│       ├── services/
│       │   ├── StorageService.py                 # [NEW] Cloudflare R2 boto3 integration
│       │   └── __init__.py                       # Export StorageService
│       ├── views/
│       │   ├── PresignedUrlAPI.py                # [NEW] HTTP GET endpoint handler
│       │   └── __init__.py                       # Export PresignedUrlAPI
│       ├── urls.py                               # Register path("storage/presigned-url/", ...)
│       └── tests/
│           └── test_StorageService.py            # [NEW] Unit test suite with offline mocks
└── specs/
    └── 003-r2-presigned-upload/
        ├── spec.md                               # Feature specification
        ├── plan.md                               # This implementation plan
        ├── research.md                           # Phase 0 research findings
        ├── data-model.md                         # Schemas & configurations
        ├── quickstart.md                         # Validation & testing guide
        ├── contracts/
        │   └── presigned-url.json                # JSON schema contract
        └── checklists/
            └── requirements.md                   # Spec quality checklist
```

---

## 5. Implementation Phases & Tasks

### Phase 1: Environment & Dependencies
1. Add `boto3==1.35.0` to `requirements.txt`.
2. Add R2 storage settings to `myproject/settings.py` (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_DOMAIN`, `R2_ENDPOINT_URL`).
3. Ensure `pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev` is registered in `ALLOWED_STORAGE_HOSTS`.

### Phase 2: Service Layer (`StorageService.py`)
1. Create `apps/rag/services/StorageService.py`.
2. Implement `__init__` with lazy or configured `boto3.client("s3", endpoint_url=..., config=Config(signature_version="s3v4"))`.
3. Implement `generate_presigned_upload_url(filename, content_type, folder="documents", expires_in=600)`.
4. Sanitize extension, generate UUID key, sign PUT URL, build public `file_url`.
5. Export `StorageService` in `apps/rag/services/__init__.py`.

### Phase 3: View & Routing Layer (`PresignedUrlAPI.py`)
1. Create `apps/rag/views/PresignedUrlAPI.py`.
2. Implement parameter validation (`filename`, `file_type`).
3. Enforce dangerous extension blacklist.
4. Call `StorageService.generate_presigned_upload_url`.
5. Return JSON response (`upload_url`, `file_url`, `key`, `expires_in`).
6. Register route in `apps/rag/urls.py` (`path("storage/presigned-url/", PresignedUrlAPI.as_view(), name="storage-presigned-url")`).
7. Export `PresignedUrlAPI` in `apps/rag/views/__init__.py`.

### Phase 4: Automated Testing (`test_StorageService.py`)
1. Create `apps/rag/tests/test_StorageService.py`.
2. Test Case 1: Successful presigned URL generation for PDF (`upload_url`, `file_url`, `key`).
3. Test Case 2: Successful presigned URL generation for video (`.mp4`).
4. Test Case 3: Rejection of dangerous executable (`.exe`, `.sh`).
5. Test Case 4: Rejection of missing `filename` or `file_type`.
6. Test Case 5: UUID collision prevention across identical filenames.
7. Run `docker compose exec -T web python manage.py test apps.rag.tests.test_StorageService`.

---

## 6. Complexity Tracking

No constitution violations detected. Standard service-view architecture implemented with zero extra abstraction layers.
