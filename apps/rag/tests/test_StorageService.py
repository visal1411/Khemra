from unittest.mock import MagicMock, patch
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.rag.services.StorageService import StorageService


class StorageServiceTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("boto3.client")
    def test_generate_presigned_url_pdf_success(self, mock_boto_client):
        # Setup mock S3 client
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://mock-r2.cloudflarestorage.com/bucket/doc.pdf?signed=1"
        mock_boto_client.return_value = mock_s3

        service = StorageService(s3_client=mock_s3)
        result = service.generate_presigned_upload_url(
            filename="my_document.pdf",
            content_type="application/pdf",
            folder="documents",
            expires_in=600,
        )

        self.assertIn("upload_url", result)
        self.assertIn("file_url", result)
        self.assertIn("key", result)
        self.assertEqual(result["expires_in"], 600)

        # Check key and URL format
        self.assertTrue(result["key"].startswith("documents/"))
        self.assertTrue(result["key"].endswith(".pdf"))
        self.assertTrue(result["file_url"].endswith(result["key"]))
        mock_s3.generate_presigned_url.assert_called_once()

    @patch("boto3.client")
    def test_uuid_collision_prevention(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://mock-r2.cloudflarestorage.com/upload"
        service = StorageService(s3_client=mock_s3)

        res1 = service.generate_presigned_upload_url("report.pdf", "application/pdf")
        res2 = service.generate_presigned_upload_url("report.pdf", "application/pdf")

        # Even with the exact same filename, keys must be distinct
        self.assertNotEqual(res1["key"], res2["key"])
        self.assertNotEqual(res1["file_url"], res2["file_url"])

    @patch("apps.rag.services.StorageService.boto3.client")
    def test_api_get_presigned_url_success(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://mock-r2.cloudflarestorage.com/bucket/video.mp4?X-Amz=1"
        mock_boto_client.return_value = mock_s3

        response = self.client.get(
            "/api/rag/storage/presigned-url/",
            {"filename": "onboarding.mp4", "file_type": "video/mp4"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("upload_url", response.data)
        self.assertIn("file_url", response.data)
        self.assertIn("key", response.data)
        self.assertTrue(response.data["key"].endswith(".mp4"))

    def test_api_dangerous_extension_rejected(self):
        for bad_file in ["trojan.exe", "script.sh", "exploit.bat", "webshell.php"]:
            response = self.client.get(
                "/api/rag/storage/presigned-url/",
                {"filename": bad_file, "file_type": "application/octet-stream"},
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Expected {bad_file} to be rejected with 400",
            )
            self.assertIn("Forbidden file extension", response.data["error"])

    def test_api_missing_parameters_rejected(self):
        # Missing both
        res = self.client.get("/api/rag/storage/presigned-url/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing file_type
        res = self.client.get("/api/rag/storage/presigned-url/", {"filename": "doc.pdf"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing extension
        res = self.client.get(
            "/api/rag/storage/presigned-url/",
            {"filename": "file_without_ext", "file_type": "text/plain"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valid file extension", res.data["error"])

    def test_api_empty_file_size_rejected(self):
        # 0 bytes
        res = self.client.get(
            "/api/rag/storage/presigned-url/",
            {"filename": "empty.pdf", "file_type": "application/pdf", "file_size": "0"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File size must be greater than 0 bytes", res.data["error"])

        # Negative bytes
        res = self.client.get(
            "/api/rag/storage/presigned-url/",
            {"filename": "negative.pdf", "file_type": "application/pdf", "file_size": "-50"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
