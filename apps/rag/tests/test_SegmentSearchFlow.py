"""End-to-end (needs Postgres + pgvector): ingest JSON -> search -> API."""
import json
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from rest_framework.test import APITestCase

from apps.rag.models import SegmentEmbedding, Video, VideoSegment
from apps.rag.services.SegmentIngestService import SegmentIngestService
from apps.rag.tests.FakeEncoder import FakeEncoder

SEG = [
    {"segment_id": "S-01", "video_id": "V-1", "time": "00:00 - 00:09", "title": "Account sign up",
     "summary": "User taps Sign Up and enters name phone and password.",
     "keywords": ["sign up", "password"], "possible_questions": ["How do I create an account?", "Which details do I enter?"]},
    {"segment_id": "S-02", "video_id": "V-1", "time": "00:10 - 00:19", "title": "SMS verification",
     "summary": "User receives a six digit SMS code and verifies the phone number.",
     "keywords": ["sms", "otp"], "possible_questions": ["How do I verify my phone number?"]},
]


@patch("apps.rag.services.SegmentIngestService.get_encoder", lambda: FakeEncoder())
@patch("apps.rag.services.SegmentSearchService.get_encoder", lambda: FakeEncoder())
class SegmentSearchFlowTest(APITestCase):
    def test_ingest_creates_three_tables(self):
        res = SegmentIngestService().upsert_many(SEG)
        self.assertEqual(res, {"created": 2, "updated": 0})
        self.assertEqual(Video.objects.get(pk="V-1").duration_seconds, 19)
        # S-01: keyword + 2 questions + topic + summary = 5 ; S-02: 1+1+1+1 = 4
        self.assertEqual(SegmentEmbedding.objects.filter(segment_id="S-01").count(), 5)
        self.assertEqual(SegmentEmbedding.objects.filter(segment_id="S-02").count(), 4)
        self.assertEqual(SegmentEmbedding.objects.count(), 9)

    def test_reload_is_idempotent(self):
        SegmentIngestService().upsert_many(SEG)
        res = SegmentIngestService().upsert_many(SEG)
        self.assertEqual(res, {"created": 0, "updated": 2})
        self.assertEqual(SegmentEmbedding.objects.count(), 9)

    def test_search_ranks_correct_segment_first(self):
        SegmentIngestService().upsert_many(SEG)
        r = self.client.post("/api/rag/search/", {"question": "How do I verify my phone number?", "threshold": 0.0}, format="json")
        self.assertEqual(r.status_code, 200)
        top = r.data["results"][0]
        self.assertEqual(top["segment_id"], "S-02")
        self.assertEqual(top["time"], "00:10 - 00:19")
        self.assertEqual(top["confidence_by_type"]["question"], 100.0)  # identical question
        self.assertEqual(top["best_match"], "question")
        self.assertEqual(set(top["confidence_by_type"]), {"keyword", "question", "topic", "summary"})
        self.assertGreater(top["score"], r.data["results"][1]["score"])

    def test_custom_weights_and_validation(self):
        SegmentIngestService().upsert_many(SEG)
        ok = self.client.post("/api/rag/search/", {"question": "sign up password", "weights": {"keyword": 1}, "threshold": 0.0}, format="json")
        self.assertEqual(ok.data["weights"]["keyword"], 1.0)
        self.assertEqual(ok.data["results"][0]["segment_id"], "S-01")
        bad = self.client.post("/api/rag/search/", {"question": "x", "weights": {"bogus": 1}}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_crud_endpoints(self):
        body = dict(SEG[0], segment_id="S-NEW")
        self.assertEqual(self.client.post("/api/rag/segments/", body, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/rag/segments/", body, format="json").status_code, 409)
        self.assertEqual(self.client.post("/api/rag/segments/", dict(body, segment_id="X", time="bad"), format="json").status_code, 400)
        g = self.client.get("/api/rag/segments/S-NEW/")
        self.assertEqual(g.data["keywords"], ["sign up", "password"])
        self.assertEqual(self.client.delete("/api/rag/segments/S-NEW/").status_code, 204)
        self.assertEqual(SegmentEmbedding.objects.filter(segment_id="S-NEW").count(), 0)  # cascade
        self.assertEqual(self.client.get("/api/rag/segments/S-NEW/").status_code, 404)

    def test_real_seed_file_roundtrip(self):
        path = Path(settings.BASE_DIR) / "seed_data" / "video_segments.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        SegmentIngestService().upsert_many(data)
        exported = self.client.get("/api/rag/segments/export/").data
        self.assertEqual(len(exported), len(data))
        by_id = {e["segment_id"]: e for e in exported}
        for src in data:  # export == original seed file (same shape, nothing lost)
            self.assertEqual(by_id[src["segment_id"]], src)
