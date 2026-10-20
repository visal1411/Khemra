# Feature Specification: Knowledge Upload and Question Search APIs

**Feature Branch**: `001-knowledge-rag-api`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "i build the backend endpoint for this project whihc the first endpoint is for uploading the knowledge, and the second is return the output back to the user when the user post a question, so now i have modified the models to fit with my revised database. but for api and return logic is not modifiied to fit with the new model yet."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest and Store New Knowledge with Multi-Facet Segments (Priority: P1)

As a content administrator or client application, I want to submit knowledge items along with their source files, segments, and structured metadata so that the system parses, stores, and prepares them for semantic search.

**Why this priority**: Without the ability to ingest and process knowledge into the revised data model, the search system has no data to query. This is the core prerequisite for the entire RAG pipeline.

**Independent Test**: Can be tested independently by submitting a complete knowledge payload with segments and metadata, verifying that the knowledge entity, sources, segments, and embeddings are correctly created in the system, and receiving a success confirmation with the assigned unique IDs and processing status.

**Acceptance Scenarios**:

1. **Given** valid knowledge details containing title, description, source type, and one or more segments with metadata (title, summary, keywords, questions, timestamps/pages), **When** submitted to the upload endpoint, **Then** the system creates the knowledge item with "completed" or "processing" status and returns the created knowledge structure with unique IDs.
2. **Given** a knowledge upload request missing required fields (e.g., missing title or source type), **When** submitted to the upload endpoint, **Then** the system rejects the submission with a descriptive validation error and creates no orphaned data.
3. **Given** a knowledge item with associated raw source file bytes and language indicator, **When** submitted, **Then** the source is stored linked to the knowledge item and adheres to unique language constraints.

---

### User Story 2 - Query Knowledge via Natural Language Question and Receive Ranked Answers (Priority: P1)

As an end user or consumer application, I want to submit a natural language question and receive the most relevant knowledge segments along with confidence scores and source metadata so that I can quickly find accurate answers.

**Why this priority**: Returning relevant, grounded information based on a user's question is the primary value delivered by the RAG platform.

**Independent Test**: Can be tested independently by issuing search queries against existing indexed knowledge and verifying that matching segments are returned in ranked order with confidence scores, best match indicators, and metadata breakdowns.

**Acceptance Scenarios**:

1. **Given** indexed knowledge segments in the system, **When** a user submits a relevant question with an acceptable confidence threshold, **Then** the system returns matching segments sorted in descending order of combined similarity score, including titles, summaries, transcripts, and source identifiers.
2. **Given** indexed knowledge segments, **When** a question is submitted that does not meet the minimum confidence threshold, **Then** the system returns an empty result list without errors.
3. **Given** custom weighting preferences for metadata types (e.g., placing higher emphasis on questions or summaries), **When** supplied with the search request, **Then** the system applies the custom weights in calculating the final ranked score.

---

### User Story 3 - Inspect Ingestion Processing Status and Stored Knowledge Details (Priority: P2)

As a system operator or developer, I want to retrieve the details and current processing state of an uploaded knowledge item and its segments so that I can verify ingestion status and debug search accuracy.

**Why this priority**: Enables traceability, monitoring of asynchronous or long-running processing jobs, and verification of segment parsing.

**Independent Test**: Can be tested independently by requesting details for a specific knowledge identifier and confirming accurate status and segment metadata are returned.

**Acceptance Scenarios**:

1. **Given** an existing knowledge record in the system, **When** its unique identifier is queried, **Then** the system returns the knowledge header, processing status, associated source files, and segment listings.
2. **Given** a non-existent knowledge identifier, **When** queried, **Then** the system returns a clear entity-not-found notification.

---

### Edge Cases

- What happens when an upload request contains empty or whitespace-only segment transcripts and summaries?
- How does the system handle search queries that contain only punctuation, stop words, or are empty?
- How does the system handle concurrent upload requests for identical knowledge titles or sources?
- How are metadata types handled if a search request specifies weights for a metadata type that does not exist or is inactive?
- What happens when a search query exceeds expected length limits (e.g., multi-paragraph questions)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an endpoint to receive and ingest knowledge records, including title, description, source type (video, pdf, text), and optional binary source file data.
- **FR-002**: System MUST validate all incoming knowledge ingestion payloads against required schema definitions before persisting records.
- **FR-003**: System MUST record the processing lifecycle status (pending, processing, completed, failed) for each knowledge item.
- **FR-004**: System MUST store individual knowledge segments associated with the knowledge item, preserving segment sequence index, start/end bounds (time in seconds or page numbers), transcript, summary, keywords, and possible questions.
- **FR-005**: System MUST generate high-dimensional vector representations for each distinct metadata facet (e.g., title, summary, keyword set, individual questions) using the registered metadata types.
- **FR-006**: System MUST persist vector embeddings linked to their segment, metadata type, item index, model name, and model version.
- **FR-007**: System MUST provide a search endpoint that accepts a natural language query, maximum result count (top_k), minimum confidence threshold, and optional metadata weight overrides.
- **FR-008**: System MUST compute similarity scores across all active metadata types for each candidate segment and produce a unified, weighted confidence score.
- **FR-009**: System MUST return search results containing the matching segment details (identifier, knowledge reference, title, summary, transcript, time/page bounds), combined confidence score, breakdown of confidence by metadata type, and indication of which metadata type produced the best match.
- **FR-010**: System MUST enforce unique constraints preventing duplicate sources for the same knowledge and language, and duplicate segment indices for the same knowledge item.

### Key Entities

- **Knowledge**: Root knowledge asset representing an uploaded document, video, or article. Contains title, description, source type, processing status, and creation/update timestamps.
- **KnowledgeSource**: Physical representation of the knowledge content, containing language code, raw binary file content, optional duration in seconds, and optional page count. Linked directly to a Knowledge entity.
- **KnowledgeSegment**: Granular, indexed passage or time segment within a knowledge entity. Contains sequence index, title, summary, full transcript, keywords list, potential questions list, and temporal (start/end seconds) or spatial (start/end pages) boundaries.
- **MetadataType**: Definitional classification for metadata categories (e.g., title, summary, keyword, question) with default scoring weights and active/inactive status.
- **KnowledgeEmbedding**: Vector representation corresponding to a specific piece of segment metadata. Contains vector array, reference to segment and metadata type, item index, embedding model details, and cached textual content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users and automated callers can submit and successfully index a multi-segment knowledge item with immediate confirmation in under 3 seconds for standard payloads.
- **SC-002**: Question search queries return ranked, multi-signal results in under 500 milliseconds for standard knowledge bases.
- **SC-003**: 100% of returned search results include both the combined score and an itemized confidence breakdown across all evaluated metadata types.
- **SC-004**: System prevents 100% of invalid or malformed knowledge submissions with zero corrupt or orphaned database records created.
- **SC-005**: Ingestion round-trip integrity ensures that all submitted segment metadata fields (keywords, questions, bounds) can be retrieved with zero data loss.

## Assumptions

- Knowledge uploads in this iteration provide pre-segmented metadata (segment transcripts, summaries, keywords, questions) or structured payloads formatted according to the revised schema.
- The embedding generation model outputs vectors matching the active vector field configuration in the database.
- Default scoring weights are derived from active `MetadataType` records in the system unless explicitly overridden in the search query.
- Callers have network connectivity to the API service and authenticate according to existing application boundary configurations.
