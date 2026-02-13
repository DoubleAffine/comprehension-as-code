"""Belief store: SQLite persistence for comprehensions."""

from .migrations import ensure_schema
from .repository import SQLiteComprehensionRepository
from .observation_index import ObservationIndex
from .belief_store import BeliefStore
from .queries import (
    CONFIDENCE_ORDER,
    build_filter_query,
    build_confidence_filter,
    get_confidence_values_at_or_above,
)

__all__ = [
    # Main public interface
    "BeliefStore",
    # Supporting classes
    "SQLiteComprehensionRepository",
    "ObservationIndex",
    # Schema
    "ensure_schema",
    # Query helpers
    "CONFIDENCE_ORDER",
    "build_filter_query",
    "build_confidence_filter",
    "get_confidence_values_at_or_above",
]
