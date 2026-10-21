# Understanding Embeddings, Cosine Similarity & Search Scoring

This guide explains how our RAG search works under the hood in simple, everyday language.

---

## 1. What is an Embedding?

Computers do not understand the meaning of words—they only understand numbers.

An **Embedding** is a way to turn a piece of text into a list of **384 decimal numbers** (called a **Vector**).
- Our AI model (`all-MiniLM-L6-v2`) reads the text and places it on a 384-dimensional "map".
- **Words or sentences with similar meanings end up very close to each other on the map.**

### Example:
- `"Slack setup"` $\rightarrow$ `[0.024, -0.115, 0.450, ...]` (384 numbers)
- `"Chat tool configuration"` $\rightarrow$ `[0.022, -0.110, 0.442, ...]` *(almost identical numbers!)*
- `"Cooking recipe"` $\rightarrow$ `[-0.450, 0.812, -0.103, ...]` *(completely different numbers)*

---

## 2. What is Cosine Distance & Cosine Similarity?

Think of every embedding vector as an **arrow pointing in a direction** on that map.

```text
                  Similar Angle (Small Distance, High Similarity)
                      ↗ "Slack setup"
                     ↗  
       Query: "How to use Slack?"
                    
                    
       ----------------------------→ "Cooking recipe" (Large Angle, Low Similarity)
```

1. **Cosine Distance** measures the angle between the two arrows:
   - `0.0` = Arrows point in the exact same direction (**100% Identical**).
   - `1.0` = Arrows are at a 90° angle (**Completely Unrelated**).

2. **Cosine Similarity** is simply:
   $$\text{Similarity} = 1.0 - \text{Distance}$$
   - **`1.0` (or 100%)** = Perfect match.
   - **`0.0` (or 0%)** = No match at all.

---

## 3. How We Store Segments in the Database

Each segment in your knowledge base has 4 types of metadata. We embed them into rows in `knowledge_embeddings`:

| Metadata Type | How it is embedded | Number of vectors stored |
| :--- | :--- | :--- |
| **`keyword`** | **One-by-one** (each keyword gets its own vector) | 1 vector per keyword |
| **`question`** | **One-by-one** (each question gets its own vector) | 1 vector per question |
| **`topic`** (Title) | Single string | 1 vector |
| **`summary`** | Single string | 1 vector |

---

## 4. Multi-Segment Showcase: Comparing 3 Segments

Let's assume a training video with **3 different segments** stored in the database:

### Segment 1: Company Culture & History (0:00 - 0:30)
- **Title (`topic`):** `"Company Culture and Core Values"`
- **Summary (`summary`):** `"Overview of company mission, heritage, and teamwork values."`
- **Keywords (`keyword`):** `["welcome", "history", "values", "culture"]`
- **Questions (`question`):** 
  - Q1: `"What are our core company values?"`
  - Q2: `"Who founded the company?"`

### Segment 2: Workspace & Slack Setup (0:30 - 1:00)
- **Title (`topic`):** `"Workspace & Tools Setup"`
- **Summary (`summary`):** `"Setting up communication tools, Slack channels, and contacting IT support."`
- **Keywords (`keyword`):** `["IT support", "slack", "email", "accounts"]`
- **Questions (`question`):** 
  - Q1: `"How do I log into Slack?"`
  - Q2: `"Who do I contact for IT support?"`

### Segment 3: HR Policies & Leave (1:00 - 1:30)
- **Title (`topic`):** `"HR Policies and Time Off"`
- **Summary (`summary`):** `"Guidelines for requesting annual leave, sick days, and payroll dates."`
- **Keywords (`keyword`):** `["vacation", "holiday", "sick leave", "payroll"]`
- **Questions (`question`):** 
  - Q1: `"How do I apply for annual leave?"`
  - Q2: `"When is monthly payday?"`

---

## 5. The User Search Query

User asks in Postman:
> **`"How do I use Slack to talk to IT support?"`**

The system encodes this query into vector `q_vec`.

Now, the database calculates cosine similarity across **all 3 segments simultaneously**:

---

### Step 1: Calculate Similarities for Segment 1 (Culture)

| Field | Comparison against Query | Similarity |
| :--- | :--- | :--- |
| **`keyword`** | Evaluates `"welcome"` (0.28), `"history"` (0.15), `"values"` (0.30), `"culture"` (0.35) $\rightarrow$ **Best Match** | **`0.35`** |
| **`question`** | Evaluates Q1 (0.32), Q2 (0.18) $\rightarrow$ **Best Match** | **`0.32`** |
| **`topic`** | `"Company Culture and Core Values"` | **`0.29`** |
| **`summary`** | `"Overview of company mission, heritage, and teamwork values."` | **`0.34`** |

