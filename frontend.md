# Frontend Integration Guide — Knowledge RAG API

> **Notice:** A complete, comprehensive technical reference with full TypeScript client code, Cloudflare R2 upload progress tracking, and AI Overview video timestamp scrubbing is available in **[`FRONTEND_INTEGRATION_GUIDE.md`](file:///d:/Khemra%20Backend/my-django-dockerv2/FRONTEND_INTEGRATION_GUIDE.md)**.

Welcome! This guide contains everything the frontend team (Web, Mobile, Flutter, React) needs to integrate with the Knowledge RAG backend.

---

## 1. Quick Overview

- **Base URL (Local):** `http://localhost:8000/api/rag/`
- **Content-Type:** `application/json`
- **Supported Content Types:** `video`, `pdf`, `text`
- **Supported Languages:** `en` (English), `km` (Khmer), or any custom language code.

### Endpoints at a Glance

| Method | Endpoint | Description | Typical Use Case |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/api/rag/knowledge/search/` | AI semantic search against all segments | Search bar / Chatbot / Q&A UI |
| **`GET`** | `/api/rag/knowledge/:id/` | Get full knowledge details & all segments | Details page / Admin review |
| **`POST`** | `/api/rag/knowledge/` | Ingest new knowledge with segments | CMS / Admin portal upload |

---

## 2. Search Endpoint (Primary User-Facing)

### `POST /api/rag/knowledge/search/`

Performs an AI semantic search across all indexed segments in the database using vector cosine distance and 4-signal weighted scoring.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body Parameters

| Field | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `question` | `string` | **Yes** | — | The user's query/question (e.g. `"How do I use Slack?"`). |
| `language` | `string` | No | `"en"` | Desired language (`"en"`, `"km"`, etc.) for source resolution. |
| `top_k` | `integer` | No | `3` | Maximum number of results to return (between `1` and `50`). |
| `threshold` | `float` | No | `0.30` | Minimum score cutoff (between `0.0` and `1.0`). Results below this are dropped. |
| `weights` | `object` | No | *Default weights* | *(Optional)* Custom weights object for tuning score signals. |

#### Example Request Body
```json
{
  "question": "How do I track my delivery status?",
  "language": "km",
  "top_k": 3,
  "threshold": 0.30
}
```

#### Example Response Body (`200 OK`)
```json
{
  "question": "How do I track my delivery status?",
  "language": "km",
  "count": 1,
  "weights_used": {
    "topic": 0.20,
    "question": 0.35,
    "keyword": 0.20,
    "summary": 0.25
  },
  "results": [
    {
      "segment_id": "fff474df-92d6-4753-8403-53158e323368",
      "knowledge_id": "3ddec49e-17ae-4b3c-bf90-b42e9b7412ef",
      "knowledge_title": "Order Management & Delivery",
      "source_type": "video",
      "segment_index": 1,
      "title": "Tracking Your Delivery",
      "summary": "Walkthrough on checking order status and live courier tracking.",
      "transcript": "To track your delivery, open the orders tab and view live status.",
      "start_time_seconds": 30.0,
      "end_time_seconds": 60.0,
      "page_start": null,
      "page_end": null,
      "keywords": [
        "order status",
        "delivery",
        "tracking",
        "courier"
      ],
      "score": 0.8118,
      "confidence": 81.18,
      "best_match": "question",
      "confidence_by_type": {
        "summary": 65.4,
        "topic": 50.0,
        "keyword": 88.5,
        "question": 95.0
      },
      "matched_source": {
        "id": "18973489-bbf6-467b-b7f4-3122b3889773",
        "language": "en",
        "file_url": "https://example.com/videos/delivery_en.mp4",
        "duration_seconds": 60.0,
        "page_count": null,
        "is_fallback": true
      }
    }
  ]
}
```

#### Key Fields for the Frontend UI:

1. **`matched_source.file_url`**: Direct playable/downloadable URL for the media file.
2. **`start_time_seconds` & `end_time_seconds`**: Used for video/audio seeking.
3. **`page_start` & `page_end`**: Used for PDF page jumping.
4. **`matched_source.is_fallback`**:
   - If `false`, the exact language requested was found.
   - If `true`, the user requested a language (e.g. `km`) that wasn't available, so the backend fell back to English (`en`). Show a badge: *"Available in English"*.
5. **`score` & `confidence`**: Numerical relevance (`0.0` - `1.0` or `0%` - `100%`).

---

## 3. Get Knowledge Details Endpoint

### `GET /api/rag/knowledge/:id/`

Fetches a full knowledge document including all its language sources and ordered segments.

#### Example Request
```http
GET http://localhost:8000/api/rag/knowledge/3ddec49e-17ae-4b3c-bf90-b42e9b7412ef/
```

#### Example Response Body (`200 OK`)
```json
{
  "id": "3ddec49e-17ae-4b3c-bf90-b42e9b7412ef",
  "title": "Company Onboarding & Welcome Orientation",
  "description": "Welcome video training session for new hires.",
  "source_type": "video",
  "processing_status": "completed",
  "created_at": "2026-10-20T14:30:00Z",
  "updated_at": "2026-10-20T14:30:05Z",
  "sources": [
    {
      "id": "18973489-bbf6-467b-b7f4-3122b3889773",
      "language": "en",
      "file_url": "https://example.com/videos/onboarding_en.mp4",
      "duration_seconds": 60.0,
      "page_count": null
    },
    {
      "id": "99883489-aef6-467b-b7f4-4422b3889111",
      "language": "km",
      "file_url": "https://example.com/videos/onboarding_km.mp4",
      "duration_seconds": 60.0,
      "page_count": null
    }
  ],
  "segments": [
    {
      "id": "fff474df-92d6-4753-8403-53158e323368",
      "segment_index": 0,
      "title": "Introduction & Welcome",
      "summary": "Greeting new employees, company mission, and values.",
      "transcript": "Welcome to the company orientation program.",
      "keywords": ["onboarding", "welcome", "values"],
      "possible_questions": [
        "What is covered in the orientation?",
        "Where can I learn about company values?"
      ],
      "start_time_seconds": 0.0,
      "end_time_seconds": 30.0,
      "page_start": null,
      "page_end": null
    }
  ]
}
```

---

## 4. Ingest / Upload Endpoint (Admin / CMS)

### `POST /api/rag/knowledge/`

Uploads and processes a new knowledge item. The backend immediately creates vector embeddings for each segment.

#### Video Upload Request (Using Video URL - Recommended)
```json
{
  "title": "Company Onboarding & Welcome Orientation",
  "description": "Welcome video training session for new hires.",
  "source_type": "video",
  "sources": [
    {
      "language": "en",
      "file_url": "https://example.com/videos/onboarding_en.mp4",
      "duration_seconds": 60.0
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Introduction & Welcome",
      "summary": "Greeting new employees and core values.",
      "transcript": "Welcome to our company orientation session.",
      "start_time_seconds": 0.0,
      "end_time_seconds": 30.0,
      "keywords": ["welcome", "onboarding", "values"],
      "possible_questions": [
        "What is the orientation about?",
        "Where can I learn about company values?"
      ]
    },
    {
      "segment_index": 1,
      "title": "Workspace & Tools Setup",
      "summary": "Slack setup, email accounts, and IT support.",
      "transcript": "Next, let's look at setting up your Slack and email accounts.",
      "start_time_seconds": 30.0,
      "end_time_seconds": 60.0,
      "keywords": ["slack", "it support", "accounts"],
      "possible_questions": [
        "How do I use Slack to talk to IT support?",
        "Who do I contact for IT help?"
      ]
    }
  ]
}
```

#### PDF Upload Request (Using Base64 File Data)
```json
{
  "title": "Employee Handbook",
  "source_type": "pdf",
  "sources": [
    {
      "language": "en",
      "file_data": "JVBERi0xLjQKJcTl8uXrp/Og0MTGCjQgMCBvYmo=...",
      "page_count": 15
    }
  ],
  "segments": [
    {
      "segment_index": 0,
      "title": "Leave Policy",
      "summary": "Annual leave and holiday guidelines.",
      "page_start": 1,
      "page_end": 5,
      "keywords": ["annual leave", "vacation"],
      "possible_questions": ["How do I request annual leave?"]
    }
  ]
}
```

#### Response Body (`201 Created`)
```json
{
  "id": "3ddec49e-17ae-4b3c-bf90-b42e9b7412ef",
  "title": "Company Onboarding & Welcome Orientation",
  "source_type": "video",
  "processing_status": "completed",
  "segments_count": 2,
  "created_at": "2026-10-20T14:30:00Z"
}
```

---

## 5. Frontend Implementation Code Snippets

### A. Video Player Seeking (HTML5 / Vanilla JS)

```javascript
async function searchAndPlayVideo(userQuestion) {
  const response = await fetch("http://localhost:8000/api/rag/knowledge/search/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: userQuestion })
  });

  const data = await response.json();
  if (data.results.length === 0) {
    alert("No matching video segment found.");
    return;
  }

  const bestResult = data.results[0];
  const videoPlayer = document.getElementById("videoPlayer");

  // 1. Set video source URL
  videoPlayer.src = bestResult.matched_source.file_url;

  // 2. Seek to the start timestamp
  videoPlayer.currentTime = bestResult.start_time_seconds; // e.g. 30.0
  videoPlayer.play();

  // 3. Optional: Pause when segment ends
  videoPlayer.ontimeupdate = () => {
    if (videoPlayer.currentTime >= bestResult.end_time_seconds) {
      videoPlayer.pause();
    }
  };
}
```

### B. React Video Player Component

```jsx
import React, { useRef } from 'react';

