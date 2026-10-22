import json
from unittest.mock import MagicMock, patch
import requests
from rest_framework import status
from rest_framework.test import APITestCase

from apps.rag.models import MetadataType
from apps.rag.tests.FakeEncoder import FakeEncoder


@patch("apps.rag.services.KnowledgeIngestService.get_encoder", lambda: FakeEncoder())
@patch("apps.rag.services.KnowledgeSearchService.get_encoder", lambda: FakeEncoder())
class AIOverviewAPITest(APITestCase):
    def setUp(self):
        MetadataType.objects.get_or_create(name="title", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="summary", defaults={"weight": 0.25, "is_active": True})
        MetadataType.objects.get_or_create(name="keywords", defaults={"weight": 0.20, "is_active": True})
        MetadataType.objects.get_or_create(name="questions", defaults={"weight": 0.35, "is_active": True})

        self.upload_payload = {
            "title": "IT Portal Handbook",
            "description": "How to access company services",
            "source_type": "text",
            "sources": [
                {"language": "en", "file_data": "dGVzdA==", "duration_seconds": 120.0},
                {"language": "km", "file_data": "dGVzdA==", "duration_seconds": 120.0},
            ],
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Portal Authentication",
                    "summary": "Navigate to https://portal.company.com and enter credentials.",
                    "transcript": "Open your browser, go to portal.company.com, and enter username and password.",
                    "keywords": ["login", "portal", "credentials"],
                    "possible_questions": ["How do I log in?", "How to log in to portal?"],
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 60.0,
                },
                {
                    "segment_index": 1,
                    "title": "Two-Factor Verification",
                    "summary": "Approve the push notification on your authenticator app.",
                    "transcript": "Check your phone for the 2FA push notification and press approve.",
                    "keywords": ["2fa", "mfa", "verification"],
                    "possible_questions": ["How to complete two factor authentication?"],
                    "start_time_seconds": 60.0,
                    "end_time_seconds": 120.0,
                },
            ],
        }

        # Seed knowledge
        res = self.client.post("/api/rag/knowledge/", self.upload_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    @patch("apps.rag.services.GroqLLMService.requests.post")
    def test_ai_overview_successful_synthesis(self, mock_post):
        # First retrieve segments to get valid segment_id for mock response
        search_res = self.client.post("/api/rag/knowledge/search/", {"question": "How to log in?"}, format="json")
        self.assertGreater(search_res.data["count"], 0)
        valid_seg_id = search_res.data["results"][0]["segment_id"]

        mock_llm_json = {
            "summary": "To log in, navigate to the portal and enter your credentials.",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Access the Portal",
                    "instruction": "Open your browser and navigate to portal.company.com.",
                    "segment_id": valid_seg_id,
                }
            ],
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_json)}}]
        }
        mock_post.return_value = mock_response

        payload = {"question": "How to log in?", "language": "en"}
        response = self.client.post("/api/rag/knowledge/search/ai-overview/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["question"], "How to log in?")
        self.assertEqual(response.data["language"], "en")
        self.assertEqual(response.data["summary"], "To log in, navigate to the portal and enter your credentials.")
        self.assertEqual(len(response.data["steps"]), 1)
        self.assertEqual(response.data["steps"][0]["title"], "Access the Portal")
        self.assertEqual(str(response.data["steps"][0]["segment_id"]), valid_seg_id)
        self.assertGreater(len(response.data["results"]), 0)
        self.assertIn("matched_source", response.data["results"][0])

    @patch("apps.rag.services.GroqLLMService.requests.post")
    def test_ai_overview_referential_integrity_fallback(self, mock_post):
        # Return a hallucinated segment_id from LLM
        mock_llm_json = {
            "summary": "Follow these steps.",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step with invalid ID",
                    "instruction": "Do something",
                    "segment_id": "00000000-0000-0000-0000-000000000000",
                }
            ],
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_json)}}]
        }
        mock_post.return_value = mock_response

        response = self.client.post(
            "/api/rag/knowledge/search/ai-overview/",
            {"question": "How to log in?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify fallback segment_id matches top result segment_id
        top_seg_id = str(response.data["results"][0]["segment_id"])
        self.assertEqual(str(response.data["steps"][0]["segment_id"]), top_seg_id)

    @patch("apps.rag.services.GroqLLMService.requests.post")
    def test_ai_overview_zero_segments_bypasses_llm(self, mock_post):
        # Query with threshold 1.0 so no segments match
        response = self.client.post(
            "/api/rag/knowledge/search/ai-overview/",
            {"question": "Irrelevant query", "threshold": 1.0},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertIsNone(response.data["summary"])
        self.assertEqual(response.data["steps"], [])
        self.assertEqual(response.data["results"], [])
        mock_post.assert_not_called()

    @patch("apps.rag.services.GroqLLMService.requests.post")
    def test_ai_overview_llm_timeout_graceful_degradation(self, mock_post):
        # Simulate LLM request timeout
        mock_post.side_effect = requests.exceptions.Timeout("Groq timeout")

        response = self.client.post(
            "/api/rag/knowledge/search/ai-overview/",
            {"question": "How to log in?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["summary"])
        self.assertEqual(response.data["steps"], [])
        self.assertGreater(len(response.data["results"]), 0)

    @patch("apps.rag.services.GroqLLMService.requests.post")
    def test_ai_overview_llm_500_graceful_degradation(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        response = self.client.post(
            "/api/rag/knowledge/search/ai-overview/",
            {"question": "How to log in?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["summary"])
        self.assertEqual(response.data["steps"], [])
        self.assertGreater(len(response.data["results"]), 0)

    def test_ai_overview_empty_question_validation_error(self):
        response = self.client.post(
            "/api/rag/knowledge/search/ai-overview/",
            {"question": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
