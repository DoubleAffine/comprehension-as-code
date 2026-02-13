"""Tests for VectorStore."""

import numpy as np
import pytest

from comprehension.convergence.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path):
    """Create a vector store with a temporary database."""
    db_path = tmp_path / "test_vectors.db"
    return VectorStore(db_path)


@pytest.fixture
def sample_embeddings():
    """Create sample normalized embeddings for testing."""
    np.random.seed(42)  # Reproducible

    # Generate random vectors and normalize them
    vectors = {}
    for name in ["alpha", "beta", "gamma", "delta"]:
        vec = np.random.randn(384).astype(np.float32)
        vec = vec / np.linalg.norm(vec)  # Normalize
        vectors[name] = vec

    return vectors


class TestVectorStoreAdd:
    """Tests for add operation."""

    def test_add_single_vector(self, vector_store, sample_embeddings):
        """Should add a single vector successfully."""
        vector_store.add("comp-001", sample_embeddings["alpha"])

        assert vector_store.count() == 1

    def test_add_multiple_vectors(self, vector_store, sample_embeddings):
        """Should add multiple vectors."""
        vector_store.add("comp-001", sample_embeddings["alpha"])
        vector_store.add("comp-002", sample_embeddings["beta"])
        vector_store.add("comp-003", sample_embeddings["gamma"])

        assert vector_store.count() == 3

    def test_add_same_id_twice_updates(self, vector_store, sample_embeddings):
        """Adding same ID should update, not duplicate."""
        vector_store.add("comp-001", sample_embeddings["alpha"])
        vector_store.add("comp-001", sample_embeddings["beta"])

        assert vector_store.count() == 1


class TestVectorStoreRemove:
    """Tests for remove operation."""

    def test_remove_existing_vector(self, vector_store, sample_embeddings):
        """Should remove an existing vector."""
        vector_store.add("comp-001", sample_embeddings["alpha"])
        vector_store.add("comp-002", sample_embeddings["beta"])

        result = vector_store.remove("comp-001")

        assert result is True
        assert vector_store.count() == 1

    def test_remove_nonexistent_returns_false(self, vector_store):
        """Removing non-existent ID should return False."""
        result = vector_store.remove("nonexistent")

        assert result is False

    def test_remove_clears_from_knn(self, vector_store, sample_embeddings):
        """Removed vectors should not appear in KNN results."""
        vector_store.add("comp-001", sample_embeddings["alpha"])
        vector_store.add("comp-002", sample_embeddings["beta"])

        vector_store.remove("comp-001")

        # Query for alpha - should not find it
        results = vector_store.query_knn(sample_embeddings["alpha"], limit=5)

        comp_ids = [r[0] for r in results]
        assert "comp-001" not in comp_ids


class TestVectorStoreKNN:
    """Tests for KNN query operation."""

    def test_knn_returns_closest_first(self, vector_store, sample_embeddings):
        """KNN should return results ordered by distance (closest first)."""
        # Add all vectors
        for name, vec in sample_embeddings.items():
            vector_store.add(f"comp-{name}", vec)

        # Query for alpha
        results = vector_store.query_knn(sample_embeddings["alpha"], limit=5)

        # First result should be alpha itself (distance ~0)
        assert results[0][0] == "comp-alpha"
        assert results[0][1] < 0.01  # Very close to 0

    def test_knn_returns_correct_limit(self, vector_store, sample_embeddings):
        """KNN should respect the limit parameter."""
        for name, vec in sample_embeddings.items():
            vector_store.add(f"comp-{name}", vec)

        results = vector_store.query_knn(sample_embeddings["alpha"], limit=2)

        assert len(results) == 2

    def test_knn_empty_store_returns_empty(self, vector_store, sample_embeddings):
        """KNN on empty store should return empty list."""
        results = vector_store.query_knn(sample_embeddings["alpha"], limit=5)

        assert results == []

    def test_knn_returns_comprehension_ids(self, vector_store, sample_embeddings):
        """KNN results should contain comprehension IDs, not rowids."""
        vector_store.add("my-custom-id-123", sample_embeddings["alpha"])

        results = vector_store.query_knn(sample_embeddings["alpha"], limit=1)

        assert results[0][0] == "my-custom-id-123"

    def test_knn_distances_are_valid(self, vector_store, sample_embeddings):
        """Distances should be reasonable values (0-2 for cosine distance)."""
        for name, vec in sample_embeddings.items():
            vector_store.add(f"comp-{name}", vec)

        results = vector_store.query_knn(sample_embeddings["alpha"], limit=5)

        for comp_id, distance in results:
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            assert 0 <= distance <= 2


class TestVectorStoreCount:
    """Tests for count operation."""

    def test_count_empty_store(self, vector_store):
        """Empty store should have count 0."""
        assert vector_store.count() == 0

    def test_count_after_adds(self, vector_store, sample_embeddings):
        """Count should reflect number of unique vectors."""
        vector_store.add("comp-001", sample_embeddings["alpha"])
        assert vector_store.count() == 1

        vector_store.add("comp-002", sample_embeddings["beta"])
        assert vector_store.count() == 2

    def test_count_after_remove(self, vector_store, sample_embeddings):
        """Count should decrease after removal."""
        vector_store.add("comp-001", sample_embeddings["alpha"])
        vector_store.add("comp-002", sample_embeddings["beta"])

        vector_store.remove("comp-001")

        assert vector_store.count() == 1


class TestVectorStoreUpsert:
    """Tests for upsert behavior (add with existing ID)."""

    def test_upsert_updates_vector(self, vector_store, sample_embeddings):
        """Adding same ID with different vector should update."""
        # Add alpha under comp-001
        vector_store.add("comp-001", sample_embeddings["alpha"])

        # Query for alpha - should find comp-001
        results = vector_store.query_knn(sample_embeddings["alpha"], limit=1)
        assert results[0][0] == "comp-001"
        assert results[0][1] < 0.01

        # Update comp-001 to beta
        vector_store.add("comp-001", sample_embeddings["beta"])

        # Now query for beta - should find comp-001
        results = vector_store.query_knn(sample_embeddings["beta"], limit=1)
        assert results[0][0] == "comp-001"
        assert results[0][1] < 0.01

        # Query for alpha - comp-001 should be distant now
        results = vector_store.query_knn(sample_embeddings["alpha"], limit=1)
        assert results[0][0] == "comp-001"
        assert results[0][1] > 0.5  # No longer close
