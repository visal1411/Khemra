# Django + pgvector Video Segment Search API

## Run
```bash
docker compose up --build
```
First start downloads the MiniLM ONNX model (~90 MB, cached in a volume). The image has no PyTorch, so it is small and builds fast. On startup it
runs migrations (which enable pgvector) and loads `seed_data/video_segments.json`.

## Data file
`seed_data/video_segments.json` - edit it, then reload:
```bash
docker compose exec web python manage.py load_segments seed_data/video_segments.json
```
Dump what is actually in the DB back to JSON to check it:
```bash
docker compose exec web python manage.py export_segments          # -> seed_data/exported_segments.json
curl http://localhost:8000/api/rag/segments/export/               # same, over HTTP
```

## Endpoints (base: http://localhost:8000/api/rag/)
| Method | URL | What |
|---|---|---|
| GET | segments/ | list all |
| GET | segments/export/ | all, in video_segments.json format |
| POST | segments/ | add one segment (embeds it) |
| GET / DELETE | segments/<segment_id>/ | one segment |
| POST | search/ | semantic search |

```bash
curl -X POST http://localhost:8000/api/rag/search/ \
  -H "Content-Type: application/json" \
  -d '{"question": "how do I log in with the QR code?", "top_k": 3, "threshold": 0.3}'
```
Optional `"weights": {"question": 0.6, "summary": 0.4}` replaces the default weights for that request.

Each result keeps the old fields and adds the confidence of every metadata type:
```json
{
  "segment_id": "SEG-000124-03", "video_id": "VID-000124", "time": "00:20 - 00:29",
  "title": "...", "summary": "...", "keywords": [], "possible_questions": [],
  "score": 0.6123,                 // combined, 0..1
  "confidence": 61.23,             // combined, percent
  "best_match": "question",        // which metadata matched best
  "confidence_by_type": {"keyword": 48.1, "question": 83.9, "topic": 55.0, "summary": 57.7}
}
```

Postgres is also exposed on host port 5433 (user/password: postgres/postgres, db: mydatabase).

## If Docker is flaky: DB in Docker, Django on Windows
```powershell
docker compose up -d db
py -m venv .venv ; .\.venv\Scripts\activate
pip install -r requirements.txt
$env:DB_HOST="localhost"; $env:DB_PORT="5433"
python manage.py migrate
python manage.py load_segments seed_data/video_segments.json
python manage.py runserver
```

## Database design (3 tables)
```
videos (video_id PK, title, duration_seconds)
  └─< video_segments (segment_id PK, video_id FK, start_time interval, end_time interval,
                      keyword, question, topic, summary)
        └─< segment_embedding (id serial PK, segment_id FK, content_type, embedding vector(384))
```
`content_type` is `keyword | question | topic | summary`. Every metadata field gets its own vector
(each *question* gets one vector too). Search = best cosine similarity per type -> weighted average.
Default weights: keyword 0.20, question 0.35, topic 0.20, summary 0.25. Change them per request, or globally
with `RAG_WEIGHTS = {...}` in `settings.py`.

## Code layout (one class per file, file named after the class)
```
apps/rag/
  constants/  ContentType.py
  models/     Video.py  VideoSegment.py  SegmentEmbedding.py
  encoder/    Encoder.py
  utils/      TimeRangeParser.py  ListTextCodec.py
  services/   EmbeddingTextBuilder.py  SegmentIngestService.py
              ScoreCombiner.py  SegmentScore.py  SegmentSearchService.py
  serializers/ SegmentInputSerializer.py  SearchRequestSerializer.py
  views/      SegmentListCreateAPI.py  SegmentExportAPI.py  SegmentDetailAPI.py  SearchAPI.py
  admin/      VideoAdmin.py  VideoSegmentAdmin.py  SegmentEmbeddingAdmin.py
  tests/      FakeEncoder.py + one test file per class
```
Run tests: `docker compose exec web python manage.py test apps.rag`
