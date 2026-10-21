# Search Typo Tolerance & Production Hybrid Search Guide

This document explains why typo queries (e.g., `"i trcak status"`) fail in pure vector semantic search, identifies the exact codebase components responsible, and outlines two production-grade solutions: **Query Preprocessing / Spell Correction** and **Hybrid Search (`pgvector` + `pg_trgm`)**.

---

## 1. Problem Analysis: Why `"i trcak status"` Returns Empty `[]`

When a query such as `"i trcak status"` is submitted with `"threshold": 0.25`:

```json
{
  "question": "i trcak status",
  "top_k": 3,
  "threshold": 0.25,
  "language": "mm"
}
```

The API returns `200 OK` with `"results": []`.

### Root Cause Breakdown

1. **Subword Tokenization Distortion (Embedding Model)**:
   - The model `sentence-transformers/all-MiniLM-L6-v2` in [apps/rag/encoder/Encoder.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/encoder/Encoder.py) uses WordPiece subword tokenization.
   - For valid words like `"track"`, it maps directly to a high-quality semantic token.
   - For typos like `"trcak"`, the tokenizer cannot recognize the word and splits it into meaningless subword fragments (`tr`, `##cak`).
   - This corrupts the resulting 384-dimensional unit vector in vector space.

2. **Similarity Score Drop vs. Threshold Gate**:
   - In [apps/rag/services/KnowledgeSearchService.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/services/KnowledgeSearchService.py), similarity scores are computed via cosine distance ($1.0 - \text{distance}$) and merged across metadata types:

| Query | Max Combined Score | Threshold | Evaluated Condition (`score >= threshold`) | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| `"i track status"` *(correct)* | **`0.4106`** (41.1%) | `0.25` | `0.4106 >= 0.25` ✅ | Returned top matches |
| `"i trcak status"` *(typo)* | **`0.2103`** (21.0%) | `0.25` | `0.2103 >= 0.25` ❌ | **Dropped / Filtered out** |

3. **Backend Validation Did Not Fail**:
   - The payload passed [KnowledgeSearchRequestSerializer.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeSearchRequestSerializer.py) without error.
   - The rejection occurs strictly within the search scoring filter.

---

## 2. Where Code Changes Are Needed