---

### Step 2: Calculate Similarities for Segment 2 (Slack / IT)

| Field | Comparison against Query | Similarity |
| :--- | :--- | :--- |
| **`keyword`** | Evaluates `"IT support"` (0.84), `"slack"` (0.91), `"email"` (0.42), `"accounts"` (0.40) $\rightarrow$ **Best Match** (`"slack"`) | **`0.91`** |
| **`question`** | Evaluates Q1 (`"How do I log into Slack?"`: 0.88), Q2 (`"Who do I contact for IT support?"`: 0.82) $\rightarrow$ **Best Match** (Q1) | **`0.88`** |
| **`topic`** | `"Workspace & Tools Setup"` | **`0.68`** |
| **`summary`** | `"Setting up communication tools, Slack channels, and contacting IT support."` | **`0.82`** |

---

### Step 3: Calculate Similarities for Segment 3 (HR & Leave)

| Field | Comparison against Query | Similarity |
| :--- | :--- | :--- |
| **`keyword`** | Evaluates `"vacation"` (0.10), `"holiday"` (0.12), `"sick leave"` (0.14), `"payroll"` (0.18) $\rightarrow$ **Best Match** | **`0.18`** |
| **`question`** | Evaluates Q1 (0.15), Q2 (0.20) $\rightarrow$ **Best Match** | **`0.20`** |
| **`topic`** | `"HR Policies and Time Off"` | **`0.14`** |
| **`summary`** | `"Guidelines for requesting annual leave, sick days, and payroll dates."` | **`0.16`** |

---

## 6. Score Combination for Each Segment

