from django.test import TestCase
from apps.rag.models import MetadataType
from apps.rag.services.KnowledgeIngestService import KnowledgeIngestService
from apps.rag.services.KnowledgeSearchService import KnowledgeSearchService
from apps.rag.tests.FakeEncoder import FakeEncoder


class KnowledgeSearchServiceTest(TestCase):
    def setUp(self):
        self.encoder = FakeEncoder()
        MetadataType.objects.get_or_create(name="title", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="summary", defaults={"weight": 0.25, "is_active": True})
        MetadataType.objects.get_or_create(name="keywords", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="questions", defaults={"weight": 0.35, "is_active": True})

        self.ingest_service = KnowledgeIngestService(encoder=self.encoder)
        self.search_service = KnowledgeSearchService(encoder=self.encoder)

        self.knowledge = self.ingest_service.ingest({
            "title": "Account Walkthrough",
            "source_type": "video",
            "sources": [
                {"language": "en", "file_data": "dGVzdA==", "duration_seconds": 180.0},
                {"language": "km", "file_data": "dGVzdA==", "duration_seconds": 180.0},
            ],
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Registration Form",
                    "summary": "Fill out email and password to sign up.",
                    "keywords": ["register", "sign up"],
                    "possible_questions": ["How do I register an account?"],
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 60.0,
                },
                {
                    "segment_index": 1,
                    "title": "Two-Factor Auth",
                    "summary": "Scan QR code with authenticator app.",
                    "keywords": ["2fa", "security", "qr"],
                    "possible_questions": ["How do I configure two-factor authentication?"],
                    "start_time_seconds": 60.0,
                    "end_time_seconds": 180.0,
                },
            ],
        })

    def test_search_ranks_matching_segment_first(self):
        res = self.search_service.search(
            question="How do I configure two-factor authentication?",
            language="km",
            threshold=0.0,
        )
        self.assertGreater(res["count"], 0)
        top = res["results"][0]
        self.assertEqual(top["segment_index"], 1)
        self.assertEqual(top["title"], "Two-Factor Auth")
        self.assertEqual(top["best_match"], "question")
        self.assertIn("question", top["confidence_by_type"])

    def test_multi_language_source_matching(self):
        # Query with Khmer language requested
        res_km = self.search_service.search(
            question="How do I register an account?",
            language="km",
            threshold=0.0,
        )
        matched_km = res_km["results"][0]["matched_source"]
        self.assertEqual(matched_km["language"], "km")
        self.assertFalse(matched_km["is_fallback"])

        # Query with Chinese language (not uploaded -> should fallback to English)
        res_zh = self.search_service.search(
            question="How do I register an account?",
            language="zh",
            threshold=0.0,
        )
        matched_zh = res_zh["results"][0]["matched_source"]
        self.assertEqual(matched_zh["language"], "en")
        self.assertTrue(matched_zh["is_fallback"])

    def test_threshold_filtering(self):
        # Very high threshold should filter out results
        res = self.search_service.search(
            question="Completely unrelated topic about cooking recipes",
            threshold=0.99,
        )
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["results"], [])

    def test_search_deduplicates_identical_segments(self):
        # Ingest the exact same knowledge payload again
        self.ingest_service.ingest({
            "title": "User Account Management",
            "source_type": "video",
            "sources": [{"language": "en", "file_url": "https://example.com/v_en.mp4"}],
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Account Registration",
                    "summary": "Fill out email and password to sign up.",
                    "keywords": ["register", "sign up"],
                    "possible_questions": ["How do I register an account?"],
                },
            ],
        })

        res = self.search_service.search(
            question="How do I register an account?",
            threshold=0.0,
            top_k=5,
        )
        # Even though segment 0 was ingested twice across 2 knowledge entities,
        # it should only appear once in search results
        registered_segments = [r for r in res["results"] if r["title"] == "Account Registration"]
        self.assertEqual(len(registered_segments), 1)