export function SearchResultVideo({ result }) {
  const videoRef = useRef(null);
  const { matched_source, start_time_seconds, end_time_seconds, title } = result;

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      // Seek directly to start time
      videoRef.current.currentTime = start_time_seconds;
    }
  };

  return (
    <div className="search-result-card">
      <h3>{title}</h3>
      <p>Jump to: {start_time_seconds}s - {end_time_seconds}s</p>

      {/* Browser Media Fragment syntax also supported: #t=30,60 */}
      <video
        ref={videoRef}
        controls
        onLoadedMetadata={handleLoadedMetadata}
        src={`${matched_source.file_url}#t=${start_time_seconds},${end_time_seconds}`}
        style={{ width: "100%", borderRadius: "8px" }}
      />

      {matched_source.is_fallback && (
        <span className="badge-warning">Shown in English (Khmer video unavailable)</span>
      )}
    </div>
  );
}
```

### C. Flutter Video Player

```dart
import 'package:video_player/video_player.dart';

void playSegment(String videoUrl, double startTimeSeconds) async {
  VideoPlayerController controller = VideoPlayerController.networkUrl(Uri.parse(videoUrl));
  await controller.initialize();
  
  // Jump directly to the segment's start time!
  await controller.seekTo(Duration(milliseconds: (startTimeSeconds * 1000).toInt()));
  controller.play();
}
```

---

## 6. TypeScript Types (Ready to Copy-Paste)

Copy these interfaces directly into your frontend `types/rag.ts` file:

```typescript
export interface SearchRequest {
  question: string;
  language?: string;
  top_k?: number;
  threshold?: number;
  weights?: {
    topic?: number;
    question?: number;
    keyword?: number;
    summary?: number;
  };
}

export interface MatchedSource {
  id: string;
  language: string;
  file_url?: string | null;
  duration_seconds?: number | null;
  page_count?: number | null;
  is_fallback: boolean;
}

export interface SearchResultItem {
  segment_id: string;
  knowledge_id: string;
  knowledge_title: string;
  source_type: 'video' | 'pdf' | 'text';
  segment_index: number;
  title?: string | null;
  summary?: string | null;
  transcript?: string | null;
  start_time_seconds?: number | null;
  end_time_seconds?: number | null;
  page_start?: number | null;
  page_end?: number | null;
  keywords: string[];
  score: number;
  confidence: number;
  best_match: string;
  confidence_by_type: {
    keyword?: number;
    question?: number;
    topic?: number;
    summary?: number;
  };
  matched_source: MatchedSource | null;
}

export interface SearchResponse {
  question: string;
  language: string;
  count: number;
  weights_used: Record<string, number>;
  results: SearchResultItem[];
}
```