The [`ScoreCombiner`](file:///d:/Khemra%20Backend/my-django-dockerv2/apps/rag/services/ScoreCombiner.py) applies the standard weighted formula:

$$\text{Score} = (0.20 \times \text{keyword}) + (0.35 \times \text{question}) + (0.20 \times \text{topic}) + (0.25 \times \text{summary})$$

### Calculating Segment 1 (Culture):
$$\text{Score}_1 = (0.20 \times 0.35) + (0.35 \times 0.32) + (0.20 \times 0.29) + (0.25 \times 0.34)$$
$$\text{Score}_1 = 0.070 + 0.112 + 0.058 + 0.085 = \mathbf{0.325} \text{ (32.5\%)}$$

### Calculating Segment 2 (Slack / IT):
$$\text{Score}_2 = (0.20 \times 0.91) + (0.35 \times 0.88) + (0.20 \times 0.68) + (0.25 \times 0.82)$$
$$\text{Score}_2 = 0.182 + 0.308 + 0.136 + 0.205 = \mathbf{0.831} \text{ (83.1\%)}$$

### Calculating Segment 3 (HR & Leave):
$$\text{Score}_3 = (0.20 \times 0.18) + (0.35 \times 0.20) + (0.20 \times 0.14) + (0.25 \times 0.16)$$
$$\text{Score}_3 = 0.036 + 0.070 + 0.028 + 0.040 = \mathbf{0.174} \text{ (17.4\%)}$$

---

## 7. Ranking and Filtering (Threshold & Top-K)

### Step 1: Filter by Threshold (`threshold = 0.30`)
- **Segment 2:** `0.831 >= 0.30` $\rightarrow$ **Passed** ✅
- **Segment 1:** `0.325 >= 0.30` $\rightarrow$ **Passed** ✅
- **Segment 3:** `0.174 < 0.30` $\rightarrow$ **Filtered out (Too irrelevant)** ❌

### Step 2: Sort by Highest Score (`top_k = 3`)

| Rank | Segment | Title | Score | Confidence Level | Matched Video Timestamp |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **#1** | **Segment 2** | Workspace & Tools Setup | **`0.831` (83.1%)** | High | `00:30 - 01:00` |
| **#2** | **Segment 1** | Company Culture and Core Values | **`0.325` (32.5%)** | Low | `00:00 - 00:30` |

---

---

## 8. Real-World Scale: What Happens with 50+ Segments?

In a production knowledge base, you won't have just 3 segments—you might have **10, 50, or 500 segments**.

**The system calculates the similarity and final score for EVERY single segment in your database!**

Here is the exact pipeline:

```text
User Query: "How do I use Slack to talk to IT support?"
       │
       ▼ (1 Query Vector encoded by AI)
       │
┌──────┴─────────────────────────────────────────────────────────────────┐
│ PostgreSQL calculates cosine similarity for ALL Segments in DB:        │
├───────────────┬────────────┬────────────┬───────────┬──────────────────┤
│ Segment       │ Keyword    │ Question   │ Topic     │ Summary          │
├───────────────┼────────────┼────────────┼───────────┼──────────────────┤
│ Segment 1     │   0.35     │   0.32     │   0.29    │   0.34           │ ──► Score: 0.325 (32.5%)
│ Segment 2     │   0.91     │   0.88     │   0.68    │   0.82           │ ──► Score: 0.831 (83.1%)
│ Segment 3     │   0.18     │   0.20     │   0.14    │   0.16           │ ──► Score: 0.174 (17.4%)
│ Segment 4     │   0.22     │   0.19     │   0.25    │   0.21           │ ──► Score: 0.213 (21.3%)
│ Segment 5     │   0.75     │   0.70     │   0.55    │   0.60           │ ──► Score: 0.665 (66.5%)
│ ...           │    ...     │    ...     │    ...    │    ...           │ ──► ...
│ Segment 50    │   0.10     │   0.12     │   0.08    │   0.11           │ ──► Score: 0.106 (10.6%)
└───────────────┴────────────┴────────────┴───────────┴──────────────────┘
                               │
                               ▼
               [Filter: Keep only Score >= 0.30]
                 (Segments 3, 4, ..., 50 dropped!)
                               │
                               ▼
               [Sort Remaining from Highest to Lowest]
                 1st place: Segment 2 (Score: 0.831)
                 2nd place: Segment 5 (Score: 0.665)
                 3rd place: Segment 1 (Score: 0.325)
                               │
                               ▼
                  Return Top 3 (`top_k = 3`) to User!
```

### Where this happens in the code (`KnowledgeSearchService.py`):

```python
# 1. Database scans ALL segments in parallel using pgvector indexing:
rows = (
    KnowledgeEmbedding.objects.values("segment_id", "metadata_type__name")
    .annotate(distance=Min(CosineDistance("embedding_vector", q_vec)))
)

# 2. Computes the weighted final score for EVERY segment:
scores = [combiner.combine(seg_id, sims) for seg_id, sims in per_segment.items()]

# 3. Discards all segments below the threshold (e.g. < 0.30):
scores = [s for s in scores if s.score >= threshold]

# 4. Sorts the surviving segments from highest score to lowest:
scores.sort(key=lambda s: s.score, reverse=True)

# 5. Returns the Top K (e.g. top 3):
scores = scores[:top_k]
```

---

## 9. What the User Receives in the JSON API Response

```json
{
  "question": "How do I use Slack to talk to IT support?",
  "language": "en",
  "count": 2,
  "results": [
    {
      "segment_id": "8488fb2c-9a4f-47dc-a567-9d7a5b3a4a11",
      "score": 0.831,
      "best_match": "keyword",
      "confidence": "high",
      "confidence_by_type": {
        "keyword": 0.91,
        "question": 0.88,
        "topic": 0.68,
        "summary": 0.82
      },
      "segment": {
        "title": "Workspace & Tools Setup",
        "summary": "Setting up communication tools, Slack channels, and contacting IT support.",
        "start_time_seconds": 30.0,
        "end_time_seconds": 60.0
      }
    },
    {
      "segment_id": "3144a11b-7a3d-42bc-9f12-8d7a1b2a3c99",
      "score": 0.325,
      "best_match": "keyword",
      "confidence": "low",
      "confidence_by_type": {
        "keyword": 0.35,
        "question": 0.32,
        "topic": 0.29,
        "summary": 0.34
      },
      "segment": {
        "title": "Company Culture and Core Values",
        "summary": "Overview of company mission, heritage, and teamwork values.",
        "start_time_seconds": 0.0,
        "end_time_seconds": 30.0
      }
    }
  ]
}
```

---

## 10. Summary of the Design

1. **Independent Evaluation:** Every segment in the database is evaluated independently across all 4 metadata facets.
2. **Best Match Wins:** Multiple keywords or questions don't drag down the score; the single best match represents that facet.
3. **Smart Filtering:** Irrelevant segments (like HR Leave in Segment 3) fail the threshold filter (`0.174 < 0.30`) and never pollute search results.
4. **Precision Ranking:** The most relevant segment (Segment 2) ranks #1 with an `0.831` score and points the user directly to the exact video clip (`0:30 - 1:00`).
