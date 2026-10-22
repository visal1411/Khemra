# Phase 1: Data Model & Schema Specification

**Feature**: `004-ai-overview-search`  
**Date**: 2026-10-22

---

## 1. Relational & Domain Models

No new database tables are needed for this feature!
The feature consumes the existing models:
* `Knowledge`
* `KnowledgeSource`
* `KnowledgeSegment`
* `KnowledgeEmbedding`

All data for the overview and steps is synthesized dynamically at query time using the matching `KnowledgeSegment` rows.

---

## 2. In-Memory DTOs & Output Structures

### StepItem
Represents an individual synthesized action step linked to a segment:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class StepItem:
    step_number: int          # 1, 2, 3...
    title: string             # e.g. "Open the platform"
    instruction: string       # e.g. "Navigate to the portal website or launch app."
    segment_id: str           # UUID of the supporting KnowledgeSegment
```

### AIOverviewResult
The combined response object containing revised summary, steps, and unchanged search results:
```python
@dataclass
class AIOverviewResult:
    question: str
    language: str
    summary: Optional[str]            # Revised overall summary from LLM
    steps: list[StepItem]             # Sequential steps
    count: int                        # Number of segments returned in results
    weights_used: dict[str, float]    # Vector search weights applied
    results: list[dict]               # Unchanged SearchResultItem instances
```

---

## 3. Serializer Definitions

### `AIOverviewStepSerializer`
Validates each item in the `steps` array:
* `step_number`: `serializers.IntegerField()`
* `title`: `serializers.CharField()`
* `instruction`: `serializers.CharField()`
* `segment_id`: `serializers.UUIDField()`

### `AIOverviewResponseSerializer`
Extends the response format:
* `question`: `serializers.CharField()`
* `language`: `serializers.CharField()`
* `summary`: `serializers.CharField(allow_null=True)`
* `steps`: `serializers.ListField(child=AIOverviewStepSerializer(), default=list)`
* `count`: `serializers.IntegerField()`
* `weights_used`: `serializers.DictField(child=serializers.FloatField())`
* `results`: `serializers.ListField(child=SearchResultItemSerializer())` *(100% identical to existing search)*
