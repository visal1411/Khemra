# Implementation Plan: AI Overview & Step-by-Step Search

**Branch**: `004-ai-overview-search` | **Date**: 2026-10-22 | **Spec**: [specs/004-ai-overview-search/spec.md](file:///d:/Khemra%20Backend/my-django-dockerv2/specs/004-ai-overview-search/spec.md)

**Input**: Feature specification from `/specs/004-ai-overview-search/spec.md`

---

## Summary

This feature adds a dedicated endpoint `POST /api/rag/knowledge/search/ai-overview/`. It performs the standard multi-signal vector search against `pgvector`, preserves the exact existing `results` segment array, and uses an LLM (Groq with OpenAI-compatible REST completions) to synthesize a revised, natural `summary` and an ordered array of `steps`, with each step attached to a specific `segment_id`.

The LLM integration uses an adapter interface (`BaseLLMService`) so Groq can easily be swapped with a custom self-hosted LLM (e.g. vLLM/Ollama) in the future.

---

## Technical Context

**Language/Version**: Python 3.12 (inside Docker Debian slim)  
**Primary Dependencies**: Django 5.1.x, Django REST Framework 3.15.x, requests 2.34.x, FastEmbed 0.9.0  
**Storage**: PostgreSQL 17 with `pgvector` extension  
**Testing**: Django TestCase with mocked LLM HTTP calls  
**Target Platform**: Linux container (Docker) on Windows / Production Linux  
**Project Type**: Django Web Service / REST API  
**Performance Goals**: < 1.0s total response time (Vector search ~20ms, Groq LLM inference ~400ms)  
**Constraints**: 
- Strict 4.0s timeout on LLM calls.
- Graceful degradation: if LLM fails, return `summary: null` and `steps: []` with `results` intact.
- Zero PyTorch, zero heavy SDKs. Direct OpenAI-compatible REST endpoint to Groq.  
**Scale/Scope**: 1 new view, 2 new services, 2 new serializers, 1 new test suite.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Analysis | Status |
| :--- | :--- | :---: |
| **I. Single Responsibility & Strict File Layout (One Class Per File)** | Each new class lives in its own dedicated file matching the class name: `BaseLLMService.py`, `GroqLLMService.py`, `AIOverviewSearchService.py`, `AIOverviewAPI.py`, `AIOverviewResponseSerializer.py`. | **PASS** |
| **II. Lightweight & Deterministic ML Runtime (No Heavy PyTorch)** | Uses existing FastEmbed ONNX runtime for vectorization and lightweight HTTP calls for LLM completions. Zero PyTorch. | **PASS** |
| **III. Multi-Signal & Granular Embedding Strategy** | Leverages the existing 4-signal vector search (`KnowledgeSearchService`) to retrieve candidate segments before LLM synthesis. | **PASS** |
| **IV. Test-Driven & Isolated Test Double Coverage** | Unit and integration tests mock Groq API calls using `unittest.mock.patch` to run offline and fast. | **PASS** |
| **V. Relational & Vector Hybrid Rigor** | No changes to the database schema needed; uses existing indexed knowledge segments. | **PASS** |

---

## Project Structure

### Documentation (this feature)

```text
specs/004-ai-overview-search/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan
├── research.md          # Technical research & decisions
├── data-model.md        # Data models and DTO structures
├── quickstart.md        # How to test & run
└── contracts/           # API JSON contracts
    └── ai-overview-search.json
```

### Source Code

```text
apps/rag/
├── services/
│   ├── BaseLLMService.py             # Abstract LLM provider interface
│   ├── GroqLLMService.py             # Groq implementation (OpenAI-compatible)
│   └── AIOverviewSearchService.py    # Orchestrates vector search + LLM synthesis
├── serializers/
│   └── AIOverviewResponseSerializer.py # Validates { question, summary, steps, results }
├── views/
│   └── AIOverviewAPI.py              # POST /api/rag/knowledge/search/ai-overview/
├── urls.py                           # URL routing
└── tests/
    └── test_AIOverviewAPI.py         # Offline test suite with mocked LLM calls
```

**Structure Decision**: Fully adheres to Constitution Principle I: one class per file in appropriate Django app subdirectories (`services/`, `serializers/`, `views/`, `tests/`).

---

## Complexity Tracking

*No constitution violations. All gates PASS.*
