from django.test import SimpleTestCase

from apps.rag.services.EmbeddingTextBuilder import EmbeddingTextBuilder


class EmbeddingTextBuilderTest(SimpleTestCase):
    def test_one_row_per_metadata_item(self):
        items = EmbeddingTextBuilder().build({
            "title": "Sign up", "summary": "User signs up.",
            "keywords": ["otp", "sms"], "possible_questions": ["How?", "Why?"],
        })
        self.assertEqual(len(items), 6)  # 2 keywords + 2 questions + 1 topic + 1 summary
        self.assertEqual(
            [(it["metadata_type"], it["item_index"], it["text"]) for it in items],
            [
                ("keyword", 0, "otp"),
                ("keyword", 1, "sms"),
                ("question", 0, "How?"),
                ("question", 1, "Why?"),
                ("topic", 0, "Sign up"),
                ("summary", 0, "User signs up."),
            ]
        )

    def test_skips_empty_fields(self):
        items = EmbeddingTextBuilder().build({"title": "T"})
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["metadata_type"], "topic")
        self.assertEqual(items[0]["text"], "T")
