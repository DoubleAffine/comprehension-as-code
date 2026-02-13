"""Parse comprehension and observation documents from Markdown with YAML frontmatter."""

from pathlib import Path
from typing import Union

import frontmatter
from pydantic import ValidationError

from comprehension.schema import Comprehension, Observation


def load_comprehension(filepath: Union[str, Path]) -> Comprehension:
    """Load and validate a comprehension document.

    Args:
        filepath: Path to Markdown file with YAML frontmatter

    Returns:
        Validated Comprehension model

    Raises:
        ValueError: If document fails validation
        FileNotFoundError: If file doesn't exist
    """
    with open(filepath, "r") as f:
        doc = frontmatter.load(f)

    try:
        return Comprehension(**doc.metadata)
    except ValidationError as e:
        raise ValueError(f"Invalid comprehension document {filepath}: {e}")


def load_observation(filepath: Union[str, Path]) -> Observation:
    """Load and validate an observation document.

    Args:
        filepath: Path to Markdown file with YAML frontmatter

    Returns:
        Validated Observation model

    Raises:
        ValueError: If document fails validation
        FileNotFoundError: If file doesn't exist
    """
    with open(filepath, "r") as f:
        doc = frontmatter.load(f)

    try:
        return Observation(**doc.metadata)
    except ValidationError as e:
        raise ValueError(f"Invalid observation document {filepath}: {e}")
