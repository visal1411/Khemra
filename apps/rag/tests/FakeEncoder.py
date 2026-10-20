"""FakeEncoder - tiny deterministic bag-of-words encoder for tests (no model download).
Same interface as Encoder.encode()."""
import hashlib
import re

import numpy as np


class FakeEncoder:
    DIMENSIONS = 384

    def encode(self, texts, normalize_embeddings=True):
        single = isinstance(texts, str)
        vecs = np.array([self._one(t) for t in ([texts] if single else texts)], dtype="float32")
        if normalize_embeddings:
            vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs[0] if single else vecs

    def _one(self, text):
        vec = np.zeros(self.DIMENSIONS)
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % self.DIMENSIONS] += 1.0
        if not vec.any():
            vec[0] = 1.0
        return vec
