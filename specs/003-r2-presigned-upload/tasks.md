# Tasks: Cloudflare R2 Presigned Direct Upload

**Branch**: `003-r2-presigned-upload` | **Date**: 2026-10-21 | **Plan**: [plan.md](./plan.md)  
**Status**: Ready to Implement  

---

## Task List

- [x] **T001: Add `boto3` to dependencies**
  - File: `requirements.txt`
  - Action: Add `boto3==1.35.0` to `requirements.txt` and install into web container.

- [x] **T002: Configure Cloudflare R2 settings in `myproject/settings.py`**
  - File: `myproject/settings.py`
  - Action: Define `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_DOMAIN`, `R2_ENDPOINT_URL` with `.env` fallbacks. Ensure `R2_PUBLIC_DOMAIN` is included in `ALLOWED_STORAGE_HOSTS`.

- [x] **T003: Implement `StorageService` for R2 presigned URLs**
  - File: `apps/rag/services/StorageService.py`
  - Action: Create `StorageService` class adhering to Constitution Principle I (One Class Per File). Initialize `boto3` S3 client with Cloudflare R2 endpoint and `s3v4` signature. Implement `generate_presigned_upload_url(filename, content_type, folder="documents", expires_in=600)`.
  - Export: Add `StorageService` to `apps/rag/services/__init__.py`.

- [x] **T004: Implement `PresignedUrlAPI` view**
  - File: `apps/rag/views/PresignedUrlAPI.py`
  - Action: Create `PresignedUrlAPI(APIView)` with `get(request)`. Validate `filename` and `file_type`. Block dangerous extensions (`.exe`, `.sh`, `.bat`, etc.). Delegate generation to `StorageService`. Return 200 JSON response with `upload_url`, `file_url`, `key`, `expires_in`.
  - Export: Add `PresignedUrlAPI` to `apps/rag/views/__init__.py`.

- [x] **T005: Register route in `apps/rag/urls.py`**
  - File: `apps/rag/urls.py`
  - Action: Add `path("storage/presigned-url/", PresignedUrlAPI.as_view(), name="storage-presigned-url")`.

- [x] **T006: Write automated unit tests with offline mocks**
  - File: `apps/rag/tests/test_StorageService.py`
  - Action: Implement test suite using `unittest.mock.patch` for `boto3.client`. Test happy path for PDF and video, dangerous extension rejection (`.exe`), missing parameters, and key UUID uniqueness.

- [x] **T007: Run test suite & verify 100% pass**
  - Command: `docker compose exec -T web python manage.py test apps.rag.tests.test_StorageService`
  - Verify all 5 tests pass with zero regressions.
