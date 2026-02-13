"""Tests for the core Bayesian update operation."""

import pytest
from datetime import datetime, timezone

from comprehension.schema import (
    Comprehension, Observation, BeliefPrior, BeliefPosterior, ConfidenceLevel
)
from comprehension.update import EvidenceType
from comprehension.update.bayesian_update import bayesian_update


@pytest.fixture
def sample_observation():
    """Create a sample observation for testing."""
    return Observation(
        id="obs-test-001",
        timestamp=datetime.now(timezone.utc),
        source="test-agent",
        event="Observed that API returns 200 on valid request",
        context={"endpoint": "/api/test"},
    )


@pytest.fixture
def sample_comprehension():
    """Create a sample comprehension for testing."""
    now = datetime.now(timezone.utc)
    return Comprehension(
        id="comp-test-001",
        topic="API response behavior",
        domain="api",
        prior=BeliefPrior(
            statement="API should return 200 on valid requests",
            confidence=ConfidenceLevel.LOW,
            source="documentation",
        ),
        observations=[],
        posterior=BeliefPosterior(
            statement="API should return 200 on valid requests",
            confidence=ConfidenceLevel.LOW,
            update_reasoning="Initial belief from documentation",
            observations_used=[],
        ),
        created=now,
        updated=now,
        version=1,
    )


class TestBasicUpdate:
    """Basic update operation produces new comprehension."""

    def test_returns_new_comprehension(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        # Must return Comprehension, not modify in place
        assert isinstance(result, Comprehension)
        assert result is not sample_comprehension

    def test_increments_version(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        assert result.version == sample_comprehension.version + 1

    def test_updates_timestamp(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        assert result.updated >= sample_comprehension.updated


class TestProvenanceTracking:
    """Provenance tracks which observations informed belief."""

    def test_observation_id_in_observations_list(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        assert sample_observation.id in result.observations

    def test_observation_id_in_posterior_observations_used(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        assert sample_observation.id in result.posterior.observations_used

    def test_preserves_existing_observations(self, sample_observation, sample_comprehension):
        # Add a prior observation
        prior_obs_id = "obs-prior-001"
        comp_with_prior = sample_comprehension.model_copy(update={
            "observations": [prior_obs_id],
            "posterior": sample_comprehension.posterior.model_copy(update={
                "observations_used": [prior_obs_id],
            }),
        })

        result = bayesian_update(
            observation=sample_observation,
            comprehension=comp_with_prior,
            evidence_type=EvidenceType.CONFIRMING,
        )

        assert prior_obs_id in result.observations
        assert sample_observation.id in result.observations
        assert prior_obs_id in result.posterior.observations_used
        assert sample_observation.id in result.posterior.observations_used


class TestIdempotency:
    """Same observation applied twice returns unchanged comprehension."""

    def test_idempotent_update(self, sample_observation, sample_comprehension):
        # First update
        first_result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )

        # Second update with same observation
        second_result = bayesian_update(
            observation=sample_observation,
            comprehension=first_result,
            evidence_type=EvidenceType.CONFIRMING,
        )

        # Should be unchanged (same object or equal)
        assert second_result.version == first_result.version
        assert second_result.observations == first_result.observations

    def test_idempotent_no_duplicate_in_observations(self, sample_observation, sample_comprehension):
        first_result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )

        second_result = bayesian_update(
            observation=sample_observation,
            comprehension=first_result,
            evidence_type=EvidenceType.CONFIRMING,
        )

        # Observation ID should appear exactly once
        assert second_result.observations.count(sample_observation.id) == 1


class TestConfidenceTransitions:
    """Update uses confidence transition rules."""

    def test_confirming_increases_confidence(self, sample_observation, sample_comprehension):
        # sample_comprehension starts at LOW
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        assert result.posterior.confidence == ConfidenceLevel.MEDIUM

    def test_contradicting_decreases_confidence(self, sample_observation):
        # Start with HIGH confidence
        now = datetime.now(timezone.utc)
        high_confidence_comp = Comprehension(
            id="comp-test-high",
            topic="Test topic",
            domain="test",
            prior=BeliefPrior(
                statement="Original belief",
                confidence=ConfidenceLevel.HIGH,
                source="test",
            ),
            observations=[],
            posterior=BeliefPosterior(
                statement="Original belief",
                confidence=ConfidenceLevel.HIGH,
                update_reasoning="Prior high confidence",
                observations_used=[],
            ),
            created=now,
            updated=now,
        )

        result = bayesian_update(
            observation=sample_observation,
            comprehension=high_confidence_comp,
            evidence_type=EvidenceType.CONTRADICTING,
            new_statement="Updated belief after contradiction",
        )
        assert result.posterior.confidence == ConfidenceLevel.MEDIUM


class TestContradictingEvidence:
    """Contradicting evidence requires new belief statement."""

    def test_contradicting_requires_new_statement(self, sample_observation, sample_comprehension):
        with pytest.raises(ValueError, match="new.*statement"):
            bayesian_update(
                observation=sample_observation,
                comprehension=sample_comprehension,
                evidence_type=EvidenceType.CONTRADICTING,
                # Missing new_statement
            )

    def test_contradicting_with_new_statement_succeeds(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONTRADICTING,
            new_statement="Revised belief after contradicting evidence",
        )
        assert result.posterior.statement == "Revised belief after contradicting evidence"


class TestUpdateReasoning:
    """Update includes reasoning about how observation changed belief."""

    def test_custom_reasoning_preserved(self, sample_observation, sample_comprehension):
        custom_reasoning = "API test confirmed the expected behavior"
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
            update_reasoning=custom_reasoning,
        )
        assert custom_reasoning in result.posterior.update_reasoning

    def test_default_reasoning_generated(self, sample_observation, sample_comprehension):
        result = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )
        # Should have some reasoning even if not provided
        assert len(result.posterior.update_reasoning) > 0
        assert sample_observation.id in result.posterior.update_reasoning


class TestImmutability:
    """Update does not mutate original comprehension."""

    def test_original_unchanged(self, sample_observation, sample_comprehension):
        original_observations = sample_comprehension.observations.copy()
        original_version = sample_comprehension.version

        _ = bayesian_update(
            observation=sample_observation,
            comprehension=sample_comprehension,
            evidence_type=EvidenceType.CONFIRMING,
        )

        assert sample_comprehension.observations == original_observations
        assert sample_comprehension.version == original_version
