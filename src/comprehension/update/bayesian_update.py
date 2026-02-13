"""Core Bayesian update operation.

This IS the compression operation. The new posterior encodes what the
observation taught, allowing the observation to be garbage collected.
"""

from datetime import datetime, timezone
from typing import Optional

from comprehension.schema import (
    Comprehension, Observation, BeliefPosterior, ConfidenceLevel
)
from comprehension.update.confidence_rules import (
    EvidenceType, compute_confidence_transition
)


def bayesian_update(
    observation: Observation,
    comprehension: Comprehension,
    evidence_type: EvidenceType,
    new_statement: Optional[str] = None,
    update_reasoning: Optional[str] = None,
) -> Comprehension:
    """Apply Bayesian update: observation informs comprehension.

    This IS the compression operation. The new posterior encodes what
    the observation taught, allowing observation GC afterward.

    Args:
        observation: Evidence to incorporate
        comprehension: Current belief state
        evidence_type: How observation relates to belief
        new_statement: Updated belief statement (required if contradicting)
        update_reasoning: Explanation of belief change (auto-generated if not provided)

    Returns:
        New Comprehension with updated posterior

    Raises:
        ValueError: If contradicting evidence but no new statement provided
    """
    # Idempotency check: already incorporated
    if observation.id in comprehension.observations:
        return comprehension

    # Validate: contradicting evidence requires new statement
    if evidence_type == EvidenceType.CONTRADICTING and new_statement is None:
        raise ValueError(
            "Contradicting evidence requires a new belief statement. "
            "Provide new_statement parameter."
        )

    # Compute confidence transition
    old_confidence = comprehension.posterior.confidence
    new_confidence = compute_confidence_transition(old_confidence, evidence_type)

    # Determine final statement
    final_statement = (
        new_statement
        if new_statement is not None
        else comprehension.posterior.statement
    )

    # Build update reasoning if not provided
    if update_reasoning is None:
        update_reasoning = (
            f"Observation {observation.id} ({evidence_type.value}) "
            f"changed confidence from {old_confidence.value} to {new_confidence.value}"
        )

    # Create new posterior (immutable)
    new_posterior = BeliefPosterior(
        statement=final_statement,
        confidence=new_confidence,
        update_reasoning=update_reasoning,
        observations_used=comprehension.posterior.observations_used + [observation.id],
    )

    # Return new comprehension (immutable copy with updates)
    return comprehension.model_copy(update={
        "posterior": new_posterior,
        "observations": comprehension.observations + [observation.id],
        "updated": datetime.now(timezone.utc),
        "version": comprehension.version + 1,
    })
