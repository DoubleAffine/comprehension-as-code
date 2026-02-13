"""Confidence transition rules for Bayesian updates.

Defines explicit rules for how confidence levels change based on evidence type.
This is a deterministic state machine, not LLM judgment.
"""

from enum import Enum
from typing import Tuple

from comprehension.schema.confidence import ConfidenceLevel


class EvidenceType(str, Enum):
    """Classification of how observation relates to belief."""
    CONFIRMING = "confirming"      # Supports existing belief
    CONTRADICTING = "contradicting" # Challenges existing belief
    NEUTRAL = "neutral"            # Doesn't clearly support or contradict


# Confidence transition rules
# Format: (current_confidence, evidence_type) -> new_confidence
CONFIDENCE_TRANSITIONS: dict[Tuple[ConfidenceLevel, EvidenceType], ConfidenceLevel] = {
    # From UNKNOWN
    (ConfidenceLevel.UNKNOWN, EvidenceType.CONFIRMING): ConfidenceLevel.LOW,
    (ConfidenceLevel.UNKNOWN, EvidenceType.CONTRADICTING): ConfidenceLevel.LOW,
    (ConfidenceLevel.UNKNOWN, EvidenceType.NEUTRAL): ConfidenceLevel.UNKNOWN,

    # From LOW
    (ConfidenceLevel.LOW, EvidenceType.CONFIRMING): ConfidenceLevel.MEDIUM,
    (ConfidenceLevel.LOW, EvidenceType.CONTRADICTING): ConfidenceLevel.LOW,
    (ConfidenceLevel.LOW, EvidenceType.NEUTRAL): ConfidenceLevel.LOW,

    # From MEDIUM
    (ConfidenceLevel.MEDIUM, EvidenceType.CONFIRMING): ConfidenceLevel.HIGH,
    (ConfidenceLevel.MEDIUM, EvidenceType.CONTRADICTING): ConfidenceLevel.LOW,
    (ConfidenceLevel.MEDIUM, EvidenceType.NEUTRAL): ConfidenceLevel.MEDIUM,

    # From HIGH
    (ConfidenceLevel.HIGH, EvidenceType.CONFIRMING): ConfidenceLevel.HIGH,
    (ConfidenceLevel.HIGH, EvidenceType.CONTRADICTING): ConfidenceLevel.MEDIUM,
    (ConfidenceLevel.HIGH, EvidenceType.NEUTRAL): ConfidenceLevel.HIGH,
}


def compute_confidence_transition(
    current: ConfidenceLevel,
    evidence_type: EvidenceType
) -> ConfidenceLevel:
    """Apply confidence transition rule.

    Args:
        current: Current confidence level
        evidence_type: How observation relates to belief

    Returns:
        New confidence level after applying transition rule
    """
    return CONFIDENCE_TRANSITIONS.get(
        (current, evidence_type),
        current  # Default: no change
    )
