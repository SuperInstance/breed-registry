"""
Task-to-model matcher — the core selection engine.

Given a task (e.g. "code_generation"), recommends the best model breeds
based on their working aptitude scores.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from breed_registry.models import (
    AptitudeScore,
    ComparisonReport,
    ModelAssessment,
)

# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

_REGISTRY_DIR = Path(__file__).resolve().parent.parent.parent / "registry"


def _load_registry(registry_dir: Optional[Path] = None) -> Dict[str, ModelAssessment]:
    """Load all breed assessments from the registry directory."""
    reg_dir = registry_dir or _REGISTRY_DIR
    assessments: Dict[str, ModelAssessment] = {}

    index_path = reg_dir / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Registry index not found at {index_path}")

    with open(index_path) as f:
        index = json.load(f)

    for key, info in index.get("breeds", {}).items():
        breed_file = reg_dir / info["file"]
        if breed_file.exists():
            with open(breed_file) as f:
                data = json.load(f)
            assessments[key] = ModelAssessment.from_dict(data)
        else:
            warnings.warn(f"Breed file not found for '{key}': {breed_file}", stacklevel=2)

    return assessments


# Lazy-loaded global registry
_REGISTRY_CACHE: Optional[Dict[str, ModelAssessment]] = None


def _get_registry() -> Dict[str, ModelAssessment]:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        _REGISTRY_CACHE = _load_registry()
    return _REGISTRY_CACHE


def _score_to_rating(score: int) -> str:
    """Convert a numeric score (0-10) to a human-readable rating."""
    if score >= 9:
        return "excellent"
    elif score >= 7:
        return "good"
    elif score >= 5:
        return "fair"
    elif score >= 3:
        return "poor"
    else:
        return "unsuitable"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_breeds() -> List[str]:
    """List all registered breed names."""
    return sorted(_get_registry().keys())


def get_breed(name: str) -> ModelAssessment:
    """Get the full assessment for a specific breed.

    Raises:
        KeyError: if the breed is not registered.
    """
    registry = _get_registry()
    if name not in registry:
        raise KeyError(
            f"Breed '{name}' not registered. Available: {', '.join(sorted(registry.keys()))}"
        )
    return registry[name]


def select_breed(
    task: str,
    top_k: int = 3,
    max_cost: Optional[str] = None,
) -> List[ModelAssessment]:
    """Recommend models for a given task, sorted by aptitude.

    Args:
        task: The task category (e.g. "code_generation", "analysis").
        top_k: Maximum number of recommendations to return.
        max_cost: Optional cost ceiling — "low" excludes moderate/high,
                  "free" excludes everything but free models.

    Returns:
        List of ModelAssessment objects, best match first.

    Raises:
        TypeError: If task is not a string, top_k is not an int, or max_cost is not a string/None.
        ValueError: If top_k is not positive, or max_cost is not a valid cost level.
    """
    # Input validation
    if not isinstance(task, str):
        raise TypeError(f"task must be a string, got {type(task).__name__}")
    if not isinstance(top_k, int):
        raise TypeError(f"top_k must be an integer, got {type(top_k).__name__}")
    if top_k < 1:
        raise ValueError(f"top_k must be positive, got {top_k}")
    if max_cost is not None and not isinstance(max_cost, str):
        raise TypeError(f"max_cost must be a string or None, got {type(max_cost).__name__}")

    registry = _get_registry()
    cost_order = {"free": 0, "low": 1, "moderate": 2, "high": 3}

    # Validate max_cost if provided
    if max_cost is not None and max_cost not in cost_order:
        raise ValueError(
            f"max_cost must be one of: {', '.join(cost_order.keys())}, got {max_cost!r}"
        )

    cost_ceiling = cost_order.get(max_cost, 3) if max_cost else 3

    scored: List[Tuple[int, ModelAssessment]] = []
    for assessment in registry.values():
        # Filter by cost ceiling
        model_cost = cost_order.get(assessment.cost_profile, 3)
        if model_cost > cost_ceiling:
            continue

        score = assessment.aptitude_for(task)
        if score > 0:
            scored.append((score, assessment))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [assessment for _, assessment in scored[:top_k]]


def compare_breeds(model_a: str, model_b: str) -> ComparisonReport:
    """Compare two breeds head-to-head across all working aptitude dimensions.

    Raises:
        KeyError: if either model is not registered.
    """
    breed_a = get_breed(model_a)
    breed_b = get_breed(model_b)

    # Build task-by-task comparison
    all_tasks = sorted(
        set(breed_a.working_aptitude.keys()) | set(breed_b.working_aptitude.keys())
    )

    aptitude_comparison: Dict[str, Dict[str, int]] = {}
    advantages_a: List[str] = []
    advantages_b: List[str] = []
    total_a = 0
    total_b = 0

    for task in all_tasks:
        score_a = breed_a.aptitude_for(task)
        score_b = breed_b.aptitude_for(task)
        aptitude_comparison[task] = {model_a: score_a, model_b: score_b}
        total_a += score_a
        total_b += score_b

        if score_a > score_b:
            advantages_a.append(task)
        elif score_b > score_a:
            advantages_b.append(task)

    margin = abs(total_a - total_b)
    if total_a > total_b:
        winner = model_a
    elif total_b > total_a:
        winner = model_b
    else:
        winner = "tie"

    cost_order = {"free": 0, "low": 1, "moderate": 2, "high": 3}
    cost_a = cost_order.get(breed_a.cost_profile, 3)
    cost_b = cost_order.get(breed_b.cost_profile, 3)

    if cost_a < cost_b:
        cost_notes = f"{model_a} is cheaper ({breed_a.cost_profile} vs {breed_b.cost_profile})"
    elif cost_b < cost_a:
        cost_notes = f"{model_b} is cheaper ({breed_b.cost_profile} vs {breed_a.cost_profile})"
    else:
        cost_notes = f"Both are {breed_a.cost_profile} cost"

    speed_order = {"fast": 0, "moderate": 1, "slow": 2}
    speed_a = speed_order.get(breed_a.speed_profile, 2)
    speed_b = speed_order.get(breed_b.speed_profile, 2)

    if speed_a < speed_b:
        speed_notes = f"{model_a} is faster ({breed_a.speed_profile} vs {breed_b.speed_profile})"
    elif speed_b < speed_a:
        speed_notes = f"{model_b} is faster ({breed_b.speed_profile} vs {breed_a.speed_profile})"
    else:
        speed_notes = f"Both are {breed_a.speed_profile} speed"

    return ComparisonReport(
        model_a=model_a,
        model_b=model_b,
        aptitude_comparison=aptitude_comparison,
        winner=winner,
        margin=margin,
        advantages_a=advantages_a,
        advantages_b=advantages_b,
        cost_notes=cost_notes,
        speed_notes=speed_notes,
    )


def assess_aptitude(model: str, task: str) -> AptitudeScore:
    """Assess a specific model's aptitude for a specific task.

    Raises:
        KeyError: if the model is not registered.
    """
    breed = get_breed(model)
    score = breed.aptitude_for(task)

    # Calculate percentile
    registry = _get_registry()
    all_scores = []
    for a in registry.values():
        score = a.aptitude_for(task)
        if score > 0:
            all_scores.append(score)
    if all_scores:
        below = sum(1 for s in all_scores if s < score)
        percentile = round((below / len(all_scores)) * 100, 1)
    else:
        percentile = None

    return AptitudeScore(
        model=model,
        task=task,
        score=score,
        rating=_score_to_rating(score),
        percentile=percentile,
    )
