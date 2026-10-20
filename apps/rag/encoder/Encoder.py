"""Encoder - embedding model (all-MiniLM-L6-v2 via fastembed/ONNX, no PyTorch).
Loaded once, reused for every request (see get_encoder)."""
import os

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_encoder = None


class Encoder:
    DIMENSIONS = 384

    def __init__(self):
        from fastembed import TextEmbedding  # lazy import
        cache = os.environ.get("FASTEMBED_CACHE_DIR")
        print(f"[encoder] Loading model: {MODEL_NAME}")
        self.model = TextEmbedding(model_name=MODEL_NAME, cache_dir=cache)
        print("[encoder] Model loaded.")

    def encode(self, texts, normalize_embeddings=True):
        """str -> 1-D vector, list[str] -> 2-D array (unit length)."""
        single = isinstance(texts, str)
        vecs = np.array(list(self.model.embed([texts] if single else texts)), dtype="float32")
        if normalize_embeddings:
            vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs[0] if single else vecs


def get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = Encoder()
    return _encoder
