# Django REST Framework Serializers & Validation Reference

This document provides a comprehensive guide to all Serializers implemented across the codebase, their input/output schemas, and every validation rule enforced.

---

## Table of Contents
1. [Overview of Serializers](#1-overview-of-serializers)
2. [RAG Ingestion Serializers](#2-rag-ingestion-serializers)
   - [KnowledgeInputSerializer](#knowledgeinputserializer)
   - [KnowledgeSourceInputSerializer](#knowledgesourceinputserializer)
   - [KnowledgeSegmentInputSerializer](#knowledgesegmentinputserializer)
3. [RAG Search Serializers](#3-rag-search-serializers)
   - [KnowledgeSearchRequestSerializer](#knowledgesearchrequestserializer)
   - [KnowledgeSearchResponseSerializer](#knowledgesearchresponseserializer)
4. [RAG Detail Serializers](#4-rag-detail-serializers)
   - [KnowledgeDetailSerializer](#knowledgedetailserializer)
   - [KnowledgeSourceDetailSerializer](#knowledgesourcedetailserializer)
   - [KnowledgeSegmentDetailSerializer](#knowledgesegmentdetailserializer)
5. [Catalog Serializers](#5-catalog-serializers)
   - [ProductSerializer](#productserializer)

---

## 1. Overview of Serializers

| Module | Serializer Class | Type | Direction | Purpose |
| :--- | :--- | :--- | :---: | :--- |
| **`apps.rag`** | [`KnowledgeInputSerializer`](#knowledgeinputserializer) | `Serializer` | **Input** | Validates documents, media files, and segment arrays during ingestion |
| **`apps.rag`** | [`KnowledgeSourceInputSerializer`](#knowledgesourceinputserializer) | `Serializer` | **Input** | Validates uploaded files (base64/URL) and languages |
| **`apps.rag`** | [`KnowledgeSegmentInputSerializer`](#knowledgesegmentinputserializer) | `Serializer` | **Input** | Validates text chunks, timestamps, and page ranges |
| **`apps.rag`** | [`KnowledgeSearchRequestSerializer`](#knowledgesearchrequestserializer) | `Serializer` | **Input** | Validates search queries, threshold, top_k, and custom weights |
| **`apps.rag`** | [`KnowledgeSearchResponseSerializer`](#knowledgesearchresponseserializer) | `Serializer` | **Output** | Serializes ranked search results and match confidence scores |
| **`apps.rag`** | [`KnowledgeDetailSerializer`](#knowledgedetailserializer) | `ModelSerializer` | **Output** | Serializes full knowledge entity, sources, and segments |
| **`apps.catalog`** | [`ProductSerializer`](#productserializer) | `ModelSerializer` | **Both** | Serializes e-commerce catalog products |

---

## 2. RAG Ingestion Serializers

**File:** [`apps/rag/serializers/KnowledgeInputSerializer.py`](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeInputSerializer.py)  
**Endpoint:** `POST /api/rag/knowledge/`

### `KnowledgeInputSerializer`
The top-level serializer for creating new knowledge bases and their segments.

#### Fields
| Field | Type | Required | Constraints / Defaults | Description |
| :--- | :--- | :---: | :--- | :--- |
| `title` | `CharField` | **Yes** | `max_length=500` | Title of the knowledge base document. |
| `description` | `CharField` | No | `allow_blank=True`, `allow_null=True` | High-level overview/description. |
| `source_type` | `ChoiceField` | **Yes** | Choices: `pdf`, `video`, `text` | The media type of the knowledge base. |
| `sources` | `ListField` | No | Child: `KnowledgeSourceInputSerializer`, `default=[]` | Multi-language source files. |
| `segments` | `ListField` | No* | Child: `KnowledgeSegmentInputSerializer` | Segment chunks (*either `segments` or `knowledge_segments` required). |
| `knowledge_segments` | `ListField` | No* | Child: `KnowledgeSegmentInputSerializer` | Alias for `segments`. |

#### Validation Rules Enforced
1. **Title Whitespace Validation (`validate_title`)**:
   - Title cannot be empty or contain only whitespace characters.
   - Automatically trims leading/trailing whitespace (`value.strip()`).
2. **At Least One Segment (`validate`)**:
   - Either `segments` or `knowledge_segments` must contain at least 1 item.
   - Raises: `"At least one segment must be provided in 'segments' or 'knowledge_segments'."`
3. **Unique Languages per Document (`validate`)**:
   - Sources cannot contain duplicate languages (e.g. two `en` sources are rejected).
   - Raises: `"Duplicate languages found in sources. Each source must have a unique language."`
4. **Unique Segment Indices (`validate`)**:
   - Every segment must have a unique `segment_index`.
   - Raises: `"Duplicate segment_index found. Each segment must have a unique segment_index."`
5. **Magic Number File Signature Validation (`_validate_source_file_signature`)**:
   - Inspects the decoded binary bytes against the declared `source_type`:
     - **PDF:** Must begin with magic bytes `b"%PDF-"`.
     - **VIDEO:** Must match recognized video container headers:
       - MP4: bytes 4–8 in `(b"ftyp", b"moov", b"mdat", b"wide")`
       - WebM / MKV: begins with `b"\x1a\x45\xdf\xa3"`
       - AVI: begins with `b"RIFF"` and bytes 8–12 are `b"AVI "`
       - MPEG: begins with `b"\x00\x00\x01\xba"` or sync byte `0x47`
     - **TEXT:** Must be valid `UTF-8` or `UTF-16` encodable text.

---

### `KnowledgeSourceInputSerializer`
Validates individual source files (e.g. video files, PDFs) associated with a document.

#### Fields
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :---: | :--- | :--- |
| `language` | `CharField` | **Yes** | `max_length=10` | Language code (e.g., `en`, `km`, `mm`). |
| `file_data` | `CharField` | No | `allow_blank=True`, `allow_null=True` | Base64-encoded raw file content. |
| `file_url` | `CharField` | No | `max_length=1000`, `allow_null=True` | Public/CDN URL if file is hosted externally. |
| `duration_seconds`| `FloatField` | No | `allow_null=True` | Video duration in seconds. |
| `page_count` | `IntegerField`| No | `allow_null=True` | Total pages (for PDFs). |

#### Validation Rules Enforced
1. **Base64 Integrity (`validate_file_data`)**:
   - If `file_data` is provided, tests `base64.b64decode(value, validate=True)`.
   - Raises validation error if string is malformed or invalid base64.

---

### `KnowledgeSegmentInputSerializer`
Validates segment chunks (transcripts, chapters, or pages).

#### Fields
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :---: | :--- | :--- |
| `segment_index` | `IntegerField` | **Yes** | `min_value=0` | Sequential ordering index. |
| `title` | `CharField` | No | `max_length=500`, `allow_blank=True` | Segment chapter/topic title. |
| `summary` | `CharField` | No | `allow_blank=True`, `allow_null=True` | Concise overview of this chunk. |
| `transcript` | `CharField` | No | `allow_blank=True`, `allow_null=True` | Full verbatim text. |
| `keywords` | `ListField` | No | Child: `CharField`, `default=[]` | Extracted search keywords. |
| `possible_questions` | `ListField` | No | Child: `CharField`, `default=[]` | Synthetic questions matching this chunk. |
| `start_time_seconds` | `FloatField` | No | `allow_null=True` | Media timestamp start. |
| `end_time_seconds` | `FloatField` | No | `allow_null=True` | Media timestamp end. |
| `page_start` | `IntegerField` | No | `allow_null=True` | Document start page. |
| `page_end` | `IntegerField` | No | `allow_null=True` | Document end page. |

#### Validation Rules Enforced
1. **Timestamp Chronology (`validate`)**:
   - `start_time_seconds` cannot be greater than `end_time_seconds`.
2. **Page Range Chronology (`validate`)**:
   - `page_start` cannot be greater than `page_end`.

---

## 3. RAG Search Serializers

**File:** [`apps/rag/serializers/KnowledgeSearchRequestSerializer.py`](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeSearchRequestSerializer.py) & [`KnowledgeSearchResponseSerializer.py`](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeSearchResponseSerializer.py)  
**Endpoint:** `POST /api/rag/knowledge/search/`

### `KnowledgeSearchRequestSerializer`
Validates incoming search requests from frontend clients or chatbots.

#### Fields
| Field | Type | Required | Default | Constraints | Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `question` | `CharField` | **Yes** | — | `min_length=1` | The query to search for. |
| `language` | `CharField` | No | `"en"` | `max_length=10` | Target language code. |
| `top_k` | `IntegerField` | No | `3` | `min_value=1`, `max_value=50` | Maximum results to return. |
| `threshold` | `FloatField` | No | `0.10` | `min_value=0.0`, `max_value=1.0` | Minimum cosine similarity cutoff. |
| `weights` | `DictField` | No | `None` | Child: `FloatField(min_value=0.0)` | Custom weights for score signals. |

#### Validation Rules Enforced
1. **Question Whitespace (`validate_question`)**:
   - Must not be empty or whitespace only.
   - Trims whitespace automatically.
2. **Custom Weights Format (`validate_weights`)**:
   - Must be a non-empty dictionary mapping string signal names to positive numbers.
   - At least one weight in the dictionary must be greater than zero (`sum(weights.values()) > 0`).

---

### `KnowledgeSearchResponseSerializer`
Serializes search results sent back to the client.

#### Fields
* `question`: (`string`) Original search query.
* `language`: (`string`) Language used for source resolution.
* `count`: (`integer`) Number of results returned.
* `weights_used`: (`dict`) Dictionary of weights applied during scoring.
* `results`: (`list` of `SearchResultItemSerializer`)
  * `segment_id`: (`UUID`) ID of the matching segment.
  * `knowledge_id`: (`UUID`) ID of the parent knowledge document.
  * `knowledge_title`: (`string`) Title of the parent document.
  * `source_type`: (`string`) `video`, `pdf`, or `text`.
  * `score`: (`float`) Merged similarity score (0.0 to 1.0).
  * `confidence`: (`float`) Percentage confidence score (0.0% to 100.0%).
  * `best_match`: (`string`) Signal with highest match (`"question"`, `"keyword"`, `"summary"`, or `"topic"`).
  * `confidence_by_type`: (`dict`) Breakdown score per signal.
  * `matched_source`: (`MatchedSourceSerializer`) Resolved media file URL and details for the requested language.

---

## 4. RAG Detail Serializers

**File:** [`apps/rag/serializers/KnowledgeDetailSerializer.py`](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeDetailSerializer.py)  
**Endpoint:** `GET /api/rag/knowledge/:id/`

### `KnowledgeDetailSerializer`
ModelSerializer for reading the full knowledge record.

* **Model:** `Knowledge`
* **Nested Relationships:**
  * `sources`: Read-only nested list via `KnowledgeSourceDetailSerializer`.
  * `segments`: Read-only nested list via `KnowledgeSegmentDetailSerializer`.
* **Fields:** `id`, `title`, `description`, `source_type`, `processing_status`, `created_at`, `updated_at`, `sources`, `segments`.

---

## 5. Catalog Serializers

**File:** [`apps/catalog/serializers/ProductSerializer_.py`](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/catalog/serializers/ProductSerializer_.py)  
**Endpoint:** `/api/catalog/products/`

### `ProductSerializer`
ModelSerializer for managing product catalog items.

* **Model:** `Product`
* **Fields:**
  * `id` *(read-only)*
  * `name`: Name of product.
  * `description`: Product details.
  * `price`: Decimal price.
  * `stock_quantity`: Integer inventory quantity.
  * `image_url`: Product thumbnail link.
  * `is_available`: Boolean availability flag.
  * `created_at` *(read-only)*
  * `updated_at` *(read-only)*

---

## Quick Reference: HTTP Validation Errors
When serializer validation fails, DRF returns `400 Bad Request` with structured error messages:

```json
{
  "segments": [
    "At least one segment must be provided in 'segments' or 'knowledge_segments'."
  ],
  "start_time_seconds": [
    "start_time_seconds cannot be greater than end_time_seconds"
  ],
  "question": [
    "Search question cannot be empty or whitespace only."
  ],
  "threshold": [
    "Ensure this value is greater than or equal to 0.0."
  ]
}
```
