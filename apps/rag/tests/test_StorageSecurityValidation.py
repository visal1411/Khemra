from django.test import TestCase, override_settings
from apps.rag.serializers import KnowledgeInputSerializer


class StorageSecurityValidationTest(TestCase):
    def setUp(self):
        self.base_payload = {
            "title": "Cloud Storage Test Guide",
            "source_type": "pdf",
            "sources": [
                {
                    "language": "en",
                    "file_url": "https://my-bucket.s3.amazonaws.com/handbook.pdf",
                }
            ],
            "segments": [
                {
                    "segment_index": 0,
                    "title": "Overview",
                    "summary": "Valid summary.",
                    "page_start": 1,
                    "page_end": 5,
                }
            ],
        }

    @override_settings(ALLOWED_STORAGE_HOSTS=["my-bucket.s3.amazonaws.com", "example.com"])
    def test_authorized_s3_storage_url_passes(self):
        serializer = KnowledgeInputSerializer(data=self.base_payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    @override_settings(ALLOWED_STORAGE_HOSTS=["my-bucket.s3.amazonaws.com"])
    def test_unauthorized_storage_domain_is_rejected(self):
        payload = dict(self.base_payload)
        payload["sources"] = [
            {"language": "en", "file_url": "https://untrusted-attacker-site.com/doc.pdf"}
        ]
        serializer = KnowledgeInputSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("sources", serializer.errors)
        error_msg = str(serializer.errors["sources"])
        self.assertIn("Unauthorized storage domain", error_msg)

    def test_executable_extension_is_blocked(self):
        payload = dict(self.base_payload)
        payload["sources"] = [
            {"language": "en", "file_url": "https://s3.amazonaws.com/setup.exe"}
        ]
        serializer = KnowledgeInputSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        error_msg = str(serializer.errors["sources"])
        self.assertIn("Forbidden file extension", error_msg)

    def test_mismatched_source_type_extension_is_rejected(self):
        payload = dict(self.base_payload)
        # Uploading an .mp4 video link under source_type: 'pdf'
        payload["sources"] = [
            {"language": "en", "file_url": "https://s3.amazonaws.com/video.mp4"}
        ]
        serializer = KnowledgeInputSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        error_msg = str(serializer.errors["sources"])
        self.assertIn("does not match expected source type 'pdf'", error_msg)
