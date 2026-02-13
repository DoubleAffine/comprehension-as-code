import pytest
from comprehension.schema.confidence import ConfidenceLevel
from comprehension.update.confidence_rules import (
    EvidenceType,
    compute_confidence_transition,
    CONFIDENCE_TRANSITIONS,
)

class TestEvidenceType:
    """EvidenceType enum exists with expected values."""

    def test_confirming_exists(self):
        assert EvidenceType.CONFIRMING.value == "confirming"

    def test_contradicting_exists(self):
        assert EvidenceType.CONTRADICTING.value == "contradicting"

    def test_neutral_exists(self):
        assert EvidenceType.NEUTRAL.value == "neutral"


class TestConfirmingEvidence:
    """Confirming evidence increases confidence."""

    def test_unknown_to_low(self):
        result = compute_confidence_transition(
            ConfidenceLevel.UNKNOWN, EvidenceType.CONFIRMING
        )
        assert result == ConfidenceLevel.LOW

    def test_low_to_medium(self):
        result = compute_confidence_transition(
            ConfidenceLevel.LOW, EvidenceType.CONFIRMING
        )
        assert result == ConfidenceLevel.MEDIUM

    def test_medium_to_high(self):
        result = compute_confidence_transition(
            ConfidenceLevel.MEDIUM, EvidenceType.CONFIRMING
        )
        assert result == ConfidenceLevel.HIGH

    def test_high_stays_high(self):
        result = compute_confidence_transition(
            ConfidenceLevel.HIGH, EvidenceType.CONFIRMING
        )
        assert result == ConfidenceLevel.HIGH  # Can't go higher


class TestContradictingEvidence:
    """Contradicting evidence decreases confidence."""

    def test_high_to_medium(self):
        result = compute_confidence_transition(
            ConfidenceLevel.HIGH, EvidenceType.CONTRADICTING
        )
        assert result == ConfidenceLevel.MEDIUM

    def test_medium_to_low(self):
        result = compute_confidence_transition(
            ConfidenceLevel.MEDIUM, EvidenceType.CONTRADICTING
        )
        assert result == ConfidenceLevel.LOW

    def test_low_stays_low(self):
        result = compute_confidence_transition(
            ConfidenceLevel.LOW, EvidenceType.CONTRADICTING
        )
        assert result == ConfidenceLevel.LOW  # Stays low, belief may flip

    def test_unknown_to_low(self):
        # Contradicting evidence on unknown = we learned something (low confidence)
        result = compute_confidence_transition(
            ConfidenceLevel.UNKNOWN, EvidenceType.CONTRADICTING
        )
        assert result == ConfidenceLevel.LOW


class TestNeutralEvidence:
    """Neutral evidence does not change confidence."""

    @pytest.mark.parametrize("level", [
        ConfidenceLevel.UNKNOWN,
        ConfidenceLevel.LOW,
        ConfidenceLevel.MEDIUM,
        ConfidenceLevel.HIGH,
    ])
    def test_neutral_no_change(self, level):
        result = compute_confidence_transition(level, EvidenceType.NEUTRAL)
        assert result == level


class TestTransitionsComplete:
    """All valid combinations have defined transitions."""

    def test_all_combinations_defined(self):
        for conf in ConfidenceLevel:
            for evidence in EvidenceType:
                # Should not raise, should return valid ConfidenceLevel
                result = compute_confidence_transition(conf, evidence)
                assert isinstance(result, ConfidenceLevel)
