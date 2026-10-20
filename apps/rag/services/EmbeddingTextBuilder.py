"""EmbeddingTextBuilder - decides WHAT text is embedded for each metadata field.

Input : one segment dict (same shape as video_segments.json)
Output: list of (content_type, text) -> each becomes one row in segment_embedding

  keyword  -> all keywords joined in ONE text (single keywords are too short to embed well)
  question -> ONE text PER question (question-to-question matching is the strongest signal)
  topic    -> the title
  summary  -> the summary
"""
from apps.rag.constants.ContentType import ContentType


class EmbeddingTextBuilder:
    def build(self, segment):
        items = []

        keywords = [k.strip() for k in segment.get("keywords") or [] if k and k.strip()]
        if keywords:
            items.append((ContentType.KEYWORD.value, ", ".join(keywords)))

        for q in segment.get("possible_questions") or []:
            if q and q.strip():
                items.append((ContentType.QUESTION.value, q.strip()))

        title = (segment.get("title") or "").strip()
        if title:
            items.append((ContentType.TOPIC.value, title))

        summary = (segment.get("summary") or "").strip()
        if summary:
            items.append((ContentType.SUMMARY.value, summary))

        return items
