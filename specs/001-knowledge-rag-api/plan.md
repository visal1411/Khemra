# Implementation Plan: Knowledge Upload and Question Search APIs

**Branch**: `001-knowledge-rag-api` | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-knowledge-rag-api/spec.md`

## Summary

Refactor and adapt the ingestion and search subsystems in `apps/rag/` to align with the revised database models (`Knowledge`, `KnowledgeSource`, `KnowledgeSegment`, `MetadataType`, and `KnowledgeEmbedding`). The implementation provides:
1. An atomic ingestion endpoint (`POST /api/rag/knowledge/`) that accepts knowledge headers, sources, and segments, generates multi-facet vector embeddings (1536-dimensional) per metadata item, and persists them transactionally.
2. A semantic question search endpoint (`POST /api/rag/search/`) that embeds queries, queries PostgreSQL with pgvector cosine distance, and computes weighted multi-signal relevance scores using active `MetadataType` weights.
3. An entity inspection endpoint (`GET /api/rag/knowledge/<id>/`) to review processing status and segment structure.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Django 5.1.3, Django REST Framework 3.15.2, pgvector 0.3.6, FastEmbed 0.9.0  
**Storage**: PostgreSQL 16 with pgvector extension enabled  
**Testing**: Django test runner (`python manage.py test apps.rag`) with deterministic test doubles (`FakeEncoder`)  
**Target Platform**: Linux container (Docker) & Windows development host  
**Project Type**: REST Web Service (Service-Oriented Monolith within Django)  
**Performance Goals**: < 500ms p95 search latency, < 3s standard multi-segment ingestion  
**Constraints**: Lightweight inference without PyTorch, 1536-dimensional vectors, 1 class per file  
**Scale/Scope**: Multi-modal knowledge ingestion (video, pdf, text) supporting fine-grained segment retrieval  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Rationale |
|---|---|---|---|
| **I. Single Responsibility & Strict File Layout** | One class per file, matching filename. Business logic in `services/`, views dispatch, serializers validate. | **PASS** | Clean division: `services/KnowledgeIngestService.py`, `services/KnowledgeSearchService.py`, serializers, and views each isolated to dedicated files. |
| **II. Lightweight & Deterministic ML Runtime** | FastEmbed / ONNX runtime, no PyTorch in requirements, offline test doubles. | **PASS** | `Encoder` uses FastEmbed / ONNX. Tests use `FakeEncoder` with 1536d output. Zero network calls or GPU dependencies in test suite. |
| **III. Multi-Signal & Granular Embedding Strategy** | Knowledge vectorized per facet (title, summary, questions, keywords); weighted multi-signal aggregation. | **PASS** | `EmbeddingTextBuilder` produces separate entries for `MetadataType`. Search uses `ScoreCombiner` across all active types. |
| **IV. Test-Driven & Isolated Test Double Coverage** | Complete test coverage in `tests/`, offline execution. | **PASS** | Unit and integration test suites will cover all new services, serializers, and endpoints. |
| **V. Relational & Vector Hybrid Rigor** | pgvector `VectorField(dimensions=1536)`, UUID PKs, cascade rules, composite unique constraints. | **PASS** | All models define UUID primary keys, pgvector vectors, and composite unique constraints matching specifications. |

## Project Structure

### Documentation (this feature)

```text
specs/001-knowledge-rag-api/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output: decisions on metadata types, 1536d vectors, search
├── data-model.md        # Phase 1 output: entity specs, relationships, state machine
├── quickstart.md        # Phase 1 output: end-to-end runnable validation guide
├── contracts/           # Phase 1 output: API schemas (upload, search, detail)
│   ├── knowledge-upload.json
│   ├── knowledge-search.json
│   └── knowledge-detail.json
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
apps/rag/
├── models/
│   ├── Knowledge.py
│   ├── KnowledgeSource.py
│   ├── KnowledgeSegment.py
│   ├── MetadataType.py
│   ├── KnowledgeEmbedding.py
│   ├── enums.py
│   └── __init__.py
├── encoder/
│   ├── Encoder.py
│   └── __init__.py
├── services/
│   ├── EmbeddingTextBuilder.py
│   ├── KnowledgeIngestService.py
│   ├── KnowledgeSearchService.py
│   ├── KnowledgeScore.py
│   ├── ScoreCombiner.py
│   └── __init__.py
├── serializers/
│   ├── KnowledgeInputSerializer.py
│   ├── KnowledgeSearchRequestSerializer.py
│   ├── KnowledgeSearchResponseSerializer.py
│   ├── KnowledgeDetailSerializer.py
│   └── __init__.py
├── views/
│   ├── KnowledgeUploadAPI.py
│   ├── KnowledgeSearchAPI.py
│   ├── KnowledgeDetailAPI.py
│   └── __init__.py
├── urls.py
├── admin/
│   ├── KnowledgeAdmin.py
│   ├── KnowledgeSourceAdmin.py
│   ├── KnowledgeSegmentAdmin.py
│   ├── MetadataTypeAdmin.py
│   ├── KnowledgeEmbeddingAdmin.py
│   └── __init__.py
└── tests/
    ├── FakeEncoder.py
    ├── test_EmbeddingTextBuilder.py
    ├── test_KnowledgeIngestService.py
    ├── test_KnowledgeSearchService.py
    └── test_KnowledgeAPIs.py
```

**Structure Decision**: Selected standard service-oriented architecture complying with the Constitution rule of "one class per file, filename matching class name". Legacy services (`SegmentIngestService`, `SegmentSearchService`) and views will be cleanly upgraded or replaced with their `Knowledge*` counterparts.

## Complexity Tracking

*No constitutional violations identified. Standard architecture requires no exception tracking.*
