"""Tests for SQLiteComprehensionRepository."""

import tempfile
import os
from datetime import datetime, timezone

import pytest

from comprehension.schema import (
    Comprehension,
    BeliefPrior,
    BeliefPosterior,
    ConfidenceLevel,
)
from comprehension.store import SQLiteComprehensionRepository


def make_comprehension(
    id: str = "test-001",
    topic: str = "Test topic",
    domain: str = "test",
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    version: int = 1,
) -> Comprehension:
    """Factory for test comprehensions."""
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
        observations=["obs-001"],
        posterior=BeliefPosterior(
            statement="Updated belief",
            confidence=confidence,
            update_reasoning="Test reasoning",
            observations_used=["obs-001"],
        ),
        created=now,
        updated=now,
        version=version,
    )


@pytest.fixture
def db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def repo(db_path):
    """Create a repository instance."""
    return SQLiteComprehensionRepository(db_path)


class TestAddAndGet:
    """Tests for add() and get() operations."""

    def test_add_and_get(self, repo):
        """Save a comprehension and retrieve it."""
        comp = make_comprehension(id="add-get-001", topic="Add and get test")
        repo.add(comp)

        loaded = repo.get("add-get-001")
        assert loaded is not None
        assert loaded.id == "add-get-001"
        assert loaded.topic == "Add and get test"
        assert loaded.domain == "test"
        assert loaded.posterior.confidence == ConfidenceLevel.MEDIUM

    def test_add_preserves_all_fields(self, repo):
        """Verify all fields survive round-trip."""
        comp = make_comprehension(
            id="preserve-001",
            topic="Field preservation test",
            domain="api",
            confidence=ConfidenceLevel.HIGH,
            version=3,
        )
        comp.verified = True

        repo.add(comp)
        loaded = repo.get("preserve-001")

        assert loaded is not None
        assert loaded.id == comp.id
        assert loaded.topic == comp.topic
        assert loaded.domain == comp.domain
        assert loaded.prior.statement == comp.prior.statement
        assert loaded.prior.confidence == comp.prior.confidence
        assert loaded.prior.source == comp.prior.source
        assert loaded.observations == comp.observations
        assert loaded.posterior.statement == comp.posterior.statement
        assert loaded.posterior.confidence == comp.posterior.confidence
        assert loaded.posterior.update_reasoning == comp.posterior.update_reasoning
        assert loaded.posterior.observations_used == comp.posterior.observations_used
        assert loaded.version == comp.version
        assert loaded.verified == comp.verified
        # Datetime comparison (allow small drift from serialization)
        assert abs((loaded.created - comp.created).total_seconds()) < 1
        assert abs((loaded.updated - comp.updated).total_seconds()) < 1


class TestAddUpdatesExisting:
    """Tests for update behavior on duplicate ID."""

    def test_add_updates_existing(self, repo):
        """Second save with same ID updates the record."""
        comp1 = make_comprehension(id="update-001", topic="Original", version=1)
        repo.add(comp1)

        # Update with new version
        comp2 = make_comprehension(id="update-001", topic="Updated", version=2)
        repo.add(comp2)

        loaded = repo.get("update-001")
        assert loaded is not None
        assert loaded.topic == "Updated"
        assert loaded.version == 2

    def test_add_replaces_confidence(self, repo):
        """Confidence can be updated."""
        comp1 = make_comprehension(
            id="conf-001",
            confidence=ConfidenceLevel.LOW,
        )
        repo.add(comp1)

        comp2 = make_comprehension(
            id="conf-001",
            confidence=ConfidenceLevel.HIGH,
        )
        repo.add(comp2)

        loaded = repo.get("conf-001")
        assert loaded is not None
        assert loaded.posterior.confidence == ConfidenceLevel.HIGH


class TestGetMissing:
    """Tests for get() with nonexistent IDs."""

    def test_get_missing(self, repo):
        """Returns None for unknown ID."""
        result = repo.get("nonexistent-id")
        assert result is None

    def test_get_missing_after_delete(self, repo):
        """Returns None after deletion."""
        comp = make_comprehension(id="del-001")
        repo.add(comp)
        repo.delete("del-001")

        result = repo.get("del-001")
        assert result is None


class TestDelete:
    """Tests for delete() operation."""

    def test_delete(self, repo):
        """Removes comprehension, get returns None."""
        comp = make_comprehension(id="delete-test-001")
        repo.add(comp)
        assert repo.get("delete-test-001") is not None

        deleted = repo.delete("delete-test-001")
        assert deleted is True
        assert repo.get("delete-test-001") is None

    def test_delete_nonexistent(self, repo):
        """Returns False when ID not found."""
        deleted = repo.delete("never-existed")
        assert deleted is False

    def test_delete_idempotent(self, repo):
        """Second delete returns False."""
        comp = make_comprehension(id="idem-001")
        repo.add(comp)

        assert repo.delete("idem-001") is True
        assert repo.delete("idem-001") is False


class TestCount:
    """Tests for count() operation."""

    def test_count_empty(self, repo):
        """Empty repo has count 0."""
        assert repo.count() == 0

    def test_count(self, repo):
        """Tracks total stored."""
        assert repo.count() == 0

        repo.add(make_comprehension(id="count-001"))
        assert repo.count() == 1

        repo.add(make_comprehension(id="count-002"))
        assert repo.count() == 2

        repo.add(make_comprehension(id="count-003"))
        assert repo.count() == 3

    def test_count_after_delete(self, repo):
        """Count decreases after delete."""
        repo.add(make_comprehension(id="cd-001"))
        repo.add(make_comprehension(id="cd-002"))
        assert repo.count() == 2

        repo.delete("cd-001")
        assert repo.count() == 1

    def test_count_unchanged_on_update(self, repo):
        """Count unchanged when updating existing ID."""
        repo.add(make_comprehension(id="same-001", version=1))
        assert repo.count() == 1

        repo.add(make_comprehension(id="same-001", version=2))
        assert repo.count() == 1


class TestPersistence:
    """Tests for persistence across sessions."""

    def test_persists_across_sessions(self, db_path):
        """Data survives connection close and reopen."""
        # First session
        repo1 = SQLiteComprehensionRepository(db_path)
        comp = make_comprehension(id="persist-001", topic="Persistence test")
        repo1.add(comp)
        del repo1  # Close first session

        # Second session
        repo2 = SQLiteComprehensionRepository(db_path)
        loaded = repo2.get("persist-001")

        assert loaded is not None
        assert loaded.id == "persist-001"
        assert loaded.topic == "Persistence test"

    def test_multiple_items_persist(self, db_path):
        """Multiple items persist across sessions."""
        # First session
        repo1 = SQLiteComprehensionRepository(db_path)
        for i in range(5):
            repo1.add(make_comprehension(id=f"multi-{i:03d}"))
        count1 = repo1.count()
        del repo1

        # Second session
        repo2 = SQLiteComprehensionRepository(db_path)
        assert repo2.count() == count1 == 5

        for i in range(5):
            assert repo2.get(f"multi-{i:03d}") is not None
