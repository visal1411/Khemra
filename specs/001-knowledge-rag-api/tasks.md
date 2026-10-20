# Tasks: Knowledge Upload and Question Search APIs

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Branch**: `001-knowledge-rag-api` | **Status**: Pending

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test fixtures, metadata types initialization, and legacy cleanup

- [ ] T001 Configure 1536-dimensional vector test double in apps/rag/tests/FakeEncoder.py
- [ ] T002 [P] Implement default metadata types seed command (title, summary, keywords, questions) in apps/rag/management/commands/seed_metadata_types.py
- [ ] T003 [P] Update admin registrations for Knowledge, KnowledgeSource, KnowledgeSegment, MetadataType, and KnowledgeEmbedding in apps/rag/admin/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database migrations and core scoring/embedding infrastructure that all user stories depend on

**⚠️ CRITICAL**: Must complete before user story implementation begins

- [ ] T004 Create and apply database migrations for revised knowledge models in apps/rag/migrations/0003_knowledge_schema.py
- [ ] T005 Update text builder to extract facet items from segments for 1536d embedding generation in apps/rag/services/EmbeddingTextBuilder.py
- [ ] T006 [P] Update unit tests for text builder in apps/rag/tests/test_EmbeddingTextBuilder.py
- [ ] T007 Implement multi-signal score data container in apps/rag/services/KnowledgeScore.py
- [ ] T008 Implement dynamic metadata-weighted score combiner with MetadataType lookup in apps/rag/services/ScoreCombiner.py

**Checkpoint**: Core foundation and scoring utilities ready; user story implementation can proceed.

---

## Phase 3: User Story 1 - Ingest and Store New Knowledge with Multi-Facet Segments (Priority: P1) 🎯 MVP

**Goal**: Enable clients to upload a knowledge item with physical sources and an array of segments, automatically generating and persisting 1536-dimensional embeddings for all metadata facets.

**Independent Test**: Submit a multi-segment knowledge payload to `POST /api/rag/knowledge/` and verify records in `Knowledge`, `KnowledgeSource`, `KnowledgeSegment`, and `KnowledgeEmbedding` with status `completed`.

### Tests for User Story 1
- [ ] T009 [P] [US1] Create unit and contract tests for knowledge ingestion in apps/rag/tests/test_KnowledgeIngestService.py

### Implementation for User Story 1
- [ ] T010 [P] [US1] Implement input validation serializer supporting segments and knowledge_segments array in apps/rag/serializers/KnowledgeInputSerializer.py
- [ ] T011 [US1] Implement atomic knowledge, source, segment, and embedding ingestion pipeline in apps/rag/services/KnowledgeIngestService.py
- [ ] T012 [US1] Implement knowledge upload API view handling POST requests in apps/rag/views/KnowledgeUploadAPI.py
- [ ] T013 [US1] Register knowledge upload route /api/rag/knowledge/ in apps/rag/urls.py

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Query Knowledge via Natural Language Question and Receive Ranked Answers (Priority: P1)

**Goal**: Accept a natural language question, query segment embeddings using pgvector cosine distance, and return ranked segments with combined confidence scores and per-metadata confidence breakdowns.

**Independent Test**: Issue a query to `POST /api/rag/search/` against indexed knowledge segments and verify that results are ranked by similarity with confidence breakdowns and best match indicators.

### Tests for User Story 2
- [ ] T014 [P] [US2] Create unit and integration tests for search service in apps/rag/tests/test_KnowledgeSearchService.py

### Implementation for User Story 2
- [ ] T015 [P] [US2] Implement search request validation serializer (question, top_k, threshold, weights) in apps/rag/serializers/KnowledgeSearchRequestSerializer.py
- [ ] T016 [US2] Implement vector similarity search and multi-signal ranking with pgvector in apps/rag/services/KnowledgeSearchService.py
- [ ] T017 [US2] Implement question search API view handling POST requests in apps/rag/views/KnowledgeSearchAPI.py
- [ ] T018 [US2] Register search route /api/rag/search/ in apps/rag/urls.py

**Checkpoint**: User Stories 1 and 2 work together end-to-end (ingest -> search).

---

## Phase 5: User Story 3 - Inspect Ingestion Processing Status and Stored Knowledge Details (Priority: P2)

**Goal**: Enable system operators and clients to retrieve the details, sources, segments, and current processing status of an uploaded knowledge item by identifier.

**Independent Test**: Retrieve an existing knowledge record via `GET /api/rag/knowledge/<id>/` and verify complete representation of sources, segments, and lifecycle status.

### Implementation for User Story 3
- [ ] T019 [P] [US3] Implement knowledge detail serializer in apps/rag/serializers/KnowledgeDetailSerializer.py
- [ ] T020 [US3] Implement knowledge detail API view handling GET requests by ID in apps/rag/views/KnowledgeDetailAPI.py
- [ ] T021 [US3] Register knowledge detail route /api/rag/knowledge/<uuid:id>/ in apps/rag/urls.py
- [ ] T022 [P] [US3] Create API integration tests covering upload, detail inspection, and search flows in apps/rag/tests/test_KnowledgeAPIs.py

**Checkpoint**: All three user stories are functional and independently verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup of legacy artifacts, validation against quickstart scenarios, and full test suite verification

- [ ] T023 Clean up obsolete legacy views and serializers (SegmentListCreateAPI, SegmentDetailAPI, SegmentExportAPI, SegmentInputSerializer, SearchRequestSerializer)
- [ ] T024 Run end-to-end validation scenarios documented in specs/001-knowledge-rag-api/quickstart.md
- [ ] T025 Run full test suite via python manage.py test apps.rag to verify 100% passing tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories.
- **User Story 1 (Phase 3 - P1)**: Depends on Phase 2 — MVP milestone.
- **User Story 2 (Phase 4 - P1)**: Depends on Phase 2 & Phase 3 (needs indexed data for end-to-end querying).
- **User Story 3 (Phase 5 - P2)**: Depends on Phase 2 & Phase 3.
- **Polish (Phase 6)**: Depends on completion of all user stories.

### Parallel Opportunities

- **Phase 1**: T002 and T003 can execute in parallel after T001.
- **Phase 2**: T006 can run in parallel with T007 and T008 once T005 completes.
- **Phase 3**: T009 and T010 can run in parallel before T011.
- **Phase 4**: T014 and T015 can run in parallel before T016.
- **Phase 5**: T019 and T022 can run in parallel with T020.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1: Knowledge Ingestion).
3. **STOP and VALIDATE**: Test ingestion endpoint with multi-segment payload and verify database rows.
4. User Story 1 delivers standalone value by establishing the persistent RAG knowledge base.

### Incremental Delivery
1. Foundation & Ingestion (US1) -> Working knowledge repository.
2. Add Semantic Search (US2) -> End-to-end question answering platform.
3. Add Detail Inspection (US3) -> Operational transparency and entity inspection.
4. Polish & Cleanup -> Deprecate legacy models and test all scenarios.
