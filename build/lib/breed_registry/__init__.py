"""The Breed Registry — model selection as breeding selection.

In the working dog paradigm, choosing the right breed is the most important
decision. This library provides structured guidance on which base model to
use for which task.

It is the **selection layer** of Working Animal Architecture — it returns
recommendations; the caller dispatches.

Quick start::

    from breed_registry import select_breed, compare_breeds, assess_aptitude

    # Find the best breed for a task — returns ModelAssessment list, ranked
    recommendations = select_breed("code_generation", top_k=3)

    # Compare two breeds head-to-head
    report = compare_breeds("gpt-4", "claude-3")

    # Check one model × one task, with rating and percentile
    score = assess_aptitude("claude-3", "analysis")

See :doc:`/docs/API` for the full public API, or :doc:`/docs/ARCHITECTURE`
for the package internals.
"""

from breed_registry.matcher import (
    select_breed,
    compare_breeds,
    assess_aptitude,
    list_breeds,
    get_breed,
)
from breed_registry.models import (
    ModelAssessment,
    ComparisonReport,
    AptitudeScore,
)

__version__ = "1.0.3"

__all__ = [
    # Functions
    "select_breed",
    "compare_breeds",
    "assess_aptitude",
    "list_breeds",
    "get_breed",
    # Data classes
    "ModelAssessment",
    "ComparisonReport",
    "AptitudeScore",
]