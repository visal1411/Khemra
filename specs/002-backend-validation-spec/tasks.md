# Tasks: Cloud Storage Validation & Ingestion Security

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Branch**: `002-backend-validation-spec` | **Status**: In Progress  

---

## Phase 1: Storage Origin Whitelist Setup

**Purpose**: Configure domain whitelisting to guarantee files originate from company-authorized S3 / Cloud storage.

- [x] T001 Define `ALLOWED_STORAGE_HOSTS` configuration in `myproject/settings.py` with `.env` override support.
- [x] T002 Update `KnowledgeSourceInputSerializer.validate_file_url` to enforce domain whitelist against `settings.ALLOWED_STORAGE_HOSTS`.

---

## Phase 2: File Security & Extension Gatekeepers

**Purpose**: Block executable files, scripts, and media-type mismatches.

- [x] T003 Implement `DANGEROUS_EXTENSIONS` blacklist (`.exe`, `.bat`, `.cmd`, `.sh`, `.php`, `.bin`, `.dll`) in `KnowledgeInputSerializer.py`.
- [x] T004 Implement `ALLOWED_EXTENSIONS` mapping per `source_type` (`pdf`, `video`, `text`) in `KnowledgeInputSerializer.py`.
- [x] T005 Implement `_validate_remote_url_signature` for HTTP Range (`Range: bytes=0-15`) magic byte sniffing (`%PDF-` and anti-`MZ` check).

---

## Phase 3: Search Typo Tolerance & Deduplication

**Purpose**: Ensure typos return results and duplicate uploads do not crowd out answers.

- [x] T006 Update default `threshold` from `0.30` to `0.10` in `KnowledgeSearchRequestSerializer.py` and `KnowledgeSearchService.py`.
- [x] T007 Implement search-time fingerprint deduplication by `(knowledge_title, segment_index)` and content snippet in `KnowledgeSearchService.py`.
- [x] T008 Add automated test `test_search_deduplicates_identical_segments` in `apps/rag/tests/test_KnowledgeSearchService.py`.

---

## Phase 4: Automated Verification & Unit Tests

**Purpose**: Verify all security gates and validation rules via automated test suite.

- [x] T009 Create automated test suite `apps/rag/tests/test_StorageSecurityValidation.py` covering:
  - Authorized S3 storage link passes validation.
  - Unauthorized domain link is rejected with `400 Bad Request`.
  - Executable link (`.exe`) is rejected with `400 Bad Request`.
  - Spoofed remote file (non-PDF named as `.pdf`) is caught via HTTP Range sniffing.
- [x] T010 Run test suite via Docker: `docker compose exec -T web python manage.py test apps.rag.tests.test_StorageSecurityValidation`.

