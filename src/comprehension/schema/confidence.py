"""Confidence level definitions for beliefs."""

from enum import Enum


class ConfidenceLevel(str, Enum):
    """Natural language confidence levels for beliefs.

    Operational definitions:
    - HIGH: Verified against behavior; multiple confirmations; would bet on it
    - MEDIUM: Single confirmation; reasonable evidence; plausible but not certain
    - LOW: Tentative hypothesis; needs validation before acting
    - UNKNOWN: Explicitly uncertain; do not act on without more evidence
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"
