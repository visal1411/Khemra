# Upload Endpoint Validation & Security Reference Guide

This document details all security checks, business rules, and input validations implemented for the Knowledge Upload API (`POST /api/rag/knowledge/`), along with practical testing instructions.

---

## Table of Contents
1. [Endpoint Overview & Architecture](#1-endpoint-overview--architecture)
2. [Security & Validation Layers](#2-security--validation-layers)
   - [Layer 1: Document Header Validation](#layer-1-document-header-validation)
   - [Layer 2: Segment Business Logic](#layer-2-segment-business-logic)
   - [Layer 3: URL Protocol & Domain Whitelist](#layer-3-url-protocol--domain-whitelist)
   - [Layer 4: Extension & Dangerous File Blocking](#layer-4-extension--dangerous-file-blocking)
   - [Layer 5: Remote Storage Existence (404/403 Guardrail) & Magic Byte Sniffing](#layer-5-remote-storage-existence-404403-guardrail--magic-byte-sniffing)
3. [Error Response Catalog](#3-error-response-catalog)
4. [Step-by-Step Testing Guide](#4-step-by-step-testing-guide)
   - [Option A: Automated Docker Test Suite](#option-a-automated-docker-test-suite)
   - [Option B: Manual Testing with Postman or cURL](#option-b-manual-testing-with-postman-or-curl)

---

## 1. Endpoint Overview & Architecture

* **Endpoint:** `POST /api/rag/knowledge/`
* **Content-Type:** `application/json`
* **Role:** Ingests document/media metadata, source links, and segment transcripts into PostgreSQL with vector embeddings.

### Cloud Storage Upload Workflow:
```
[ User (Web / Mobile) ]
         │
         │ 1. Picks file via UI file picker
         ▼
[ Cloud Storage (R2 / S3) ] ──▶ 2. File stored securely via PUT upload_url
         │
         │ 3. CDN returns public URL: "https://pub-...r2.dev/video.mp4"
         ▼
[ Django Backend ] ──────────▶ 4. Receives POST /api/rag/knowledge/ with URL
                                  • Verifies storage domain whitelist
                                  • Verifies file extension compatibility
                                  • Verifies file EXISTS in R2 (HTTP 200/206 vs 404/403)
                                  • Sniffs first 16 bytes (blocks malware & 0 bytes)
                                  • Saves to DB & creates vector embeddings
```

---

## 2. Security & Validation Layers

### Layer 1: Document Header Validation
* **Non-Empty Title (`validate_title`):**
  * Cannot be blank or whitespace-only (e.g. `"   "`).
  * Maximum length: `500` characters.
  * Auto-trims leading/trailing whitespace.
* **Valid Source Type (`source_type`):**
  * Must be one of: `'pdf'`, `'video'`, `'text'`.

---

### Layer 2: Segment Business Logic
* **Minimum One Segment:**
  * Payload must provide at least one segment chunk in `segments` or `knowledge_segments`.
* **Unique Segment Index:**
  * Every segment must have a unique `segment_index` (e.g. `0`, `1`, `2`, ...). Duplicates are rejected.
* **Chronological Video Timestamps:**
  * `start_time_seconds` must be $\le$ `end_time_seconds`.
* **Chronological PDF Pages:**
  * `page_start` must be $\le$ `page_end`.

---

### Layer 3: URL Protocol & Domain Whitelist
* **Protocol Guard:**
  * URLs must begin with `http://` or `https://`.
  * Blocks dangerous URI schemes like `ftp://`, `file://`, or `javascript:`.
* **Storage Origin Whitelist (`ALLOWED_STORAGE_HOSTS`):**
  * Verifies that the URL host matches authorized cloud domains configured in `settings.py` (e.g., `pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev`, `r2.cloudflarestorage.com`, `s3.amazonaws.com`).
  * Rejects random external links from unapproved websites.

---

### Layer 4: Extension & Dangerous File Blocking
* **Malware & Script Blacklist (`DANGEROUS_EXTENSIONS`):**
  * Immediately blocks any URL ending in:
    `.exe`, `.bat`, `.cmd`, `.sh`, `.php`, `.py`, `.bin`, `.dll`, `.apk`, `.msi`, `.vbs`, `.scr`, `.com`
* **Media Type Compatibility (`ALLOWED_EXTENSIONS`):**
  * Matches URL file extension against the declared `source_type`:
    * **`pdf`**: only allows `.pdf`
    * **`video`**: allows `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`, `.m4v`, `.mpeg`, `.mpg`
    * **`text`**: allows `.txt`, `.md`, `.json`, `.csv`, `.log`

---

### Layer 5: Remote Storage Existence (404/403 Guardrail) & Magic Byte Sniffing
* **What it does:**
  * When a public cloud URL is provided, the backend issues an HTTP range request (`Range: bytes=0-15`) to verify the file on Cloudflare R2 / S3 before writing anything to PostgreSQL.
* **What it catches (The Ghost Record Guardrail):**
  1. **Non-Existent File (HTTP 404):** If the frontend calls `POST /api/rag/knowledge/` before the `PUT` upload finishes, or if the cloud upload failed, the backend detects `404 Not Found` and **immediately rejects the request**. This prevents broken "ghost" videos/PDFs from ever polluting your database!
  2. **Access Forbidden (HTTP 403):** Catches misconfigured private bucket permissions.
  3. **Empty File (0 bytes):** Rejects any file with `Content-Length: 0` or empty payload.
  4. **Disguised Malware (.exe renamed to .pdf):** Inspects the first 2 bytes. If they start with `b'MZ'` (the Windows executable header), it **immediately blocks the upload**.
  5. **Fake PDF Files:** For `pdf` sources, it confirms the file header begins with `b'%PDF-'`.

---

## 3. Error Response Catalog

When validation fails, the API returns **`400 Bad Request`** with clear, descriptive JSON errors:

| Trigger Scenario | HTTP Status | Error Response Payload |
| :--- | :---: | :--- |
| **File Not Found in R2 (404)** | `400` | `{"sources": "Remote file at 'https://...r2.dev/...' does not exist (HTTP 404 Not Found). The file upload to Cloudflare R2 must complete successfully before submitting knowledge metadata."}` |
| **Storage Access Denied (403)** | `400` | `{"sources": "Access denied to remote file at 'https://...r2.dev/...' (HTTP 403 Forbidden). Please ensure the file was uploaded and is publicly accessible via the storage CDN."}` |
| **Empty File (0 bytes)** | `400` | `{"sources": "Remote file at '...' for language 'en' is empty (0 bytes). Uploaded files must not be empty."}` |
| **Dangerous Executable** | `400` | `{"sources": {"0": {"file_url": ["Forbidden file extension '.exe'. Executable and script files are strictly blocked."]}}}` |
| **Unauthorized Domain** | `400` | `{"sources": {"0": {"file_url": ["Unauthorized storage domain 'evil.com'. Files must be hosted on authorized cloud storage."]}}}` |
| **Mismatched Media Type** | `400` | `{"sources": "URL extension '.mp4' for language 'en' does not match expected source type 'pdf'."}` |
| **Fake PDF Header** | `400` | `{"sources": "Invalid PDF file at URL for language 'en'. Remote file does not begin with '%PDF-'."}` |
| **Inverted Timestamps** | `400` | `{"segments": {"start_time_seconds": "start_time_seconds cannot be greater than end_time_seconds"}}` |
| **Inverted Page Numbers** | `400` | `{"segments": {"page_start": "page_start cannot be greater than page_end"}}` |
| **Duplicate Languages** | `400` | `{"sources": "Duplicate languages found in sources. Each source must have a unique language."}` |
| **Duplicate Segment Indices** | `400` | `{"segments": "Duplicate segment_index found. Each segment must have a unique segment_index."}` |
| **Missing Segments** | `400` | `{"segments": "At least one segment must be provided in 'segments' or 'knowledge_segments'."}` |
| **Empty Title** | `400` | `{"title": ["Title cannot be empty or whitespace only."]}` |

---

## 4. Step-by-Step Testing Guide

### Option A: Automated Docker Test Suite (Instant Verification)

Run the automated test suite inside your Docker container:

```bash
docker compose exec -T web python manage.py test apps.rag.tests.test_StorageSecurityValidation
```

**Expected Output:**
```text
Found 4 test(s).
Creating test database for alias 'default'...
....
----------------------------------------------------------------------
Ran 4 tests in 1.041s

OK
Destroying test database for alias 'default'...
```

---

### Option B: Manual Testing with Postman or cURL

Use the following test cases in Postman against `http://localhost:8000/api/rag/knowledge/`:

---

#### Test 1: Valid S3 Document Upload (Happy Path)
```http
POST /api/rag/knowledge/
Content-Type: application/json
```
```json
{
  "title": "AWS Architecture Handbook",
  "source_type": "pdf",
  "sources": [
    {
      "language": "en",
      "file_url": "https://s3.amazonaws.com/handbook.pdf"
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Cloud Overview",
      "summary": "Introduction to cloud architecture.",
      "page_start": 1,
      "page_end": 10
    }
  ]
}
```
* **Expected Result:** `201 Created`

---

#### Test 2: Attack Attempt - Dangerous Executable File (`.exe`)
```json
{
  "title": "Malware Test",
  "source_type": "pdf",
  "sources": [
    {
      "language": "en",
      "file_url": "https://s3.amazonaws.com/malware.exe"
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Test"
    }
  ]
}
```
* **Expected Result:** `400 Bad Request`  
  `"Forbidden file extension '.exe'. Executable and script files are strictly blocked."`

---

#### Test 3: Attack Attempt - Unauthorized External Domain
```json
{
  "title": "External Phishing Link",
  "source_type": "pdf",
  "sources": [
    {
      "language": "en",
      "file_url": "https://untrusted-hacker-site.com/doc.pdf"
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Test"
    }
  ]
}
```
* **Expected Result:** `400 Bad Request`  
  `"Unauthorized storage domain 'untrusted-hacker-site.com'. Files must be hosted on authorized cloud storage."`

---

#### Test 4: Mismatched Media Type (`.mp4` under `pdf`)
```json
{
  "title": "Wrong Media Type Test",
  "source_type": "pdf",
  "sources": [
    {
      "language": "en",
      "file_url": "https://s3.amazonaws.com/tutorial_video.mp4"
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Intro"
    }
  ]
}
```
* **Expected Result:** `400 Bad Request`  
  `"URL extension '.mp4' for language 'en' does not match expected source type 'pdf'. Allowed extensions: .pdf."`

---

#### Test 5: Inverted Video Timestamps (`start > end`)
```json
{
  "title": "Invalid Video Clip",
  "source_type": "video",
  "sources": [
    {
      "language": "en",
      "file_url": "https://s3.amazonaws.com/video.mp4"
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Corrupt Clip",
      "start_time_seconds": 120.0,
      "end_time_seconds": 30.0
    }
  ]
}
```
* **Expected Result:** `400 Bad Request`  
  `"start_time_seconds cannot be greater than end_time_seconds"`

---

#### Test 6: Missing / Non-Existent File Guardrail (HTTP 404)
```json
{
  "title": "Ghost Record Test",
  "source_type": "video",
  "sources": [
    {
      "language": "en",
      "file_url": "https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev/non_existent_video.mp4"
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Intro"
    }
  ]
}
```
* **Expected Result:** `400 Bad Request`  
  `{"sources": "Remote file at 'https://pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev/non_existent_video.mp4' does not exist (HTTP 404 Not Found). The file upload to Cloudflare R2 must complete successfully before submitting knowledge metadata."}`

