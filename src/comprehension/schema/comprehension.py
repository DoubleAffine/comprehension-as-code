"""Comprehension model: structured understanding with Bayesian belief updates."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .confidence import ConfidenceLevel


class BeliefPrior(BaseModel):
    """Prior belief before observations.

    Represents what was believed BEFORE seeing new evidence.
    Source indicates where this prior came from.
    """

    statement: str = Field(
        description="Natural language belief statement"
    )
    confidence: ConfidenceLevel = Field(
        description="How confident in this belief before observations"
    )
    source: str = Field(
        description="Where prior came from: 'training', 'accumulated', 'documentation', etc."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Why this was believed (optional elaboration)"
    )


class BeliefPosterior(BaseModel):
    """Updated belief after observations.

    Represents what is now believed AFTER incorporating evidence.
    Must explain how observations changed the belief.
    """

    statement: str = Field(
        description="Natural language updated belief statement"
    )
    confidence: ConfidenceLevel = Field(
        description="How confident in this belief after observations"
    )
    update_reasoning: str = Field(
        description="How observations changed the belief (required)"
    )
    observations_used: List[str] = Field(
        description="References to observation IDs that informed this update"
    )


class Comprehension(BaseModel):
    """Structured understanding with Bayesian belief update history.

    Comprehension is the primary artifact in this system.
    It represents verified understanding, not just raw observations.

    Structure follows Bayesian epistemology:
    - Prior: What was believed before
    - Observations: What was observed (by ID reference)
    - Posterior: What is believed now, and why
    """

    id: str = Field(
        description="Unique identifier (e.g., 'comp-api-auth-001')"
    )
    topic: str = Field(
        description="What this comprehension is about (natural language)"
    )
    domain: str = Field(
        description="Category for retrieval (api, database, architecture, etc.)"
    )
    prior: BeliefPrior = Field(
        description="Belief before observations"
    )
    observations: List[str] = Field(
        description="Observation IDs that informed this comprehension"
    )
    posterior: BeliefPosterior = Field(
        description="Updated belief after observations"
    )
    created: datetime = Field(
        description="When this comprehension was first created"
    )
    updated: datetime = Field(
        description="When this comprehension was last updated"
    )
    version: int = Field(
        default=1,
        description="Version number, increments on update"
    )
    verified: bool = Field(
        default=False,
        description="Has behavioral verification passed?"
    )
    spec: str = Field(
        default="comprehension/v1",
        description="Schema version for this comprehension format"
    )
