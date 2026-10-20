# Quickstart & Validation Guide: Knowledge RAG APIs

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Date**: 2026-10-19

## Overview

This guide provides step-by-step runnable validation scenarios to verify the Knowledge Ingestion and Question Search endpoints end-to-end against the revised schema.

---

## 1. Prerequisites

1. Ensure the PostgreSQL database container with pgvector is running:
   ```bash
   docker compose up -d db
   ```
2. Apply database migrations:
   ```bash
   docker compose exec web python manage.py migrate
   # Or locally:
   python manage.py migrate
   ```
3. Ensure default `MetadataType` records exist in the database (`title`, `summary`, `keywords`, `questions`):
   ```bash
   python manage.py shell -c "from apps.rag.models import MetadataType; [MetadataType.objects.get_or_create(name=n, defaults={'weight': w, 'is_active': True}) for n, w in [('title', 0.20), ('summary', 0.25), ('keywords', 0.20), ('questions', 0.35)]]"
   ```

---

## 2. Scenario 1: Uploading New Knowledge with Segments

Submit a new knowledge document with segmented metadata via `POST /api/rag/knowledge/`.

### Request
```bash
curl -X POST http://localhost:8000/api/rag/knowledge/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Employee Leave Policy Guidelines",
    "description": "Comprehensive corporate guidelines regarding paid time off, sick leave, and holidays.",
    "source_type": "text",
    "sources": [
      {
        "language": "en",
        "file_data": "RW1wbG95ZWUgTGVhdmUgUG9saWN5IGRvY3VtZW50IGNvbnRlbnQuLi4="
      }
    ],
    "segments": [
      {
        "segment_index": 0,
        "title": "Annual Paid Time Off Allocation",
        "summary": "Full-time employees receive 18 days of paid time off accrued monthly.",
        "transcript": "All permanent employees accrue 1.5 days of annual paid leave every month, totaling 18 days per calendar year.",
        "keywords": ["annual leave", "PTO", "vacation days", "accrual"],
        "possible_questions": [
          "How many annual leave days do I get?",
          "How does PTO accrue each month?"
        ]
      },
      {
        "segment_index": 1,
        "title": "Sick Leave and Medical Certificates",
        "summary": "Employees are entitled to 10 paid sick days per year, requiring medical certificates for absences longer than two days.",
        "transcript": "Sick leave covers medical appointments and illness. Absences exceeding two consecutive days require a certified doctor note.",
        "keywords": ["sick leave", "medical certificate", "illness", "doctor note"],
        "possible_questions": [
          "When is a medical certificate required?",
          "How many paid sick days do employees receive?"
        ]
      }
    ]
  }'
```

### Expected Response (`201 Created`)
```json
{
  "id": "7b8e1f5c-890a-428e-8a21-432851910245",
  "title": "Employee Leave Policy Guidelines",
  "source_type": "text",
  "processing_status": "completed",
  "segments_count": 2,
  "created_at": "2026-10-19T15:30:00Z"
}
```

---

## 3. Scenario 2: Semantic Search Query

Submit a natural language question to `POST /api/rag/search/` to retrieve matching segments.

### Request
```bash
curl -X POST http://localhost:8000/api/rag/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I take time off when I am sick?",
    "top_k": 2,
    "threshold": 0.30,
    "weights": {
      "questions": 0.40,
      "summary": 0.30,
      "title": 0.15,
      "keywords": 0.15
    }
  }'
```

### Expected Response (`200 OK`)
```json
{
  "question": "How do I take time off when I am sick?",
  "count": 1,
  "weights": {
    "questions": 0.4,
    "summary": 0.3,
    "title": 0.15,
    "keywords": 0.15
  },
  "results": [
    {
      "segment_id": "4d1a3c7e-9081-4235-8651-789a1b2c3d4e",
      "knowledge_id": "7b8e1f5c-890a-428e-8a21-432851910245",
      "knowledge_title": "Employee Leave Policy Guidelines",
      "segment_index": 1,
      "title": "Sick Leave and Medical Certificates",
      "summary": "Employees are entitled to 10 paid sick days per year, requiring medical certificates for absences longer than two days.",
      "transcript": "Sick leave covers medical appointments and illness. Absences exceeding two consecutive days require a certified doctor note.",
      "score": 0.812,
      "confidence": 81.20,
      "best_match": "questions",
      "confidence_by_type": {
        "questions": 89.4,
        "summary": 78.1,
        "title": 68.5,
        "keywords": 72.3
      }
    }
  ]
}
```

---

## 4. Scenario 3: Inspecting Knowledge Details

Retrieve full details of the stored knowledge item via `GET /api/rag/knowledge/{id}/`.

### Request
```bash
curl http://localhost:8000/api/rag/knowledge/7b8e1f5c-890a-428e-8a21-432851910245/
```

### Expected Response (`200 OK`)
Returns the complete `Knowledge` entity with its `sources` and `segments` as defined in [contracts/knowledge-detail.json](./contracts/knowledge-detail.json).
