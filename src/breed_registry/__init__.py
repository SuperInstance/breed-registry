"""
The Breed Registry — model selection as breeding selection.

Maps tasks to recommended base models using working animal breeding metaphors.
"""

from .matcher import (
    BreedMatcher,
    BreedComparison,
    AptitudeAssessment,
    BreedRecommendation,
    BREED_REGISTRY,
)

__version__ = "0.1.0"

__all__ = [
    "select_breed",
    "compare_breeds",
    "assess_aptitude",
    "BreedMatcher",
    "BreedComparison",
    "AptitudeAssessment",
    "BreedRecommendation",
    "BREED_REGISTRY",
]

# Module-level singleton matcher
_matcher = BreedMatcher()


def select_breed(task: str, **kwargs) -> "BreedRecommendation":
    """Select the best breed (model) for a given working class (task).

    Args:
        task: The working class identifier (e.g. "code_generation").
        **kwargs: Additional weighting overrides (cost_weight, speed_weight).

    Returns:
        BreedRecommendation with the top breed and ranked alternatives.

    Examples:
        >>> result = select_breed("code_generation")
        >>> result.recommended
        'gpt-4'
    """
    return _matcher.select(task, **kwargs)


def compare_breeds(a: str, b: str, task: str | None = None) -> "BreedComparison":
    """Compare two breeds head-to-head, optionally for a specific task.

    Args:
        a: First breed name.
        b: Second breed name.
        task: Optional working class to weight the comparison.

    Returns:
        BreedComparison with scores and winner.

    Examples:
        >>> comp = compare_breeds("gpt-4", "claude-3")
        >>> comp.winner
        'gpt-4'
    """
    return _matcher.compare(a, b, task=task)


def assess_aptitude(model: str, task: str) -> "AptitudeAssessment":
    """Assess a specific model's aptitude for a specific task.

    Args:
        model: Breed name (e.g. "llama-3").
        task: Working class (e.g. "summarization").

    Returns:
        AptitudeAssessment with scores and interpretation.

    Examples:
        >>> score = assess_aptitude("llama-3", "summarization")
        >>> score.overall
        7
    """
    return _matcher.assess(model, task)