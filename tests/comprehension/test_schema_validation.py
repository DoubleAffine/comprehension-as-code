"""Tests for comprehension and observation schema validation."""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from comprehension.parser import load_comprehension, load_observation
from comprehension.schema import (
    BeliefPosterior,
    BeliefPrior,
    Comprehension,
    ConfidenceLevel,
    Observation,
)

SAMPLE_DIR = Path(__file__).parent.parent.parent / "spec" / "examples"


class TestSampleDocuments:
    """Test that sample documents validate against schemas."""

    @pytest.mark.parametrize(
        "filepath", list(SAMPLE_DIR.glob("sample_comprehension*.md"))
    )
    def test_comprehension_samples_valid(self, filepath):
        """All sample comprehension documents must validate against schema."""
        comp = load_comprehension(filepath)

        # Verify structure
        assert comp.id is not None
        assert comp.prior is not None
        assert comp.posterior is not None
        assert comp.posterior.confidence in ConfidenceLevel
        assert len(comp.observations) > 0 or comp.prior.source == "training"

    @pytest.mark.parametrize(
        "filepath", list(SAMPLE_DIR.glob("sample_observation*.md"))
    )
    def test_observation_samples_valid(self, filepath):
        """All sample observation documents must validate against schema."""
        obs = load_observation(filepath)

        # Verify structure
        assert obs.id is not None
        assert obs.timestamp is not None
        assert obs.source is not None
        assert obs.event is not None


class TestSchemaValidation:
    """Test schema validation catches invalid documents."""

    def test_comprehension_requires_prior(self):
        """Comprehension must have prior belief."""
        with pytest.raises(ValidationError):
            Comprehension(
                id="test",
                topic="test",
                domain="test",
                # missing prior
                observations=[],
                posterior=BeliefPosterior(
                    statement="test",
                    confidence=ConfidenceLevel.LOW,
                    update_reasoning="test",
                    observations_used=[],
                ),
                created=datetime.now(),
                updated=datetime.now(),
            )

    def test_comprehension_requires_posterior(self):
        """Comprehension must have posterior belief."""
        with pytest.raises(ValidationError):
            Comprehension(
                id="test",
                topic="test",
                domain="test",
                prior=BeliefPrior(
                    statement="test",
                    confidence=ConfidenceLevel.LOW,
                    source="test",
                ),
                observations=[],
                # missing posterior
                created=datetime.now(),
                updated=datetime.now(),
            )

    def test_confidence_must_be_valid_level(self):
        """Confidence must be HIGH, MEDIUM, LOW, or UNKNOWN."""
        with pytest.raises(ValidationError):
            BeliefPrior(
                statement="test",
                confidence="very_high",  # invalid
                source="test",
            )

    def test_observation_requires_timestamp(self):
        """Observation must have timestamp."""
        with pytest.raises(ValidationError):
            Observation(
                id="test",
                # missing timestamp
                source="test",
                event="test",
            )

    def test_observation_requires_source(self):
        """Observation must have source."""
        with pytest.raises(ValidationError):
            Observation(
                id="test",
                timestamp=datetime.now(),
                # missing source
                event="test",
            )


class TestConfidenceLevels:
    """Test confidence level definitions."""

    def test_confidence_levels_exist(self):
        """All four confidence levels must exist."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.UNKNOWN.value == "unknown"

    def test_confidence_is_string_enum(self):
        """Confidence levels must be string values for natural language."""
        assert isinstance(ConfidenceLevel.HIGH.value, str)
        assert isinstance(ConfidenceLevel.MEDIUM.value, str)
        assert isinstance(ConfidenceLevel.LOW.value, str)
        assert isinstance(ConfidenceLevel.UNKNOWN.value, str)

    def test_confidence_count(self):
        """Exactly four confidence levels."""
        assert len(ConfidenceLevel) == 4


class TestBayesianStructure:
    """Test Bayesian belief structure."""

    def test_prior_has_required_fields(self):
        """BeliefPrior must have statement, confidence, source."""
        prior = BeliefPrior(
            statement="Test belief",
            confidence=ConfidenceLevel.MEDIUM,
            source="documentation",
        )
        assert prior.statement == "Test belief"
        assert prior.confidence == ConfidenceLevel.MEDIUM
        assert prior.source == "documentation"
        assert prior.reasoning is None  # Optional

    def test_posterior_has_required_fields(self):
        """BeliefPosterior must have statement, confidence, update_reasoning, observations_used."""
        posterior = BeliefPosterior(
            statement="Updated belief",
            confidence=ConfidenceLevel.HIGH,
            update_reasoning="Evidence confirmed hypothesis",
            observations_used=["obs-001", "obs-002"],
        )
        assert posterior.statement == "Updated belief"
        assert posterior.confidence == ConfidenceLevel.HIGH
        assert posterior.update_reasoning == "Evidence confirmed hypothesis"
        assert posterior.observations_used == ["obs-001", "obs-002"]

    def test_posterior_requires_update_reasoning(self):
        """BeliefPosterior must explain how observations changed belief."""
        with pytest.raises(ValidationError):
            BeliefPosterior(
                statement="test",
                confidence=ConfidenceLevel.HIGH,
                # missing update_reasoning
                observations_used=[],
            )
