"""Tests for ComprehensionEmbedder."""

from datetime import datetime

import numpy as np
import pytest

from comprehension.convergence.embedder import ComprehensionEmbedder
from comprehension.schema import (
    BeliefPrior,
    BeliefPosterior,
    Comprehension,
    ConfidenceLevel,
)


@pytest.fixture(scope="module")
def embedder():
    """Create embedder once for all tests (model loading is expensive)."""
    return ComprehensionEmbedder()


@pytest.fixture
def sample_comprehension():
    """Create a sample comprehension for testing."""
    return Comprehension(
        id="comp-test-001",
        topic="API authentication",
        domain="api",
        prior=BeliefPrior(
            statement="API uses basic auth",
            confidence=ConfidenceLevel.MEDIUM,
            source="documentation",
        ),
        posterior=BeliefPosterior(
            statement="API uses JWT tokens with refresh rotation",
            confidence=ConfidenceLevel.HIGH,
            update_reasoning="Observed Authorization header format",
            observations_used=["obs-001"],
        ),
        observations=["obs-001"],
        created=datetime.now(),
        updated=datetime.now(),
    )


class TestEmbedderShape:
    """Tests for embedding output shape."""

    def test_embed_returns_correct_shape(self, embedder, sample_comprehension):
        """Embedding should be 384-dimensional."""
        embedding = embedder.embed(sample_comprehension)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)

    def test_embed_text_returns_correct_shape(self, embedder):
        """embed_text should also return 384-dimensional vector."""
        embedding = embedder.embed_text("test text")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)


class TestEmbedderNormalization:
    """Tests for embedding normalization."""

    def test_embedding_is_normalized(self, embedder, sample_comprehension):
        """Embedding should have L2 norm of approximately 1.0."""
        embedding = embedder.embed(sample_comprehension)
        l2_norm = np.linalg.norm(embedding)

        assert np.isclose(l2_norm, 1.0, atol=1e-5)

    def test_embed_text_is_normalized(self, embedder):
        """embed_text should also produce normalized vectors."""
        embedding = embedder.embed_text("any text should be normalized")
        l2_norm = np.linalg.norm(embedding)

        assert np.isclose(l2_norm, 1.0, atol=1e-5)


class TestEmbedderSemanticSimilarity:
    """Tests for semantic similarity properties."""

    def test_similar_texts_have_higher_similarity(self, embedder):
        """Semantically similar texts should have higher cosine similarity."""
        # Two similar texts about authentication
        text_a = "The API uses JWT tokens for authentication"
        text_b = "Authentication is handled via JSON Web Tokens"

        # A very different text
        text_c = "The weather is sunny today"

        emb_a = embedder.embed_text(text_a)
        emb_b = embedder.embed_text(text_b)
        emb_c = embedder.embed_text(text_c)

        # Cosine similarity (embeddings are normalized, so dot product = cosine)
        similarity_ab = np.dot(emb_a, emb_b)
        similarity_ac = np.dot(emb_a, emb_c)

        # Similar texts should have higher similarity than dissimilar
        assert similarity_ab > similarity_ac
        # Similar texts should be reasonably close (>0.5)
        assert similarity_ab > 0.5
        # Dissimilar texts should be far apart (<0.5)
        assert similarity_ac < 0.5

    def test_identical_texts_have_maximum_similarity(self, embedder):
        """Identical texts should have similarity of ~1.0."""
        text = "The database uses PostgreSQL for persistence"

        emb_a = embedder.embed_text(text)
        emb_b = embedder.embed_text(text)

        similarity = np.dot(emb_a, emb_b)

        assert np.isclose(similarity, 1.0, atol=1e-5)

    def test_comprehension_embeds_both_prior_and_posterior(self, embedder):
        """Comprehension embedding should capture both prior and posterior."""
        # Create two comprehensions with same prior but different posterior
        prior = BeliefPrior(
            statement="Data is stored locally",
            confidence=ConfidenceLevel.MEDIUM,
            source="assumption",
        )

        comp_a = Comprehension(
            id="comp-a",
            topic="storage",
            domain="database",
            prior=prior,
            posterior=BeliefPosterior(
                statement="Data is stored in cloud S3 buckets",
                confidence=ConfidenceLevel.HIGH,
                update_reasoning="Observed S3 API calls",
                observations_used=["obs-1"],
            ),
            observations=["obs-1"],
            created=datetime.now(),
            updated=datetime.now(),
        )

        comp_b = Comprehension(
            id="comp-b",
            topic="storage",
            domain="database",
            prior=prior,
            posterior=BeliefPosterior(
                statement="Data is stored in on-premise PostgreSQL",
                confidence=ConfidenceLevel.HIGH,
                update_reasoning="Found connection strings",
                observations_used=["obs-2"],
            ),
            observations=["obs-2"],
            created=datetime.now(),
            updated=datetime.now(),
        )

        emb_a = embedder.embed(comp_a)
        emb_b = embedder.embed(comp_b)

        # Even with same prior, different posteriors should give different embeddings
        similarity = np.dot(emb_a, emb_b)

        # Should be similar (same topic/prior) but not identical
        assert similarity < 0.99
        # But still somewhat related (same domain)
        assert similarity > 0.3
