"""Tests for BeliefStore: unified interface for belief persistence."""

import tempfile
import os
from datetime import datetime, timezone

import pytest

from comprehension.store import BeliefStore, ObservationIndex
from comprehension.schema import (
    Comprehension,
    BeliefPrior,
    BeliefPosterior,
    ConfidenceLevel,
)


@pytest.fixture
def db_path():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def store(db_path):
    """Create BeliefStore instance."""
    return BeliefStore(db_path)


def make_comprehension(
    id: str,
    topic: str = "Test topic",
    domain: str = "test",
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    observations: list = None,
) -> Comprehension:
    """Helper to create test comprehensions."""
    if observations is None:
        observations = ["obs-001"]

    now = datetime.now(timezone.utc)
    return Comprehension(
        id=id,
        topic=topic,
        domain=domain,
        prior=BeliefPrior(
            statement="Initial belief",
            confidence=ConfidenceLevel.UNKNOWN,
            source="test",
        ),
        observations=observations,
        posterior=BeliefPosterior(
            statement="Updated belief",
            confidence=confidence,
            update_reasoning="Test reasoning",
            observations_used=observations,
        ),
        created=now,
        updated=now,
    )


class TestSaveAndGet:
    """Test basic persistence operations."""

    def test_save_and_get_roundtrip(self, store):
        """Saved comprehension can be retrieved by ID."""
        comp = make_comprehension("comp-001", topic="Authentication flow")
        store.save(comp)

        loaded = store.get("comp-001")

        assert loaded is not None
        assert loaded.id == "comp-001"
        assert loaded.topic == "Authentication flow"

    def test_get_returns_none_for_missing(self, store):
        """Get returns None for non-existent ID."""
        assert store.get("does-not-exist") is None

    def test_save_updates_existing(self, store):
        """Saving with same ID updates existing comprehension."""
        comp1 = make_comprehension("comp-001", topic="Version 1")
        comp2 = make_comprehension("comp-001", topic="Version 2")

        store.save(comp1)
        store.save(comp2)

        loaded = store.get("comp-001")
        assert loaded.topic == "Version 2"


class TestSaveUpdatesObservationIndex:
    """Test that save() properly tracks observation references."""

    def test_save_records_observation_references(self, store):
        """Saving comprehension records observation references in index."""
        comp = make_comprehension(
            "comp-001",
            observations=["obs-A", "obs-B", "obs-C"],
        )
        store.save(comp)

        obs_index = store.get_observation_index()

        # All observations should reference this comprehension
        for obs_id in ["obs-A", "obs-B", "obs-C"]:
            comps = obs_index.get_referencing_comprehensions(obs_id)
            assert "comp-001" in comps

    def test_multiple_comprehensions_share_observation(self, store):
        """Multiple comprehensions can reference same observation."""
        comp1 = make_comprehension("comp-001", observations=["obs-shared"])
        comp2 = make_comprehension("comp-002", observations=["obs-shared"])

        store.save(comp1)
        store.save(comp2)

        obs_index = store.get_observation_index()
        comps = obs_index.get_referencing_comprehensions("obs-shared")

        assert set(comps) == {"comp-001", "comp-002"}


class TestDelete:
    """Test deletion operations."""

    def test_delete_removes_comprehension(self, store):
        """Delete removes comprehension from store."""
        comp = make_comprehension("comp-to-delete")
        store.save(comp)

        assert store.delete("comp-to-delete") is True
        assert store.get("comp-to-delete") is None

    def test_delete_returns_false_for_missing(self, store):
        """Delete returns False for non-existent ID."""
        assert store.delete("does-not-exist") is False

    def test_delete_removes_observation_references(self, store):
        """Delete also removes observation references from index."""
        comp = make_comprehension("comp-001", observations=["obs-A", "obs-B"])
        store.save(comp)

        store.delete("comp-001")

        obs_index = store.get_observation_index()
        assert obs_index.get_referencing_comprehensions("obs-A") == []
        assert obs_index.get_referencing_comprehensions("obs-B") == []


