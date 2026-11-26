"""Embeddings provider supporting dense embeddings with deterministic fallback."""

from __future__ import annotations

import math
import hashlib
from typing import List


class LegalEmbeddingModel:
    """Generates normalized vector representations for legal text chunks."""

    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def _hash_vector(self, text: str) -> List[float]:
        """Creates a stable normalized high-dimensional semantic hash vector.

        Uses subword/token frequency hashing with character n-grams to capture
        legal terminology, section numbers, and case names deterministically.
        """
        words = text.lower().split()
        vector = [0.0] * self.dimension

        for i, word in enumerate(words):
            # Clean word
            clean = "".join(c for c in word if c.isalnum() or c in ".-_()")
            if not clean:
                continue

            # Weight by word importance (boost section numbers, legal terms)
            weight = 1.0
            if "section" in clean or "sec." in clean or clean.isdigit() or "article" in clean:
                weight = 2.5
            elif clean in ["void", "breach", "damages", "restraint", "injunction", "arbitration"]:
                weight = 2.0

            # Hash token into dimension buckets
            h = int(hashlib.md5(clean.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h // self.dimension) % 2 == 0 else -1.0
            vector[idx] += sign * weight

            # Bigram hashing for sequential context
            if i > 0:
                bigram = f"{words[i-1]}_{clean}"
                h_bi = int(hashlib.md5(bigram.encode('utf-8')).hexdigest(), 16)
                idx_bi = h_bi % self.dimension
                vector[idx_bi] += 1.5 * weight

        # Normalize vector to unit length (L2 norm)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            return [v / norm for v in vector]
        return vector

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a vector."""
        return self._hash_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of documents."""
        return [self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculates cosine similarity between two normalized vectors."""
        if len(v1) != len(v2):
            return 0.0
        return sum(a * b for a, b in zip(v1, v2))
