"""Observation lifecycle management for garbage collection.

Key insight: Once an observation has informed comprehension, the observation
itself can be discarded. The posterior IS the compression - we store beliefs,
not evidence.
"""

from enum import Enum
from typing import Set


class ObservationState(str, Enum):
    """Lifecycle states for observations.

    PENDING: Created, not yet incorporated into any comprehension
    INCORPORATED: Has informed at least one comprehension
    COLLECTIBLE: Safe to garbage collect (same as INCORPORATED for now)

    Note: Currently INCORPORATED == COLLECTIBLE. Future phases may add
    retention policies (e.g., keep for N days, keep if referenced by
    active comprehension, etc.)
    """
    PENDING = "pending"
    INCORPORATED = "incorporated"
    COLLECTIBLE = "collectible"


class ObservationLifecycle:
    """Manages observation lifecycle for garbage collection.

    Tracks observation state transitions:
    - register(): New observation -> PENDING
    - mark_incorporated(): PENDING -> INCORPORATED
    - get_collectible(): Returns IDs safe for deletion
    - collect(): Acknowledge deletion, stop tracking

    Thread safety: NOT thread-safe. Wrap in lock for concurrent access.
    """

    def __init__(self):
        """Initialize empty lifecycle tracker."""
        self._pending: Set[str] = set()
        self._incorporated: Set[str] = set()

    def register(self, observation_id: str) -> None:
        """Register new observation as pending.

        Args:
            observation_id: Unique identifier for the observation
        """
        self._pending.add(observation_id)

    def mark_incorporated(self, observation_id: str) -> None:
        """Mark observation as having informed a comprehension.

        Moves observation from PENDING to INCORPORATED state.
        Can be called multiple times (idempotent).

        Args:
            observation_id: Observation that has been incorporated
        """
        self._pending.discard(observation_id)
        self._incorporated.add(observation_id)

    def get_state(self, observation_id: str) -> ObservationState:
        """Get current state of an observation.

        Args:
            observation_id: Observation to check

        Returns:
            ObservationState or raises KeyError if not tracked
        """
        if observation_id in self._pending:
            return ObservationState.PENDING
        if observation_id in self._incorporated:
            return ObservationState.INCORPORATED
        raise KeyError(f"Unknown observation: {observation_id}")

    def get_pending(self) -> Set[str]:
        """Get observation IDs that haven't been incorporated yet.

        Returns:
            Set of observation IDs in PENDING state
        """
        return self._pending.copy()

    def get_collectible(self) -> Set[str]:
        """Get observation IDs safe for garbage collection.

        Returns observations that have been incorporated into at least
        one comprehension's posterior. Their content is now redundant.

        Returns:
            Set of observation IDs safe to delete
        """
        return self._incorporated.copy()

    def collect(self, observation_id: str) -> bool:
        """Remove observation from tracking after deletion.

        Call this after successfully deleting the observation file/record.

        Args:
            observation_id: Observation that was deleted

        Returns:
            True if observation was collectible and removed, False otherwise
        """
        if observation_id in self._incorporated:
            self._incorporated.remove(observation_id)
            return True
        return False

    def is_pending(self, observation_id: str) -> bool:
        """Check if observation is pending (not yet incorporated)."""
        return observation_id in self._pending

    def is_incorporated(self, observation_id: str) -> bool:
        """Check if observation has been incorporated."""
        return observation_id in self._incorporated

    def __len__(self) -> int:
        """Total number of tracked observations."""
        return len(self._pending) + len(self._incorporated)

    def stats(self) -> dict:
        """Get lifecycle statistics.

        Returns:
            Dict with counts: pending, incorporated, total
        """
        return {
            "pending": len(self._pending),
            "incorporated": len(self._incorporated),
            "total": len(self),
        }