class TestRetrievalMethods:
    """Test that all find_* methods delegate properly."""

    def test_find_by_domain(self, store):
        """find_by_domain returns comprehensions in domain."""
        store.save(make_comprehension("comp-api-1", domain="api"))
        store.save(make_comprehension("comp-api-2", domain="api"))
        store.save(make_comprehension("comp-db-1", domain="database"))

        results = store.find_by_domain("api")

        assert len(results) == 2
        assert all(c.domain == "api" for c in results)

    def test_find_by_topic(self, store):
        """find_by_topic searches topic text."""
        store.save(make_comprehension("comp-1", topic="Authentication and JWT tokens"))
        store.save(make_comprehension("comp-2", topic="Database migrations"))

        results = store.find_by_topic("authentication")

        assert len(results) >= 1
        assert any("Authentication" in c.topic for c in results)

    def test_find_by_confidence(self, store):
        """find_by_confidence filters by minimum level."""
        store.save(make_comprehension("comp-low", confidence=ConfidenceLevel.LOW))
        store.save(make_comprehension("comp-med", confidence=ConfidenceLevel.MEDIUM))
        store.save(make_comprehension("comp-high", confidence=ConfidenceLevel.HIGH))

        results = store.find_by_confidence(ConfidenceLevel.MEDIUM)

        assert len(results) == 2
        assert all(
            c.posterior.confidence in [ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH]
            for c in results
        )

    def test_find_recent(self, store):
        """find_recent returns most recently updated."""
        store.save(make_comprehension("comp-1"))
        store.save(make_comprehension("comp-2"))
        store.save(make_comprehension("comp-3"))

        results = store.find_recent(limit=2)

        assert len(results) == 2

    def test_find_combined_filters(self, store):
        """find() combines multiple filters."""
        store.save(
            make_comprehension(
                "comp-match",
                domain="api",
                topic="JWT authentication",
                confidence=ConfidenceLevel.HIGH,
            )
        )
        store.save(
            make_comprehension(
                "comp-wrong-domain",
                domain="database",
                topic="JWT",
                confidence=ConfidenceLevel.HIGH,
            )
        )
        store.save(
            make_comprehension(
                "comp-wrong-conf",
                domain="api",
                topic="JWT",
                confidence=ConfidenceLevel.LOW,
            )
        )

        results = store.find(
            domain="api",
            min_confidence=ConfidenceLevel.MEDIUM,
        )

        assert len(results) == 1
        assert results[0].id == "comp-match"


class TestStats:
    """Test store statistics."""

    def test_stats_returns_counts(self, store):
        """Stats returns comprehension and observation counts."""
        store.save(make_comprehension("comp-1", observations=["obs-1", "obs-2"]))
        store.save(make_comprehension("comp-2", observations=["obs-2", "obs-3"]))

        stats = store.stats()

        assert stats["comprehension_count"] == 2
        assert stats["observation_refs"] == 4  # obs-1, obs-2, obs-2, obs-3
        assert stats["unique_observations"] == 3  # obs-1, obs-2, obs-3
        assert stats["pruned_observations"] == 0


class TestMemoryEfficiencyPrinciple:
    """Validate that observation references persist after content pruning."""

    def test_observation_refs_retained_after_content_pruned(self, store):
        """Comprehension.observations list retains IDs after content is pruned.

        This is the key memory-efficiency principle:
        - Store beliefs, not evidence
        - Observation content can be deleted
        - References remain in comprehension for provenance
        """
        comp = make_comprehension(
            "test-refs",
            topic="Reference retention test",
            observations=["obs-A", "obs-B"],
        )
        store.save(comp)

        # Prune observation content
        obs_index = store.get_observation_index()
        obs_index.mark_content_pruned("obs-A")
        obs_index.mark_content_pruned("obs-B")

        # CRITICAL: comprehension.observations must still contain the IDs
        loaded = store.get("test-refs")
        assert "obs-A" in loaded.observations, "obs-A reference lost after pruning!"
        assert "obs-B" in loaded.observations, "obs-B reference lost after pruning!"

        # But content is marked as unavailable
        assert not obs_index.is_content_available("obs-A")
        assert not obs_index.is_content_available("obs-B")


class TestObservationIndexAccess:
    """Test accessing observation index through store."""

    def test_get_observation_index_returns_index(self, store):
        """get_observation_index returns ObservationIndex instance."""
        obs_index = store.get_observation_index()

        assert isinstance(obs_index, ObservationIndex)

    def test_observation_index_shares_database(self, store):
        """Observation index uses same database as store."""
        # Save comprehension with observations
        comp = make_comprehension("comp-001", observations=["obs-001"])
        store.save(comp)

        # Access index through store
        obs_index = store.get_observation_index()

        # Should have recorded the reference
        comps = obs_index.get_referencing_comprehensions("obs-001")
        assert "comp-001" in comps
