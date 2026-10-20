import base64
from django.test import TestCase
from apps.rag.models import (
    Knowledge,
    KnowledgeSource,
    KnowledgeSegment,
    MetadataType,
    KnowledgeEmbedding,
    ProcessingStatus,
)
from apps.rag.services.KnowledgeIngestService import KnowledgeIngestService
from apps.rag.tests.FakeEncoder import FakeEncoder


class KnowledgeIngestServiceTest(TestCase):
    def setUp(self):
        self.fake_encoder = FakeEncoder()
        self.service = KnowledgeIngestService(encoder=self.fake_encoder)
        MetadataType.objects.get_or_create(name="title", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="summary", defaults={"weight": 0.25, "is_active": True})
        MetadataType.objects.get_or_create(name="keywords", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="questions", defaults={"weight": 0.35, "is_active": True})

    def test_ingest_creates_all_entities_and_embeddings(self):
        payload = {
            "title": "Onboarding Walkthrough",
            "description": "Guide for new employees",
            "source_type": "video",
            "sources": [
                {
                    "language": "en",
                    "file_data": base64.b64encode(b"dummy en video bytes").decode(),
                    "duration_seconds": 120.0,
                },
                {
                    "language": "km",
                    "file_data": base64.b64encode(b"dummy km video bytes").decode(),
                    "duration_seconds": 120.0,
                },
            ],
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Welcome Chapter",
                    "summary": "Brief introduction",
                    "transcript": "Hello and welcome to the team.",
                    "keywords": ["welcome", "team"],
                    "possible_questions": ["What is this team?", "Where do I start?"],
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 60.0,
                },
                {
                    "segment_index": 1,
                    "title": "Account Setup",
                    "summary": "Setting up password",
                    "transcript": "Enter your credentials here.",
                    "keywords": ["account", "password"],
                    "possible_questions": ["How do I set my password?"],
                    "start_time_seconds": 60.0,
                    "end_time_seconds": 120.0,
                },
            ],
        }

        knowledge = self.service.ingest(payload)
        self.assertIsNotNone(knowledge.id)
        self.assertEqual(knowledge.processing_status, ProcessingStatus.COMPLETED)
        self.assertEqual(KnowledgeSource.objects.filter(knowledge=knowledge).count(), 2)
        self.assertEqual(KnowledgeSegment.objects.filter(knowledge=knowledge).count(), 2)

        # Verify embeddings created (Segment 0: title + summary + keywords + 2 questions = 5; Segment 1: 1+1+1+1 = 4 -> Total 9)
        embeddings = KnowledgeEmbedding.objects.filter(segment__knowledge=knowledge)
        self.assertEqual(embeddings.count(), 9)

        # Verify vector dimension is 1536
        for emb in embeddings:
            self.assertEqual(len(emb.embedding_vector), 1536)
            self.assertEqual(emb.model_name, "fastembed/model")

    def test_atomic_rollback_on_failure(self):
        class BrokenEncoder:
            def encode(self, texts, normalize_embeddings=True):
                raise RuntimeError("Vector inference exploded!")

        broken_service = KnowledgeIngestService(encoder=BrokenEncoder())
        payload = {
            "title": "Failing Ingestion",
            "source_type": "text",
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Broken Segment",
                    "summary": "Will fail",
                }
            ],
        }

        with self.assertRaises(RuntimeError):
            broken_service.ingest(payload)

        self.assertEqual(Knowledge.objects.filter(title="Failing Ingestion").count(), 0)
        self.assertEqual(KnowledgeSegment.objects.count(), 0)
