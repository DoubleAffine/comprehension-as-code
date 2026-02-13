"""Tests for SQLiteComprehensionRepository."""

import tempfile
import os
import time
from datetime import datetime, timezone, timedelta

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
    updated: datetime = None,
) -> Comprehension:
    """Factory for test comprehensions."""
    now = updated or datetime.now(timezone.utc)
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


def make_comprehension_with_created(
    id: str,
    topic: str,
    domain: str,
    confidence: ConfidenceLevel,
    created: datetime,
    updated: datetime,
) -> Comprehension:
    """Factory for test comprehensions with explicit timestamps."""
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
        created=created,
        updated=updated,
        version=1,
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


class TestFindByDomain:
    """Tests for find_by_domain() retrieval."""

    def test_find_by_domain(self, repo):
        """Filters correctly by domain."""
        repo.add(make_comprehension(id="py-001", domain="python", topic="Python basics"))
        repo.add(make_comprehension(id="py-002", domain="python", topic="Python advanced"))
        repo.add(make_comprehension(id="js-001", domain="javascript", topic="JS basics"))

        python_comps = repo.find_by_domain("python")
        assert len(python_comps) == 2
        assert all(c.domain == "python" for c in python_comps)

        js_comps = repo.find_by_domain("javascript")
        assert len(js_comps) == 1
        assert js_comps[0].domain == "javascript"

    def test_find_by_domain_empty(self, repo):
        """Returns empty list if no match."""
        repo.add(make_comprehension(id="py-001", domain="python"))

        result = repo.find_by_domain("nonexistent")
        assert result == []

    def test_find_by_domain_ordered_by_updated(self, repo):
        """Results are ordered by updated DESC."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=1)
        older = now - timedelta(hours=2)

        repo.add(make_comprehension_with_created(
            id="old", topic="Old", domain="test", confidence=ConfidenceLevel.MEDIUM,
            created=older, updated=older
        ))
        repo.add(make_comprehension_with_created(
            id="new", topic="New", domain="test", confidence=ConfidenceLevel.MEDIUM,
            created=now, updated=now
        ))
        repo.add(make_comprehension_with_created(
            id="mid", topic="Mid", domain="test", confidence=ConfidenceLevel.MEDIUM,
            created=old, updated=old
        ))

        results = repo.find_by_domain("test")
        assert len(results) == 3
        assert results[0].id == "new"
        assert results[1].id == "mid"
        assert results[2].id == "old"


class TestFindByTopic:
    """Tests for find_by_topic() full-text search."""

    def test_find_by_topic_fts(self, repo):
        """Full-text search works."""
        repo.add(make_comprehension(id="py-001", topic="Python error handling patterns"))
        repo.add(make_comprehension(id="py-002", topic="Python type hints for functions"))
        repo.add(make_comprehension(id="js-001", topic="JavaScript async await"))

        results = repo.find_by_topic("Python")
        assert len(results) >= 2
        topics = [r.topic for r in results]
        assert any("Python" in t for t in topics)

    def test_find_by_topic_stemming(self, repo):
        """FTS5 stemming: 'learning' matches 'learn'."""
        repo.add(make_comprehension(id="learn-001", topic="Machine learning fundamentals"))
        repo.add(make_comprehension(id="learn-002", topic="Learn Python fast"))
        repo.add(make_comprehension(id="other-001", topic="Database design patterns"))

        # "learning" should match "learn" due to Porter stemmer
        results = repo.find_by_topic("learning")
        assert len(results) >= 1
        topics = [r.topic for r in results]
        assert any("learn" in t.lower() for t in topics)

    def test_find_by_topic_limit(self, repo):
        """Respects limit parameter."""
        for i in range(20):
            repo.add(make_comprehension(
                id=f"topic-{i:03d}",
                topic=f"Python feature number {i}"
            ))

        results = repo.find_by_topic("Python", limit=5)
        assert len(results) == 5


class TestFindByConfidence:
    """Tests for find_by_confidence() filtering."""

    def test_find_by_confidence_high(self, repo):
        """HIGH returns HIGH only."""
        repo.add(make_comprehension(id="high-001", confidence=ConfidenceLevel.HIGH))
        repo.add(make_comprehension(id="med-001", confidence=ConfidenceLevel.MEDIUM))
        repo.add(make_comprehension(id="low-001", confidence=ConfidenceLevel.LOW))
        repo.add(make_comprehension(id="unk-001", confidence=ConfidenceLevel.UNKNOWN))

        results = repo.find_by_confidence(ConfidenceLevel.HIGH)
        assert len(results) == 1
        assert results[0].posterior.confidence == ConfidenceLevel.HIGH

    def test_find_by_confidence_medium(self, repo):
        """MEDIUM returns HIGH + MEDIUM."""
        repo.add(make_comprehension(id="high-001", confidence=ConfidenceLevel.HIGH))
        repo.add(make_comprehension(id="med-001", confidence=ConfidenceLevel.MEDIUM))
        repo.add(make_comprehension(id="low-001", confidence=ConfidenceLevel.LOW))
        repo.add(make_comprehension(id="unk-001", confidence=ConfidenceLevel.UNKNOWN))

        results = repo.find_by_confidence(ConfidenceLevel.MEDIUM)
        assert len(results) == 2
        confidences = {r.posterior.confidence for r in results}
        assert confidences == {ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM}

    def test_find_by_confidence_low(self, repo):
        """LOW returns HIGH + MEDIUM + LOW."""
        repo.add(make_comprehension(id="high-001", confidence=ConfidenceLevel.HIGH))
        repo.add(make_comprehension(id="med-001", confidence=ConfidenceLevel.MEDIUM))
        repo.add(make_comprehension(id="low-001", confidence=ConfidenceLevel.LOW))
        repo.add(make_comprehension(id="unk-001", confidence=ConfidenceLevel.UNKNOWN))

        results = repo.find_by_confidence(ConfidenceLevel.LOW)
        assert len(results) == 3
        confidences = {r.posterior.confidence for r in results}
        assert ConfidenceLevel.UNKNOWN not in confidences

    def test_find_by_confidence_unknown(self, repo):
        """UNKNOWN returns all."""
        repo.add(make_comprehension(id="high-001", confidence=ConfidenceLevel.HIGH))
        repo.add(make_comprehension(id="med-001", confidence=ConfidenceLevel.MEDIUM))
        repo.add(make_comprehension(id="low-001", confidence=ConfidenceLevel.LOW))
        repo.add(make_comprehension(id="unk-001", confidence=ConfidenceLevel.UNKNOWN))

        results = repo.find_by_confidence(ConfidenceLevel.UNKNOWN)
        assert len(results) == 4


class TestFindRecent:
    """Tests for find_recent() retrieval."""

    def test_find_recent(self, repo):
        """Returns correct order, respects limit."""
        now = datetime.now(timezone.utc)

        for i in range(10):
            updated = now - timedelta(hours=i)
            repo.add(make_comprehension_with_created(
                id=f"recent-{i:03d}",
                topic=f"Topic {i}",
                domain="test",
                confidence=ConfidenceLevel.MEDIUM,
                created=updated,
                updated=updated,
            ))

        results = repo.find_recent(limit=5)
        assert len(results) == 5
        # Most recent first
        assert results[0].id == "recent-000"
        assert results[4].id == "recent-004"

    def test_find_recent_default_limit(self, repo):
        """Default limit is 10."""
        now = datetime.now(timezone.utc)
        for i in range(15):
            updated = now - timedelta(minutes=i)
            repo.add(make_comprehension_with_created(
                id=f"rec-{i:03d}",
                topic=f"Topic {i}",
                domain="test",
                confidence=ConfidenceLevel.MEDIUM,
                created=updated,
                updated=updated,
            ))

        results = repo.find_recent()
        assert len(results) == 10


class TestFindCombined:
    """Tests for find() combined query."""

    def test_find_combined_domain_and_confidence(self, repo):
        """Domain + confidence + limit work together."""
        repo.add(make_comprehension(
            id="py-high-001", domain="python", confidence=ConfidenceLevel.HIGH
        ))
        repo.add(make_comprehension(
            id="py-med-001", domain="python", confidence=ConfidenceLevel.MEDIUM
        ))
        repo.add(make_comprehension(
            id="py-low-001", domain="python", confidence=ConfidenceLevel.LOW
        ))
        repo.add(make_comprehension(
            id="js-high-001", domain="javascript", confidence=ConfidenceLevel.HIGH
        ))

        # Python domain, at least MEDIUM confidence
        results = repo.find(domain="python", min_confidence=ConfidenceLevel.MEDIUM)
        assert len(results) == 2
        assert all(r.domain == "python" for r in results)
        assert all(r.posterior.confidence in {ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM}
                   for r in results)

    def test_find_combined_with_topic(self, repo):
        """Domain + topic + confidence all work together."""
        repo.add(make_comprehension(
            id="py-err-high", domain="python",
            topic="Error handling patterns in Python",
            confidence=ConfidenceLevel.HIGH
        ))
        repo.add(make_comprehension(
            id="py-err-low", domain="python",
            topic="Python error logging",
            confidence=ConfidenceLevel.LOW
        ))
        repo.add(make_comprehension(
            id="py-type", domain="python",
            topic="Python type hints",
            confidence=ConfidenceLevel.HIGH
        ))
        repo.add(make_comprehension(
            id="js-err", domain="javascript",
            topic="JavaScript error handling",
            confidence=ConfidenceLevel.HIGH
        ))

        # Python domain, error topic, at least MEDIUM confidence
        results = repo.find(
            domain="python",
            topic_query="error",
            min_confidence=ConfidenceLevel.MEDIUM,
        )
        # Should match py-err-high (Python + error + HIGH)
        # Should NOT match py-err-low (LOW confidence)
        # Should NOT match py-type (no "error" in topic)
        # Should NOT match js-err (wrong domain)
        assert len(results) == 1
        assert results[0].id == "py-err-high"

    def test_find_with_none_filters(self, repo):
        """All filters can be None (returns all)."""
        repo.add(make_comprehension(id="any-001"))
        repo.add(make_comprehension(id="any-002"))
        repo.add(make_comprehension(id="any-003"))

        results = repo.find()
        assert len(results) == 3

    def test_find_respects_limit(self, repo):
        """Limit parameter is respected."""
        for i in range(10):
            repo.add(make_comprehension(id=f"limit-{i:03d}"))

        results = repo.find(limit=3)
        assert len(results) == 3
