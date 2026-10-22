# Phase 0: Technical Research & Architectural Decisions

**Feature**: `004-ai-overview-search`  
**Date**: 2026-10-22

---

## 1. Research Question: Groq Client vs. Requests vs. Official SDK

### Options Evaluated:
1. **`groq` official SDK**:
   - Pros: Built on `httpx`, supports native type hints and structured output with Pydantic/JSON mode.
   - Cons: Adds an extra dependency.
2. **`requests` / `urllib` direct REST calls to `https://api.groq.com/openai/v1/chat/completions`**:
   - Pros: Zero new dependencies (we already have `requests` in `requirements.txt`).
   - Standard OpenAI-compatible API format (works identically with Groq, vLLM, Ollama, OpenAI, or any self-hosted model).
   - Fast, straightforward, easily mockable in tests without complex SDK wrapper mocking.

### Decision:
Use direct standard HTTP requests via `requests` to Groq's OpenAI-compatible completions endpoint (`https://api.groq.com/openai/v1/chat/completions`) wrapped inside an abstract `BaseLLMService` and concrete `GroqLLMService`.
* Rationale: Because the user explicitly plans to swap to their **own self-hosted LLM** later, the OpenAI-compatible REST wire protocol is universal. Both Groq and self-hosted engines (vLLM, Ollama, TGI, LocalAI) speak the exact same `chat/completions` REST API. Switching providers later only requires changing `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`.

---

## 2. Research Question: Ensuring Structured JSON Output & Citation Grounding

### Problem:
How do we force the LLM to return valid JSON with:
1. A clean, revised `summary`.
2. Sequential `steps` (`step_number`, `title`, `instruction`).
3. Each step reliably citing a valid `segment_id` from the retrieved segments without hallucinating phantom IDs.

### Strategy:
1. **Groq JSON Mode**: Set `"response_format": {"type": "json_object"}` in the API call.
2. **Prompt Engineering with Strict Schema & Constrained ID Injection**:
   - Provide the LLM with a strictly numbered dictionary of available segments:
     ```text
     Available Segments:
     [Segment ID: c29385b3-2222-42ce-92dc-962bb1770b7d]
     Title: Accessing the Portal
     Transcript: ...
     ```
   - In the system prompt, instruct:
     *"You must output a JSON object with 'summary' (string) and 'steps' (array). Each step must have 'step_number' (int), 'title' (string), 'instruction' (string), and 'segment_id' (string). The 'segment_id' MUST EXACTLY MATCH one of the segment IDs listed in the context. If no single segment explains the step, use the closest segment ID from the context."*
3. **Backend Post-Processing & Validation**:
   - Parse the JSON response.
   - Verify that every `segment_id` returned in `steps` actually belongs to one of the retrieved `results`.
   - If an invalid or hallucinated `segment_id` is returned, fall back to the top-scoring segment's ID to preserve referential integrity.

---

## 3. Research Question: Latency, Timeouts & Error Resilience

### Goal:
Keep overall endpoint latency under 1.5 seconds and ensure search never crashes if the LLM provider is down.

### Architecture:
* **Vector Search First**: Vector search takes $\sim 20\text{ms}$.
* **Timeout Budget**: Set Groq HTTP request timeout to `4.0` seconds. Groq inference on Llama 3 typically takes $250\text{ms} - 600\text{ms}$.
* **Graceful Fallback**: If Groq returns 429 (rate limit), 5xx, or times out, catch the exception, log it via `loguru`, set `summary = None` and `steps = []`, and return the `results` segments normally with `200 OK`. The search user experience is never broken.

---

## 4. Architectural Summary

| Component | Responsibility | Layer |
| :--- | :--- | :--- |
| `AIOverviewAPI.py` | Handles `POST /api/rag/knowledge/search/ai-overview/`, parses input, returns response. | `views/` |
| `AIOverviewSearchService.py` | Orchestrates vector search retrieval + LLM synthesis. | `services/` |
| `BaseLLMService.py` | Abstract base class defining `generate_overview(question, segments)`. | `services/` |
| `GroqLLMService.py` | Concrete implementation connecting to Groq / OpenAI-compatible endpoint. | `services/` |
| `AIOverviewResponseSerializer.py` | DRF serializer validating output payload (`summary`, `steps`, `results`). | `serializers/` |
