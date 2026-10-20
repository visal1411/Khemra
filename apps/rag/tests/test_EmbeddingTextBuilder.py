from django.test import SimpleTestCase

from apps.rag.services.EmbeddingTextBuilder import EmbeddingTextBuilder


class EmbeddingTextBuilderTest(SimpleTestCase):
    def test_one_row_per_metadata_item(self):
        items = EmbeddingTextBuilder().build({
            "title": "Sign up", "summary": "User signs up.",
            "keywords": ["otp", "sms"], "possible_questions": ["How?", "Why?"],
        })
        self.assertEqual(items, [
            ("keyword", "otp, sms"), ("question", "How?"), ("question", "Why?"),
            ("topic", "Sign up"), ("summary", "User signs up."),
        ])

    def test_skips_empty_fields(self):
        self.assertEqual(EmbeddingTextBuilder().build({"title": "T"}), [("topic", "T")])
