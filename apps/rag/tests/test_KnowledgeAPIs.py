from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.rag.models import MetadataType
from apps.rag.tests.FakeEncoder import FakeEncoder


@patch("apps.rag.services.KnowledgeIngestService.get_encoder", lambda: FakeEncoder())
@patch("apps.rag.services.KnowledgeSearchService.get_encoder", lambda: FakeEncoder())
class KnowledgeAPIsTest(APITestCase):
    def setUp(self):
        MetadataType.objects.get_or_create(name="title", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="summary", defaults={"weight": 0.25, "is_active": True})
        MetadataType.objects.get_or_create(name="keywords", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="questions", defaults={"weight": 0.35, "is_active": True})

        self.valid_upload_payload = {
            "title": "Employee Handbook",
            "description": "Rules and guidelines",
            "source_type": "video",
            "sources": [
                {"language": "en", "file_data": "dGVzdA==", "duration_seconds": 120.0},
                {"language": "km", "file_data": "dGVzdA==", "duration_seconds": 120.0},
            ],
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Working Hours",
                    "summary": "Core hours are 9 AM to 5 PM.",
                    "transcript": "All full-time staff must be available from 9 AM to 5 PM.",
                    "keywords": ["hours", "schedule"],
                    "possible_questions": ["What are the working hours?"],
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 60.0,
                },
                {
                    "segment_index": 1,
                    "title": "Paid Time Off",
                    "summary": "Employees get 18 days of paid leave annually.",
                    "transcript": "Paid time off accrues at 1.5 days per month totaling 18 days.",
                    "keywords": ["leave", "pto", "vacation"],
                    "possible_questions": ["How many vacation days do I get?"],
                    "start_time_seconds": 60.0,
                    "end_time_seconds": 120.0,
                },
            ],
        }

    def test_upload_knowledge_success(self):
        response = self.client.post("/api/rag/knowledge/", self.valid_upload_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["title"], "Employee Handbook")
        self.assertEqual(response.data["processing_status"], "completed")
        self.assertEqual(response.data["segments_count"], 2)

    def test_upload_knowledge_validation_error(self):
        bad_payload = {"title": "", "source_type": "invalid_type"}
        response = self.client.post("/api/rag/knowledge/", bad_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_knowledge_detail_success(self):
        create_res = self.client.post("/api/rag/knowledge/", self.valid_upload_payload, format="json")
        knowledge_id = create_res.data["id"]

        detail_res = self.client.get(f"/api/rag/knowledge/{knowledge_id}/")
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["id"], knowledge_id)
        self.assertEqual(len(detail_res.data["sources"]), 2)
        self.assertEqual(len(detail_res.data["segments"]), 2)

    def test_get_knowledge_detail_not_found(self):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        detail_res = self.client.get(f"/api/rag/knowledge/{fake_uuid}/")
        self.assertEqual(detail_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_knowledge_endpoint(self):
        self.client.post("/api/rag/knowledge/", self.valid_upload_payload, format="json")

        search_payload = {
            "question": "What are the working hours?",
            "language": "km",
            "threshold": 0.0,
        }
        res = self.client.post("/api/rag/search/", search_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(res.data["count"], 0)

        top_result = res.data["results"][0]
        self.assertEqual(top_result["segment_index"], 0)
        self.assertEqual(top_result["matched_source"]["language"], "km")
        self.assertFalse(top_result["matched_source"]["is_fallback"])
