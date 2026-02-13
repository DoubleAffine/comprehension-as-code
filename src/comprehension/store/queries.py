"""Query builders and helpers for comprehension retrieval."""

from typing import List, Optional, Tuple, Any

from comprehension.schema import ConfidenceLevel


# Ordinal ordering for confidence levels
# Used for >= comparisons (e.g., "at least MEDIUM" includes MEDIUM and HIGH)
CONFIDENCE_ORDER = {
    ConfidenceLevel.UNKNOWN: 0,
    ConfidenceLevel.LOW: 1,
    ConfidenceLevel.MEDIUM: 2,
    ConfidenceLevel.HIGH: 3,
}


def get_confidence_values_at_or_above(min_level: ConfidenceLevel) -> List[str]:
    """Get all confidence level values at or above the minimum.

    Args:
        min_level: The minimum confidence level

    Returns:
        List of confidence string values (e.g., ["high", "medium"])
    """
    min_order = CONFIDENCE_ORDER[min_level]
    return [
        level.value
        for level, order in CONFIDENCE_ORDER.items()
        if order >= min_order
    ]


def build_confidence_filter(min_level: ConfidenceLevel) -> Tuple[str, List[str]]:
    """Build SQL fragment for confidence filtering.

    Returns SQL WHERE clause fragment and parameters.

    Args:
        min_level: Minimum confidence level to include

    Returns:
        Tuple of (SQL fragment, list of parameter values)
    """
    values = get_confidence_values_at_or_above(min_level)
    placeholders = ", ".join("?" for _ in values)
    return f"confidence IN ({placeholders})", values


def build_filter_query(
    domain: Optional[str] = None,
    min_confidence: Optional[ConfidenceLevel] = None,
    limit: Optional[int] = None,
) -> Tuple[str, List[Any]]:
    """Build SQL query with optional filters.

    Constructs a SELECT query for the comprehensions table with
    optional domain and confidence filtering. Results are always
    ordered by updated DESC (most recent first).

    Args:
        domain: Optional domain to filter by (exact match)
        min_confidence: Optional minimum confidence level
        limit: Optional maximum number of results

    Returns:
        Tuple of (SQL query string, list of parameters)
    """
    query = "SELECT data FROM comprehensions"
    conditions: List[str] = []
    params: List[Any] = []

    if domain is not None:
        conditions.append("domain = ?")
        params.append(domain)

    if min_confidence is not None:
        conf_sql, conf_params = build_confidence_filter(min_confidence)
        conditions.append(conf_sql)
        params.extend(conf_params)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    return query, params
