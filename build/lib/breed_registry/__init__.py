"""
The Breed Registry — model selection as breeding selection.

In the working dog paradigm, choosing the right breed is the most important
decision. This library provides structured guidance on which base model to
use for which task.

Usage:
    from breed_registry import select_breed, compare_breeds, assess_aptitude

    # Find the best breed for a task
    recommendations = select_breed("code_generation")

    # Compare two breeds head-to-head
    report = compare_breeds("gpt-4", "llama-3")

    # Check a specific model's aptitude for a task
    score = assess_aptitude("mistral", "analysis")
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

__version__ = "1.0.0"

__all__ = [
    "select_breed",
    "compare_breeds",
    "assess_aptitude",
    "list_breeds",
    "get_breed",
    "ModelAssessment",
    "ComparisonReport",
    "AptitudeScore",
]
