"""Embedding service for comprehension semantic similarity."""

import numpy as np
from sentence_transformers import SentenceTransformer

from comprehension.schema import Comprehension


class ComprehensionEmbedder:
    """Generates semantic embeddings for comprehension belief statements.

    Uses sentence-transformers with all-MiniLM-L6-v2 model to create
    384-dimensional normalized embeddings. Embeddings capture the
    structural shape of belief transformations (prior + posterior).

    Thread safety: Model is loaded once in __init__ and can be safely
    reused across threads for inference.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder with specified model.

        Args:
            model_name: Name of the sentence-transformers model.
                Default is "all-MiniLM-L6-v2" (384 dimensions, fast).
        """
        self._model = SentenceTransformer(model_name)

    def embed(self, comprehension: Comprehension) -> np.ndarray:
        """Embed a comprehension's belief structure.

        Combines prior and posterior statements to capture the shape
        of the belief transformation, not just the subject matter.

        Args:
            comprehension: Comprehension to embed.

        Returns:
            Normalized 384-dimensional embedding as np.ndarray.
        """
        text = f"{comprehension.prior.statement} {comprehension.posterior.statement}"
        return self._model.encode(text, normalize_embeddings=True)

    def embed_text(self, text: str) -> np.ndarray:
        """Embed arbitrary text.

        Lower-level method for embedding any text string.
        Useful for testing and direct text embedding.

        Args:
            text: Text to embed.

        Returns:
            Normalized 384-dimensional embedding as np.ndarray.
        """
        return self._model.encode(text, normalize_embeddings=True)
