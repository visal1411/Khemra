"""EmbeddingTextBuilder - decides WHAT text is embedded for each metadata field.

Input : one segment dict (same shape as video_segments.json / KnowledgeInputSerializer)
Output: list of dicts — each dict becomes one KnowledgeEmbedding row:
  {
    "metadata_type": str,   # name matching MetadataType.name in DB
    "item_index":    int,   # 0 for single items; 0,1,2... for multi-value (questions)
    "text":          str,   # the text to embed
    "field_kwargs":  dict,  # extra fields to store on KnowledgeEmbedding (title/summary/keywords/questions)
  }

Metadata types produced (aligned with ContentType constants):
  keyword  -> ONE item PER keyword (individual vector per keyword)
  question -> ONE item PER question (question-to-question matching is the strongest signal)
  topic    -> the title
  summary  -> the summary
"""


class EmbeddingTextBuilder:
    def build(self, segment):
        items = []

        # keywords -> one embedding per keyword
        for idx, k in enumerate(segment.get("keywords") or []):
            if k and k.strip():
                items.append({
                    "metadata_type": "keyword",
                    "item_index": idx,
                    "text": k.strip(),
                    "field_kwargs": {"keywords": [{"text": k.strip()}]},
                })

        # possible_questions -> one embedding per question
        for idx, q in enumerate(segment.get("possible_questions") or []):
            if q and q.strip():
                items.append({
                    "metadata_type": "question",
                    "item_index": idx,
                    "text": q.strip(),
                    "field_kwargs": {"questions": [{"text": q.strip()}]},
                })

        # title -> topic embedding
        title = (segment.get("title") or "").strip()
        if title:
            items.append({
                "metadata_type": "topic",
                "item_index": 0,
                "text": title,
                "field_kwargs": {"title": title},
            })

        # summary -> summary embedding
        summary = (segment.get("summary") or "").strip()
        if summary:
            items.append({
                "metadata_type": "summary",
                "item_index": 0,
                "text": summary,
                "field_kwargs": {"summary": summary},
            })

        return items
