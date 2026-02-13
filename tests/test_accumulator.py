"""Tests for AccumulationTracker rising tide detection."""

import pytest
import tempfile
import os
from datetime import datetime

from comprehension.schema import (
    Comprehension,
    BeliefPrior,
    BeliefPosterior,
    ConfidenceLevel,
)
from comprehension.convergence.accumulator import AccumulationTracker, AccumulationHotspot
from comprehension.convergence.similarity import SimilarityMatch


def make_comprehension(
    id: str,
    domain: str,
    prior_statement: str = "test prior",
    posterior_statement: str = "test posterior",
    topic: str = "test topic"
) -> Comprehension:
    """Factory function for test comprehensions."""
    now = datetime.now()
    return Comprehension(
        id=id,
        topic=topic,
        domain=domain,
        prior=BeliefPrior(
            statement=prior_statement,
            confidence=ConfidenceLevel.MEDIUM,
            source="test"
        ),
        observations=[],
        posterior=BeliefPosterior(
            statement=posterior_statement,
            confidence=ConfidenceLevel.MEDIUM,
            update_reasoning="test update",
            observations_used=[]
        ),
        created=now,
        updated=now
    )


@pytest.fixture
def db_path():
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test.db")


@pytest.fixture
def tracker(db_path):
    """Create an AccumulationTracker."""
    return AccumulationTracker(db_path)


class TestRecordSimilarity:
    """Tests for recording similarity edges."""

    def test_record_similarity_creates_edge(self, tracker):
        """record_similarity creates an edge in the database."""
        tracker.record_similarity(
            source_id="comp-1",
            target_id="comp-2",
            similarity=0.85,
            source_domain="api",
            target_domain="database"
        )

        # Verify by getting connections
        connections = tracker.get_connections("comp-1")

        assert len(connections) == 1
        assert connections[0] == ("comp-2", "database", 0.85)

    def test_record_similarity_upserts(self, tracker):
        """record_similarity updates existing edge."""
        # Record initial edge
        tracker.record_similarity(
            source_id="comp-1",
            target_id="comp-2",
            similarity=0.7,
            source_domain="api",
            target_domain="database"
        )

        # Update with new similarity
        tracker.record_similarity(
            source_id="comp-1",
            target_id="comp-2",
            similarity=0.9,
            source_domain="api",
            target_domain="database"
        )

        connections = tracker.get_connections("comp-1")

        # Should have only one edge with updated similarity
        assert len(connections) == 1
        assert connections[0][2] == 0.9


class TestRecordMatches:
    """Tests for batch recording from reminds_me_of results."""

    def test_record_matches_creates_edges(self, tracker):
        """record_matches creates edges for all matches."""
        source = make_comprehension(id="source-1", domain="api")
        matches = [
            SimilarityMatch(comprehension_id="target-1", domain="database", similarity=0.85),
            SimilarityMatch(comprehension_id="target-2", domain="auth", similarity=0.75),
        ]

        tracker.record_matches(source, matches)

        connections = tracker.get_connections("source-1")

        assert len(connections) == 2
        target_ids = {c[0] for c in connections}
        assert target_ids == {"target-1", "target-2"}

    def test_record_matches_empty_list(self, tracker):
        """record_matches with empty list does nothing."""
        source = make_comprehension(id="source-1", domain="api")

        tracker.record_matches(source, [])

        connections = tracker.get_connections("source-1")
        assert len(connections) == 0


class TestGetConnections:
    """Tests for retrieving connections."""

    def test_get_connections_returns_outgoing(self, tracker):
        """get_connections returns edges where comp is source."""
        tracker.record_similarity(
            source_id="comp-1",
            target_id="comp-2",
            similarity=0.8,
            source_domain="api",
            target_domain="database"
        )

        connections = tracker.get_connections("comp-1")

        assert len(connections) == 1
        assert connections[0][0] == "comp-2"

    def test_get_connections_returns_incoming(self, tracker):
        """get_connections returns edges where comp is target."""
        tracker.record_similarity(
            source_id="comp-1",
            target_id="comp-2",
            similarity=0.8,
            source_domain="api",
            target_domain="database"
        )

        # Get connections for the target
        connections = tracker.get_connections("comp-2")

        assert len(connections) == 1
        assert connections[0][0] == "comp-1"

    def test_get_connections_bidirectional(self, tracker):
        """get_connections returns both incoming and outgoing."""
        # comp-1 -> comp-2
        tracker.record_similarity(
            source_id="comp-1",
            target_id="comp-2",
            similarity=0.8,
            source_domain="api",
            target_domain="database"
        )
        # comp-3 -> comp-1
        tracker.record_similarity(
            source_id="comp-3",
            target_id="comp-1",
            similarity=0.75,
            source_domain="auth",
            target_domain="api"
        )

        connections = tracker.get_connections("comp-1")

        # Should have both outgoing to comp-2 and incoming from comp-3
        assert len(connections) == 2
        other_ids = {c[0] for c in connections}
        assert other_ids == {"comp-2", "comp-3"}

    def test_get_connections_no_edges(self, tracker):
        """get_connections returns empty list when no edges."""
        connections = tracker.get_connections("nonexistent")

        assert connections == []


