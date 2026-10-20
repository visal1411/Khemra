<!--
Sync Impact Report:
- Version change: Unversioned Template -> 1.0.0
- List of modified principles:
  - [PRINCIPLE_1_NAME] -> I. Single Responsibility & Strict File Layout (One Class Per File)
  - [PRINCIPLE_2_NAME] -> II. Lightweight & Deterministic ML Runtime (No Heavy PyTorch)
  - [PRINCIPLE_3_NAME] -> III. Multi-Signal & Granular Embedding Strategy
  - [PRINCIPLE_4_NAME] -> IV. Test-Driven & Isolated Test Double Coverage
  - [PRINCIPLE_5_NAME] -> V. Relational & Vector Hybrid Rigor
- Added sections:
  - Technical Stack & Constraints
  - Development Workflow & Quality Gates
- Removed sections: None
- Follow-up TODOs: None
-->

# Khemra RAG Platform Constitution

## Core Principles

### I. Single Responsibility & Strict File Layout (One Class Per File)
Every Python file MUST define exactly one primary class whose name matches the filename (e.g., `SegmentSearchService.py` defines `SegmentSearchService`). Code MUST be structured strictly across architectural layers:
- `models/`: Database schema, table constraints, and model-level field definitions.
- `services/`: Business logic, search scoring, data pipelines, and orchestration. Business logic MUST NOT leak into views or models.
- `serializers/`: Input validation and API payload transformation using Django REST Framework.
- `views/`: HTTP protocol handling, dispatching to services, and returning standard JSON responses.
- `encoder/`: Vectorization abstractions and model inference wrappers.
- `utils/` & `constants/`: Pure helper functions, parsers, and enum definitions.

### II. Lightweight & Deterministic ML Runtime (No Heavy PyTorch)
The backend MUST prioritize operational efficiency, small container images, and low-latency startup:
- Embeddings and vector representations MUST run through lightweight runtimes (e.g., FastEmbed with ONNX runtime). Heavy deep-learning frameworks (such as PyTorch or TensorFlow) MUST NOT be introduced unless explicitly mandated.
- Inference caching and model weights MUST be volume-cached in container environments.
- Tests MUST NOT perform network downloads or heavy inference; deterministic test doubles (such as `FakeEncoder`) MUST be used in testing environments.

### III. Multi-Signal & Granular Embedding Strategy
Semantic search precision relies on fine-grained, contextual representations rather than monolithic document dumps:
- Knowledge segments MUST be vectorized per distinct metadata facet (e.g., title, summary, keyword collections, individual questions).
- The retrieval pipeline MUST support multi-signal matching with configurable weights and expose per-metadata confidence scores alongside the combined similarity score.
- Text builders MUST explicitly prepare each metadata item according to its semantic granularity.

### IV. Test-Driven & Isolated Test Double Coverage
Software quality and vector pipeline correctness MUST be verified through comprehensive, repeatable testing:
- Every service, serializer, and API endpoint MUST have a corresponding test suite located in `tests/`.
- Tests MUST run completely offline and finish within seconds.
- Test suites MUST validate edge cases, including empty metadata, threshold filtering, score boundary behavior, and malformed inputs.
- Schema migrations MUST be validated against test data before merging.

### V. Relational & Vector Hybrid Rigor
Database integrity is paramount when handling paired structured metadata and high-dimensional vectors:
- All vector storage MUST utilize PostgreSQL with the `pgvector` extension, explicitly defining dimensionality (e.g., `VectorField(dimensions=1536)`).
- Relational integrity MUST be strictly enforced via UUID primary keys, foreign key cascading rules, database-level indices, and composite unique constraints.
- Raw file data and binary streams stored in the database MUST use appropriate binary fields with size and type validations.

## Technical Stack & Constraints

- **Language & Framework**: Python 3.11+, Django 5.1+, Django REST Framework 3.15+.
- **Database & Search**: PostgreSQL with `pgvector` extension enabled.
- **Inference Runtime**: FastEmbed / ONNX Runtime (CPU-optimized, container-friendly).
- **Architecture**: Service-oriented monolith within Django app modules (`apps.rag`, `apps.catalog`).
- **Data Interchange**: RESTful JSON APIs adhering strictly to camelCase or snake_case conventions established by active serializers.

## Development Workflow & Quality Gates

- **Quality Verification**: All test suites (`python manage.py test apps.rag`) MUST pass before committing changes.
- **Migration Discipline**: Any changes to models in `apps/*/models/` MUST include corresponding migration files generated via `python manage.py makemigrations`.
- **Bidirectional Fidelity**: Data import and export workflows MUST preserve complete structural fidelity round-trip.
- **Error Handling**: API endpoints MUST return clear, informative error structures with appropriate HTTP status codes (400 for bad input, 404 for missing entities, 500 for unhandled exceptions).

## Governance

This Constitution represents the authoritative architectural and operational standard for the Khemra RAG Platform. It supersedes informal agreements and transient coding shortcuts:
- All pull requests, code reviews, and automated generation tasks MUST verify compliance against these principles.
- Deviations or architectural exceptions require explicit justification and must be documented as formal amendments.
- Versioning follows Semantic Versioning (MAJOR for principle removals/redefinitions, MINOR for new principles or substantial expansions, PATCH for clarifications).

**Version**: 1.0.0 | **Ratified**: 2026-10-19 | **Last Amended**: 2026-10-19
