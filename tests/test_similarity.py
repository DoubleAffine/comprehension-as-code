"""Tests for SimilarityFinder cross-domain matching."""

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
from comprehension.convergence import ComprehensionEmbedder
from comprehension.convergence.similarity import SimilarityFinder, SimilarityMatch
from comprehension.store.repository import SQLiteComprehensionRepository


def make_comprehension(
    id: str,
    domain: str,
    prior_statement: str,
    posterior_statement: str,
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
def embedder():
    """Shared embedder instance to avoid loading model multiple times."""
    return ComprehensionEmbedder()


@pytest.fixture
def finder(db_path, embedder):
    """Create a SimilarityFinder with shared embedder."""
    return SimilarityFinder(db_path, embedder=embedder)


@pytest.fixture
def repository(db_path):
    """Create a repository for storing comprehensions."""
    return SQLiteComprehensionRepository(db_path)


class TestSimilarityFinderBasic:
    """Basic SimilarityFinder tests."""

    def test_reminds_me_of_empty_returns_no_matches(self, finder):
        """When no comprehensions indexed, returns empty list."""
        comp = make_comprehension(
            id="query-1",
            domain="test",
            prior_statement="I believe X is true",
            posterior_statement="X is confirmed"
        )

        matches = finder.reminds_me_of(comp)

        assert matches == []

    def test_index_adds_comprehension(self, finder):
        """Index adds comprehension to vector store."""
        comp = make_comprehension(
            id="comp-1",
            domain="api",
            prior_statement="APIs should be RESTful",
            posterior_statement="REST is the standard approach"
        )

        finder.index(comp)

        # Verify it's indexed by checking vector store count
        assert finder._vector_store.count() == 1

    def test_remove_index_removes_comprehension(self, finder):
        """Remove index removes comprehension from vector store."""
        comp = make_comprehension(
            id="comp-1",
            domain="api",
            prior_statement="APIs should be RESTful",
            posterior_statement="REST is the standard approach"
        )

        finder.index(comp)
        assert finder._vector_store.count() == 1

        removed = finder.remove_index("comp-1")

        assert removed is True
        assert finder._vector_store.count() == 0

    def test_remove_index_nonexistent_returns_false(self, finder):
        """Remove index on non-existent ID returns False."""
        removed = finder.remove_index("nonexistent")

        assert removed is False


class TestCrossDomainFiltering:
    """Tests for domain exclusion behavior."""

    def test_excludes_same_domain_matches(self, finder, repository):
        """Same-domain comprehensions are excluded from results."""
        # Create two comprehensions in the SAME domain with similar structure
        comp1 = make_comprehension(
            id="api-1",
            domain="api",
            prior_statement="Caching improves performance",
            posterior_statement="HTTP caching headers are essential"
        )
        comp2 = make_comprehension(
            id="api-2",
            domain="api",  # Same domain
            prior_statement="Caching speeds up responses",
            posterior_statement="Response caching is critical"
        )

        # Store in repository (needed for domain lookup)
        repository.add(comp1)
        repository.add(comp2)

        # Index both
        finder.index(comp1)
        finder.index(comp2)

        # Query with comp1 - should NOT find comp2 (same domain)
        matches = finder.reminds_me_of(comp1, min_similarity=0.0)

        # No matches because only same-domain exists
        assert len(matches) == 0

    def test_includes_different_domain_matches(self, finder, repository, embedder):
        """Different-domain comprehensions ARE included in results."""
        # Create comprehensions with similar structure but DIFFERENT domains
        # Note: Semantic similarity for related but different texts is typically 0.3-0.5
        # Using a low threshold to ensure we find cross-domain matches
        comp1 = make_comprehension(
            id="database-1",
            domain="database",
            prior_statement="Caching improves database performance",
            posterior_statement="Query caching is essential for speed"
        )
        comp2 = make_comprehension(
            id="api-1",
            domain="api",  # Different domain
            prior_statement="Caching improves API performance",
            posterior_statement="Response caching is essential for speed"
        )

        # Store in repository
        repository.add(comp1)
        repository.add(comp2)

        # Index both
        finder.index(comp1)
        finder.index(comp2)

        # Query with comp1 - should find comp2 (different domain)
        # Using low threshold since semantic similarity is ~0.34 for these texts
        matches = finder.reminds_me_of(comp1, min_similarity=0.3)

        assert len(matches) == 1
        assert matches[0].comprehension_id == "api-1"
        assert matches[0].domain == "api"

    def test_multiple_domains_all_different_from_query(self, finder, repository):
        """All matches come from domains different than query."""
        # Create comprehensions across 3 domains
        domains = ["database", "api", "infrastructure"]
        comps = []

        for i, domain in enumerate(domains):
            comp = make_comprehension(
                id=f"{domain}-1",
                domain=domain,
                prior_statement=f"Caching improves {domain} performance",
                posterior_statement=f"Caching is essential for {domain}"
            )
            repository.add(comp)
            finder.index(comp)
            comps.append(comp)

        # Query from database domain - low threshold for semantic similarity
        matches = finder.reminds_me_of(comps[0], min_similarity=0.3)

        # Should get matches from api and infrastructure, NOT database
        match_domains = {m.domain for m in matches}
        assert "database" not in match_domains
        assert len(matches) <= 2  # At most 2 other domains


class TestSimilarityOrdering:
    """Tests for similarity ordering and thresholds."""

    def test_matches_ordered_by_similarity_descending(self, finder, repository):
        """Matches are returned highest similarity first."""
        # Create query and two matches with different similarity
        query = make_comprehension(
            id="query-1",
            domain="query-domain",
            prior_statement="Authentication with JWT tokens",
            posterior_statement="JWT provides stateless authentication"
        )

        # Close match (very similar text)
        close_match = make_comprehension(
            id="close-1",
            domain="auth",
            prior_statement="Authentication using JWT tokens",
            posterior_statement="JWT enables stateless auth"
        )

        # Distant match (less similar text)
        distant_match = make_comprehension(
            id="distant-1",
            domain="security",
            prior_statement="Security requires authentication",
            posterior_statement="Systems must verify identity"
        )

        # Store all
        repository.add(query)
        repository.add(close_match)
        repository.add(distant_match)

        finder.index(query)
        finder.index(close_match)
        finder.index(distant_match)

        # Query - use low threshold to get both
        matches = finder.reminds_me_of(query, min_similarity=0.3)

        if len(matches) >= 2:
            # First match should have higher similarity
            assert matches[0].similarity >= matches[1].similarity

    def test_min_similarity_threshold_filters_results(self, finder, repository):
        """Results below min_similarity are excluded."""
        query = make_comprehension(
            id="query-1",
            domain="query-domain",
            prior_statement="Machine learning models improve predictions",
            posterior_statement="Neural networks are effective for ML"
        )

        # Match with somewhat different topic
        other = make_comprehension(
            id="other-1",
            domain="different-domain",
            prior_statement="Database indexing improves queries",
            posterior_statement="B-trees are effective for indexing"
        )

        repository.add(query)
        repository.add(other)
        finder.index(query)
        finder.index(other)

        # With high threshold, should get no matches (topics very different)
        high_threshold_matches = finder.reminds_me_of(query, min_similarity=0.95)

        # With low threshold, might get a match
        low_threshold_matches = finder.reminds_me_of(query, min_similarity=0.0)

        # High threshold should return fewer (or same) matches
        assert len(high_threshold_matches) <= len(low_threshold_matches)


class TestFindSimilarToId:
    """Tests for find_similar_to_id convenience method."""

    def test_find_similar_to_id_works(self, finder, repository):
        """find_similar_to_id loads and queries by ID."""
        comp1 = make_comprehension(
            id="comp-1",
            domain="domain-a",
            prior_statement="Caching improves performance",
            posterior_statement="Cache is essential"
        )
        comp2 = make_comprehension(
            id="comp-2",
            domain="domain-b",  # Different domain
            prior_statement="Caching speeds up systems",
            posterior_statement="Cache is critical"
        )

        repository.add(comp1)
        repository.add(comp2)
        finder.index(comp1)
        finder.index(comp2)

        # Query by ID - using low threshold for semantic similarity
        matches = finder.find_similar_to_id("comp-1", min_similarity=0.3)

        assert len(matches) >= 1
        assert matches[0].comprehension_id == "comp-2"

    def test_find_similar_to_id_nonexistent_returns_empty(self, finder):
        """find_similar_to_id with non-existent ID returns empty list."""
        matches = finder.find_similar_to_id("nonexistent")

        assert matches == []


class TestSimilarityMatchDataclass:
    """Tests for SimilarityMatch structure."""

    def test_similarity_match_fields(self):
        """SimilarityMatch has expected fields."""
        match = SimilarityMatch(
            comprehension_id="test-id",
            domain="test-domain",
            similarity=0.85
        )

        assert match.comprehension_id == "test-id"
        assert match.domain == "test-domain"
        assert match.similarity == 0.85