| Component | File Path | What Needs Changing |
| :--- | :--- | :--- |
| **Search Service** | [apps/rag/services/KnowledgeSearchService.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/services/KnowledgeSearchService.py) | Integrate query preprocessing (Option A) or merge trigram lexical scoring with vector scoring (Option B). |
| **Response Serializer** | [apps/rag/serializers/KnowledgeSearchResponseSerializer.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeSearchResponseSerializer.py) | Add `corrected_query` or `did_you_mean` field to the response schema. |
| **Dependencies / Docker** | [requirements.txt](file:///d:/Khemra%20Backend/my-django-dockerv2/requirements.txt) | Add spell-checking library (e.g., `symspellpy` or `pyspellchecker` for Option A). |
| **Database Migrations** | `apps/rag/migrations/` | Enable PostgreSQL `pg_trgm` extension and add GIN trigram indexes on `KnowledgeSegment` text fields (Option B). |

---

## 3. Solution Approaches

```mermaid
graph TD
    UserQuery["User Input: 'i trcak status'"]

    subgraph Option_A ["Option A: Spell Correction Preprocessor"]
        Pre["QueryPreprocessor (SymSpell / Vocabulary)"]
        Pre -->|"Corrects to 'i track status'"| EncA["Encoder (all-MiniLM)"]
        EncA -->|"Clean Vector"| VecSearchA["pgvector Cosine Search"]
        VecSearchA -->|"Score: ~0.41"| OutputA["Results + 'did_you_mean': 'i track status'"]
    end

    subgraph Option_C ["Option B: Hybrid Search (pgvector + pg_trgm)"]
        EncB["Encoder (Raw Vector)"]
        EncB --> VecSearchB["Vector Similarity (Dense)"]
        UserQuery --> TrgmSearch["PostgreSQL Trigram Search (Sparse/Fuzzy)"]
        VecSearchB --> RRF["Score Fusion: α·Vector + β·Trigram"]
        TrgmSearch --> RRF
        RRF -->|"Score: ~0.55"| OutputB["High-Confidence Combined Results"]
    end

    UserQuery --> Pre
    UserQuery --> EncB
```

---

### Option A: Query Preprocessing & Spell Correction (Recommended for Quick Win)

#### Concept
Before passing the raw question into the embedding encoder, run it through an in-memory spell corrector or domain-vocabulary matcher. If a correction occurs, search using the corrected text while returning the corrected query to the client.

#### Implementation Steps

1. **Add dependency to [requirements.txt](file:///d:/Khemra%20Backend/my-django-dockerv2/requirements.txt)**:
   ```text
   pyspellchecker>=0.8.0
   ```
   *(or `symspellpy>=6.7.7` for microsecond-level performance).*

2. **Create a Query Preprocessor Service**:
   Create `apps/rag/services/QueryPreprocessor.py`:
   ```python
   from spellchecker import SpellChecker

   class QueryPreprocessor:
       def __init__(self, custom_words=None):
           self.spell = SpellChecker()
           if custom_words:
               self.spell.word_frequency.load_words(custom_words)

       def preprocess(self, text: str) -> dict:
           words = text.split()
           corrected_words = []
           was_corrected = False

           for word in words:
               clean_word = word.lower().strip("?,.!")
               correction = self.spell.correction(clean_word)
               if correction and correction != clean_word:
                   corrected_words.append(correction)
                   was_corrected = True
               else:
                   corrected_words.append(word)

           corrected_text = " ".join(corrected_words)
           return {
               "original": text,
               "corrected": corrected_text,
               "was_corrected": was_corrected,
           }
   ```

3. **Integrate into [KnowledgeSearchService.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/services/KnowledgeSearchService.py)**:
   ```python
   # At beginning of search():
   preprocessor = QueryPreprocessor()
   prep = preprocessor.preprocess(question)
   query_text = prep["corrected"] if prep["was_corrected"] else question

   # Encode the clean text
   raw_vec = self.encoder.encode(query_text, normalize_embeddings=True)
   ```

4. **Update Response Serializer**:
   In [KnowledgeSearchResponseSerializer.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/serializers/KnowledgeSearchResponseSerializer.py), add:
   ```python
   did_you_mean = serializers.CharField(required=False, allow_null=True)
   ```

#### Pros & Cons
- **Pros**: Very fast (< 2ms), handles standard typos cleanly, allows UI to show *"Did you mean: i track status?"*, requires zero database changes.
- **Cons**: Requires keeping a domain dictionary for company/product-specific jargon that isn't standard English.

---

### Option B: Hybrid Search (`pgvector` Dense + `pg_trgm` Trigrams) (Enterprise Standard)

#### Concept
Rather than relying only on vector distance, combine **dense semantic search** (`pgvector`) with **fuzzy lexical matching** (`pg_trgm`).

- **Dense Embedding**: Captures meaning (e.g., `"view parcel delivery"` matches `"track status"`).
- **Trigram Similarity**: Captures character-level similarity (e.g., `"trcak"` matches `"track"` because trigrams `tra`, `rac`, `ack` overlap).

#### Implementation Steps

1. **Enable PostgreSQL `pg_trgm` Extension**:
   Create a migration or execute in database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

2. **Add GIN Trigram Indexes on `KnowledgeSegment`**:
   In [apps/rag/models/KnowledgeSegment.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/models/KnowledgeSegment.py):
   ```python
   from django.contrib.postgres.indexes import GinIndex

   class Meta:
       indexes = [
           GinIndex(fields=["title"], opclasses=["gin_trgm_ops"], name="idx_segment_title_trgm"),
           GinIndex(fields=["summary"], opclasses=["gin_trgm_ops"], name="idx_segment_summary_trgm"),
           GinIndex(fields=["transcript"], opclasses=["gin_trgm_ops"], name="idx_segment_transcript_trgm"),
       ]
   ```

3. **Compute Hybrid Score in [KnowledgeSearchService.py](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/services/KnowledgeSearchService.py)**:
   Combine vector cosine similarity with trigram similarity using Reciprocal Rank Fusion (RRF) or linear interpolation:
   ```python
   from django.contrib.postgres.search import TrigramSimilarity

   # 1. Fetch Trigram Lexical Scores
   trigram_matches = (
       KnowledgeSegment.objects.annotate(
           lexical_sim=Greatest(
               TrigramSimilarity("title", question),
               TrigramSimilarity("summary", question),
               TrigramSimilarity("transcript", question),
           )
       )
       .filter(lexical_sim__gt=0.1)
       .values("id", "lexical_sim")
   )

   # 2. Blend: Final_Score = (0.7 * Vector_Score) + (0.3 * Trigram_Score)
   for seg_id, score in combined_vector_scores.items():
       lex_score = trigram_map.get(seg_id, 0.0)
       hybrid_score = (0.7 * score) + (0.3 * lex_score)
   ```

#### Pros & Cons
- **Pros**: State-of-the-art retrieval; immune to both semantic misses and character typos; handles exact IDs, codes, names, and mistyped words automatically without third-party dictionaries.
- **Cons**: Requires database index creation and tuning weights between dense and sparse results.

---

## 4. Comparison Summary

| Metric | Option A: Query Preprocessor | Option B: Hybrid Search (`pg_trgm`) |
| :--- | :--- | :--- |
| **Typo Resilience** | High (for known dictionary words) | High (for any character permutations) |
| **Implementation Complexity** | Low (single service module) | Moderate (DB migration + hybrid scoring) |
| **New Infrastructure** | Python package (`pyspellchecker`) | Postgres extension (`pg_trgm`) |
| **Query Latency Impact** | < 2ms | 5 - 15ms |
| **UI Feedback Capability** | Provides *"Did you mean?"* | Transparent rank boosting |
