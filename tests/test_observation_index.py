"""Tests for ObservationIndex: reference tracking and pruning status."""

import tempfile
import os
import pytest

from comprehension.store.observation_index import ObservationIndex
from comprehension.update.lifecycle import ObservationLifecycle


@pytest.fixture
def db_path():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def index(db_path):
    """Create ObservationIndex instance."""
    return ObservationIndex(db_path)


class TestRecordReference:
    """Test recording observation -> comprehension references."""

    def test_record_reference_creates_link(self, index):
        """Recording a reference creates an observation-comprehension link."""
        index.record_reference("obs-001", "comp-001")

        comps = index.get_referencing_comprehensions("obs-001")
        assert comps == ["comp-001"]

    def test_record_reference_idempotent(self, index):
        """Recording same reference twice has no effect."""
        index.record_reference("obs-001", "comp-001")
        index.record_reference("obs-001", "comp-001")

        comps = index.get_referencing_comprehensions("obs-001")
        assert len(comps) == 1


class TestMultipleReferences:
    """Test one observation referenced by multiple comprehensions."""

    def test_multiple_comprehensions_reference_same_observation(self, index):
        """One observation can be referenced by multiple comprehensions."""
        index.record_reference("obs-shared", "comp-001")
        index.record_reference("obs-shared", "comp-002")
        index.record_reference("obs-shared", "comp-003")

        comps = index.get_referencing_comprehensions("obs-shared")
        assert set(comps) == {"comp-001", "comp-002", "comp-003"}

    def test_comprehension_can_reference_multiple_observations(self, index):
        """One comprehension can reference multiple observations."""
        index.record_reference("obs-001", "comp-001")
        index.record_reference("obs-002", "comp-001")
        index.record_reference("obs-003", "comp-001")

        obs = index.get_references_for_comprehension("comp-001")
        assert set(obs) == {"obs-001", "obs-002", "obs-003"}


class TestPruning:
    """Test observation content pruning."""

    def test_mark_pruned_sets_status(self, index):
        """Marking as pruned changes availability status."""
        obs_id = "obs-to-prune"

        # Initially available (not pruned)
        assert index.is_content_available(obs_id) is True

        # After pruning, not available
        index.mark_content_pruned(obs_id)
        assert index.is_content_available(obs_id) is False

    def test_mark_pruned_idempotent(self, index):
        """Marking same observation pruned twice has no error."""
        index.mark_content_pruned("obs-001")
        index.mark_content_pruned("obs-001")  # Should not raise

        assert index.is_content_available("obs-001") is False


class TestContentAvailability:
    """Test checking if observation content is available."""

    def test_is_content_available_returns_true_for_unpruned(self, index):
        """Unpruned observations have content available."""
        # Never seen observation is "available" (not marked pruned)
        assert index.is_content_available("obs-never-seen") is True

    def test_is_content_available_returns_false_after_pruning(self, index):
        """Pruned observations have content unavailable."""
        index.mark_content_pruned("obs-pruned")
        assert index.is_content_available("obs-pruned") is False


class TestGetReferencingComprehensions:
    """Test retrieving comprehensions that reference an observation."""

    def test_returns_empty_list_for_unreferenced(self, index):
        """Unreferenced observations return empty list."""
        comps = index.get_referencing_comprehensions("obs-unknown")
        assert comps == []

    def test_returns_all_referencing_comprehensions(self, index):
        """Returns all comprehensions that reference the observation."""
        index.record_reference("obs-001", "comp-A")
        index.record_reference("obs-001", "comp-B")

        comps = index.get_referencing_comprehensions("obs-001")
        assert set(comps) == {"comp-A", "comp-B"}


class TestGetPrunable:
    """Test integration with ObservationLifecycle for pruning decisions."""

    def test_get_prunable_returns_incorporated_not_yet_pruned(self, index):
        """Returns observations that are incorporated but not yet pruned."""
        lifecycle = ObservationLifecycle()

        # Register and incorporate observations
        lifecycle.register("obs-001")
        lifecycle.register("obs-002")
        lifecycle.register("obs-003")
        lifecycle.mark_incorporated("obs-001")
        lifecycle.mark_incorporated("obs-002")
        # obs-003 stays pending

        # obs-001 already pruned
        index.mark_content_pruned("obs-001")

        # Should return only obs-002 (incorporated but not pruned)
        prunable = index.get_prunable(lifecycle)
        assert prunable == {"obs-002"}

    def test_get_prunable_empty_when_all_pruned(self, index):
        """Returns empty set when all incorporated have been pruned."""
        lifecycle = ObservationLifecycle()

        lifecycle.register("obs-001")
        lifecycle.mark_incorporated("obs-001")
        index.mark_content_pruned("obs-001")

        prunable = index.get_prunable(lifecycle)
        assert prunable == set()

    def test_get_prunable_excludes_pending(self, index):
        """Pending observations are not prunable."""
        lifecycle = ObservationLifecycle()

        lifecycle.register("obs-pending")  # Never incorporated

        prunable = index.get_prunable(lifecycle)
        assert prunable == set()


class TestObservationRefsRetainedAfterPrune:
    """Validate key memory-efficiency principle: references persist when content is deleted."""

    def test_observation_refs_retained_after_prune(self, index):
        """After mark_content_pruned(), references to observation remain intact.

        This validates the key memory-efficiency principle:
        - Observation content can be deleted to save space
        - But references in comprehension.observations list persist
        - The index tracks this distinction
        """
        # Record references
        index.record_reference("obs-A", "comp-001")
        index.record_reference("obs-B", "comp-001")
        index.record_reference("obs-A", "comp-002")

        # Prune observation content
        index.mark_content_pruned("obs-A")
        index.mark_content_pruned("obs-B")

        # References still exist after pruning
        comps_for_a = index.get_referencing_comprehensions("obs-A")
        assert set(comps_for_a) == {"comp-001", "comp-002"}

        comps_for_b = index.get_referencing_comprehensions("obs-B")
        assert comps_for_b == ["comp-001"]

        # Comprehension still references both observations
        obs_for_comp = index.get_references_for_comprehension("comp-001")
        assert set(obs_for_comp) == {"obs-A", "obs-B"}

        # But content is marked as unavailable
        assert index.is_content_available("obs-A") is False
        assert index.is_content_available("obs-B") is False


class TestRemoveReferencesForComprehension:
    """Test cleanup when comprehension is deleted."""

    def test_removes_all_references_for_deleted_comprehension(self, index):
        """Removing references cleans up all observation links."""
        index.record_reference("obs-001", "comp-to-delete")
        index.record_reference("obs-002", "comp-to-delete")
        index.record_reference("obs-001", "comp-keep")

        removed = index.remove_references_for_comprehension("comp-to-delete")

        assert removed == 2
        assert index.get_referencing_comprehensions("obs-001") == ["comp-keep"]
        assert index.get_referencing_comprehensions("obs-002") == []


class TestStats:
    """Test observation index statistics."""

    def test_stats_returns_counts(self, index):
        """Stats returns reference and pruning counts."""
        index.record_reference("obs-001", "comp-001")
        index.record_reference("obs-001", "comp-002")
        index.record_reference("obs-002", "comp-001")
        index.mark_content_pruned("obs-003")

        stats = index.stats()

        assert stats["total_refs"] == 3
        assert stats["unique_observations"] == 2
        assert stats["pruned_count"] == 1
