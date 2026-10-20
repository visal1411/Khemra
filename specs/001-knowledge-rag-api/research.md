# Research: Knowledge Upload and Question Search APIs

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Date**: 2026-10-19

## Overview

This research document analyzes the technical approaches, decisions, and architectural patterns required to align the API and retrieval layers with the revised database models (`Knowledge`, `KnowledgeSource`, `KnowledgeSegment`, `MetadataType`, and `KnowledgeEmbedding`).

---

## 1. Dynamic Metadata Types & Scoring Weights

### Context
In the previous implementation, metadata types were hardcoded as fixed enum choices (`ContentType`: keyword, question, topic, summary) with fixed static weights. The revised data model establishes a database entity:
```sql
Table MetadataType {
  id uuid [pk]
  name varchar(50) [not null, unique]
  weight float [not null]
  is_active boolean [not null]
  ...
}
```

### Decision
- Create a `MetadataTypeService` (or cache layer in `ScoreCombiner`) that loads active `MetadataType` records from the database with an in-memory TTL/cache fallback.
- Standard default types seeded in the database:
  - `title` (weight: 0.20)
  - `summary` (weight: 0.25)
  - `keywords` (weight: 0.20)
  - `questions` (weight: 0.35)
- Allow request-level overrides in `POST /api/rag/search/` via a `weights` object (e.g., `{"questions": 0.5, "summary": 0.5}`).
- Normalize active weights dynamically when computing the composite score:
  $$\text{Score} = \frac{\sum_{t} w_t \cdot \max(0, \text{sim}_t)}{\sum_{t} w_t}$$

### Alternatives Considered
- *Hardcoded weights in settings.py*: Rejected because the new model introduces `MetadataType` specifically to allow database-driven weights and activation states.
- *Strict database lookup on every query*: Can introduce minor latency; mitigated with cached dictionary lookup of active types.

---

## 2. Vector Dimension Alignment & Embedding Strategy (1536-Dimensional)

### Context
The revised model defines `embedding_vector vector(1536)` on `KnowledgeEmbedding`, paired with `model_name` and `model_version`. The previous setup used 384-dimensional vectors from `all-MiniLM-L6-v2`.

### Decision
- Update `Encoder` and `FakeEncoder` interfaces:
  - Production `Encoder`: Configured to output 1536-dimensional embeddings (e.g., FastEmbed model supporting 1536 dimensions or OpenAI-compatible embedding interface `text-embedding-3-small` / standard FastEmbed ONNX 1536d provider).
  - Test double `FakeEncoder`: Configured with `DIMENSIONS = 1536` generating deterministic normalized vectors using token hashing.
- Record `model_name` (e.g., `"fastembed/bge"` or `"openai/text-embedding-3-small"`) and `model_version` (e.g., `"1.0"`) on every `KnowledgeEmbedding` record to support multi-model migrations and reproducibility.
- Ingestion pipeline embeds each metadata item:
  - Title: 1 row with `item_index=0`, `title` populated, `embedding_vector` set.
  - Summary: 1 row with `item_index=0`, `summary` populated, `embedding_vector` set.
  - Questions: $N$ rows with `item_index=i`, `questions=[{"text": q, ...}]`, and `embedding_vector` set for that question.
  - Keywords: Stored either as a single joined representation or per-keyword with `item_index`.

### Alternatives Considered
- *Single concatenated vector per segment*: Rejected by Constitution Principle III (Multi-Signal & Granular Embedding Strategy), which mandates per-facet vectorization.
- *Changing DB column to 384 dimensions*: Rejected because user specified `vector(1536)` in the revised model schema.

---

## 3. Ingestion Payload Architecture & Source File Handling

### Context
`Knowledge` represents the top-level entity, `KnowledgeSource` stores physical files and language metadata (`file_data bytea`), and `KnowledgeSegment` stores granular search passages. The upload endpoint must accommodate structured ingestion.

### Decision
- Structure the primary upload endpoint `POST /api/rag/knowledge/`:
  - Accepts a JSON payload containing:
    - `title`, `description`, `source_type` (video, pdf, text)
    - Optional `sources`: list of `{language, file_data (base64 or reference), duration_seconds, page_count}`
    - `segments`: list of `{segment_index, title, summary, transcript, keywords, possible_questions, start_time_seconds, end_time_seconds, page_start, page_end}`
  - Atomic database transaction:
    1. Create `Knowledge` with `processing_status = 'processing'`.
    2. Persist `KnowledgeSource` records with byte decoding.
    3. Bulk create `KnowledgeSegment` records.
    4. Batch generate embeddings for all segments in one vectorizer call.
    5. Bulk create `KnowledgeEmbedding` records.
    6. Transition `processing_status` to `'completed'`.
  - On unhandled failure, mark status as `'failed'` or rollback.

### Alternatives Considered
- *Multiple round-trip API calls (create knowledge -> create segments -> trigger embed)*: Too error-prone and invites orphaned records. A unified atomic endpoint ensures consistency.

---

## 4. Multi-Signal Vector Retrieval with PostgreSQL pgvector

### Context
When a user asks a question, we want to find the best segments by matching against all metadata types, scoring each type independently, and combining them with weights.

### Decision
- Search algorithm in `KnowledgeSearchService`:
  1. Embed the user question once into a 1536-dimensional query vector.
  2. Query `KnowledgeEmbedding` using pgvector's `CosineDistance`:
     ```python
     KnowledgeEmbedding.objects.values("segment_id", "metadata_type__name")
         .annotate(distance=Min(CosineDistance("embedding_vector", query_vector)))
     ```
  3. Convert distance to cosine similarity: $\text{sim} = 1.0 - \text{distance}$.
  4. Group similarities by `segment_id`.
  5. Compute combined score using `ScoreCombiner` with active or user-overridden weights.
  6. Filter candidates by `threshold` (default 0.30) and sort descending.
  7. Paginate/slice to `top_k`.
  8. Fetch matching `KnowledgeSegment` records in bulk, including parent `Knowledge` details.
  9. Format output with combined confidence, best matching metadata type, and itemized confidence per type.

### Alternatives Considered
- *Full text search (BM25) only*: Does not leverage embeddings or semantic nuance.
- *In-memory dot product*: Inefficient at scale; utilizing PostgreSQL's native pgvector index (`HNSW` / `IVFFlat`) delegates distance calculations to the database.