class TestGetHotspots:
    """Tests for hotspot detection."""

    def test_get_hotspots_detects_cross_domain_accumulation(self, tracker):
        """get_hotspots finds comprehensions with cross-domain connections."""
        # Create a hotspot: comp-target has connections from 3 domains
        tracker.record_similarity(
            source_id="api-1", target_id="target",
            similarity=0.8, source_domain="api", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="database-1", target_id="target",
            similarity=0.75, source_domain="database", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="auth-1", target_id="target",
            similarity=0.7, source_domain="auth", target_domain="patterns"
        )

        hotspots = tracker.get_hotspots(min_domains=2, min_connections=2)

        assert len(hotspots) == 1
        assert hotspots[0].comprehension_id == "target"
        assert hotspots[0].domain_count == 3
        assert hotspots[0].connection_count == 3

    def test_get_hotspots_filters_by_min_domains(self, tracker):
        """get_hotspots excludes items below min_domains threshold."""
        # Single domain connection
        tracker.record_similarity(
            source_id="api-1", target_id="target",
            similarity=0.8, source_domain="api", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="api-2", target_id="target",
            similarity=0.75, source_domain="api", target_domain="patterns"
        )

        # Require 2 domains - should not find this target
        hotspots = tracker.get_hotspots(min_domains=2, min_connections=1)

        assert len(hotspots) == 0

    def test_get_hotspots_filters_by_min_connections(self, tracker):
        """get_hotspots excludes items below min_connections threshold."""
        # Only 2 connections from 2 domains
        tracker.record_similarity(
            source_id="api-1", target_id="target",
            similarity=0.8, source_domain="api", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="database-1", target_id="target",
            similarity=0.75, source_domain="database", target_domain="patterns"
        )

        # Require 3 connections - should not find this target
        hotspots = tracker.get_hotspots(min_domains=2, min_connections=3)

        assert len(hotspots) == 0

    def test_get_hotspots_orders_by_domain_count_then_similarity(self, tracker):
        """get_hotspots returns results ordered by domain_count DESC, avg_similarity DESC."""
        # Hotspot A: 3 domains, avg ~0.75
        tracker.record_similarity(
            source_id="api-1", target_id="hotspot-a",
            similarity=0.8, source_domain="api", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="database-1", target_id="hotspot-a",
            similarity=0.75, source_domain="database", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="auth-1", target_id="hotspot-a",
            similarity=0.7, source_domain="auth", target_domain="patterns"
        )

        # Hotspot B: 2 domains, avg ~0.85
        tracker.record_similarity(
            source_id="infra-1", target_id="hotspot-b",
            similarity=0.85, source_domain="infra", target_domain="system"
        )
        tracker.record_similarity(
            source_id="network-1", target_id="hotspot-b",
            similarity=0.85, source_domain="network", target_domain="system"
        )

        hotspots = tracker.get_hotspots(min_domains=2, min_connections=2)

        # Should have both hotspots, A first (more domains)
        assert len(hotspots) == 2
        assert hotspots[0].comprehension_id == "hotspot-a"
        assert hotspots[1].comprehension_id == "hotspot-b"

    def test_get_hotspots_calculates_avg_similarity(self, tracker):
        """get_hotspots correctly calculates average similarity."""
        tracker.record_similarity(
            source_id="api-1", target_id="target",
            similarity=0.8, source_domain="api", target_domain="patterns"
        )
        tracker.record_similarity(
            source_id="database-1", target_id="target",
            similarity=0.6, source_domain="database", target_domain="patterns"
        )

        hotspots = tracker.get_hotspots(min_domains=2, min_connections=2)

        assert len(hotspots) == 1
        assert hotspots[0].avg_similarity == pytest.approx(0.7, rel=0.01)


class TestRemoveEdges:
    """Tests for edge cleanup."""

    def test_remove_edges_removes_outgoing(self, tracker):
        """remove_edges removes edges where comp is source."""
        tracker.record_similarity(
            source_id="comp-1", target_id="comp-2",
            similarity=0.8, source_domain="api", target_domain="database"
        )

        removed = tracker.remove_edges("comp-1")

        assert removed == 1
        assert tracker.get_connections("comp-1") == []

    def test_remove_edges_removes_incoming(self, tracker):
        """remove_edges removes edges where comp is target."""
        tracker.record_similarity(
            source_id="comp-1", target_id="comp-2",
            similarity=0.8, source_domain="api", target_domain="database"
        )

        removed = tracker.remove_edges("comp-2")

        assert removed == 1
        assert tracker.get_connections("comp-2") == []

    def test_remove_edges_removes_both_directions(self, tracker):
        """remove_edges removes all edges involving the comprehension."""
        # Outgoing edge
        tracker.record_similarity(
            source_id="comp-1", target_id="comp-2",
            similarity=0.8, source_domain="api", target_domain="database"
        )
        # Incoming edge
        tracker.record_similarity(
            source_id="comp-3", target_id="comp-1",
            similarity=0.75, source_domain="auth", target_domain="api"
        )

        removed = tracker.remove_edges("comp-1")

        assert removed == 2
        assert tracker.get_connections("comp-1") == []

    def test_remove_edges_nonexistent_returns_zero(self, tracker):
        """remove_edges on non-existent comprehension returns 0."""
        removed = tracker.remove_edges("nonexistent")

        assert removed == 0


class TestAccumulationHotspotDataclass:
    """Tests for AccumulationHotspot structure."""

    def test_accumulation_hotspot_fields(self):
        """AccumulationHotspot has expected fields."""
        hotspot = AccumulationHotspot(
            comprehension_id="test-id",
            domain_count=3,
            connection_count=5,
            avg_similarity=0.75
        )

        assert hotspot.comprehension_id == "test-id"
        assert hotspot.domain_count == 3
        assert hotspot.connection_count == 5
        assert hotspot.avg_similarity == 0.75
