"""Observation model: raw events without interpretation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Raw observation—what happened, without interpretation.

    Observations are episodic events captured during agent execution.
    They are inputs to comprehension (belief updates), not conclusions.

    Key distinction: Observations are WHAT HAPPENED;
    Comprehension is WHAT WE NOW BELIEVE.
    """

    id: str = Field(
        description="Unique identifier (e.g., 'obs-001' or 'obs-2026-02-13-abc123')"
    )
    timestamp: datetime = Field(
        description="When the observation was made"
    )
    source: str = Field(
        description="Agent/system that made the observation (e.g., 'agent/api-integration-agent')"
    )
    event: str = Field(
        description="Natural language description of what was observed"
    )
    context: dict = Field(
        default_factory=dict,
        description="Additional context (project, task, prior_belief ref, etc.)"
    )
    trace_ref: Optional[str] = Field(
        default=None,
        description="Reference to full execution trace if available"
    )
    spec: str = Field(
        default="observation/v1",
        description="Schema version for this observation format"
    )
