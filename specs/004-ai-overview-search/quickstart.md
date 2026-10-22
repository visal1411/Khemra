# Quickstart: AI Overview Search with Groq

**Feature**: `004-ai-overview-search`

---

## 1. Setup Environment Variables

Add your Groq API credentials to your `.env` file:

```dotenv
# Groq LLM Configuration
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

*(Note: If `GROQ_MODEL` is not specified, it defaults to `llama-3.3-70b-versatile`).*

---

## 2. Test via cURL

```bash
curl -X POST http://localhost:8000/api/rag/knowledge/search/ai-overview/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I log into the portal?",
    "language": "en",
    "top_k": 3
  }'
```

---

## 3. Expected Output

```json
{
  "question": "How do I log into the portal?",
  "language": "en",
  "summary": "To log in, open the official portal, click Sign In on the top right, and type your username and password.",
  "steps": [
    {
      "step_number": 1,
      "title": "Open portal",
      "instruction": "Launch your browser and go to the portal.",
      "segment_id": "c29385b3-2222-42ce-92dc-962bb1770b7d"
    },
    {
      "step_number": 2,
      "title": "Enter credentials",
      "instruction": "Enter your username and password and press enter.",
      "segment_id": "d38496c4-3333-42ce-92dc-962bb1770b7d"
    }
  ],
  "count": 2,
  "weights_used": { "question": 0.4, "keyword": 0.3, "summary": 0.2, "topic": 0.1 },
  "results": [
    {
      "segment_id": "c29385b3-2222-42ce-92dc-962bb1770b7d",
      "knowledge_title": "Portal Guide",
      "source_type": "video",
      "start_time_seconds": 0.0,
      "end_time_seconds": 30.0,
      "matched_source": { "file_url": "https://pub-...r2.dev/videos/portal.mp4" }
    }
  ]
}
```
