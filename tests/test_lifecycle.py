"""Tests for observation lifecycle management."""

import pytest

from comprehension.update.lifecycle import ObservationState, ObservationLifecycle


class TestObservationState:
    """ObservationState enum has expected values."""

    def test_pending_exists(self):
        assert ObservationState.PENDING.value == "pending"

    def test_incorporated_exists(self):
        assert ObservationState.INCORPORATED.value == "incorporated"

    def test_collectible_exists(self):
        assert ObservationState.COLLECTIBLE.value == "collectible"


class TestLifecycleBasics:
    """Basic lifecycle operations."""

    def test_register_observation(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        assert lifecycle.is_pending("obs-001")
        assert not lifecycle.is_incorporated("obs-001")

    def test_mark_incorporated(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")
        assert not lifecycle.is_pending("obs-001")
        assert lifecycle.is_incorporated("obs-001")

    def test_mark_incorporated_idempotent(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")
        lifecycle.mark_incorporated("obs-001")  # Should not fail
        assert lifecycle.is_incorporated("obs-001")


class TestGetState:
    """State retrieval."""

    def test_get_pending_state(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        assert lifecycle.get_state("obs-001") == ObservationState.PENDING

    def test_get_incorporated_state(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")
        assert lifecycle.get_state("obs-001") == ObservationState.INCORPORATED

    def test_unknown_observation_raises(self):
        lifecycle = ObservationLifecycle()
        with pytest.raises(KeyError):
            lifecycle.get_state("obs-unknown")


class TestGarbageCollection:
    """Garbage collection support."""

    def test_pending_not_collectible(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        assert "obs-001" not in lifecycle.get_collectible()

    def test_incorporated_is_collectible(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")
        assert "obs-001" in lifecycle.get_collectible()

    def test_collect_removes_from_tracking(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")

        result = lifecycle.collect("obs-001")

        assert result is True
        assert "obs-001" not in lifecycle.get_collectible()
        assert not lifecycle.is_incorporated("obs-001")

    def test_collect_pending_returns_false(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        result = lifecycle.collect("obs-001")
        assert result is False
        assert lifecycle.is_pending("obs-001")


class TestBulkOperations:
    """Operations on multiple observations."""

    def test_get_pending_returns_copy(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        pending = lifecycle.get_pending()
        pending.add("obs-999")  # Modify returned set
        assert "obs-999" not in lifecycle.get_pending()

    def test_get_collectible_returns_copy(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")
        collectible = lifecycle.get_collectible()
        collectible.add("obs-999")  # Modify returned set
        assert "obs-999" not in lifecycle.get_collectible()


class TestStats:
    """Lifecycle statistics."""

    def test_empty_stats(self):
        lifecycle = ObservationLifecycle()
        stats = lifecycle.stats()
        assert stats["pending"] == 0
        assert stats["incorporated"] == 0
        assert stats["total"] == 0

    def test_stats_after_operations(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.register("obs-002")
        lifecycle.mark_incorporated("obs-001")

        stats = lifecycle.stats()
        assert stats["pending"] == 1
        assert stats["incorporated"] == 1
        assert stats["total"] == 2

    def test_len(self):
        lifecycle = ObservationLifecycle()
        lifecycle.register("obs-001")
        lifecycle.register("obs-002")
        assert len(lifecycle) == 2
