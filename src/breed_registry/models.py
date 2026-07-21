"""Data models for the Breed Registry.

This module defines the three dataclasses returned by the public API:

- :class:`ModelAssessment` — one breed's full profile (loaded from JSON)
- :class:`ComparisonReport` — head-to-head comparison of two breeds
- :class:`AptitudeScore` — single-model × single-task score

All three are immutable from the matcher's perspective: the matcher loads
:class:`ModelAssessment` instances from ``registry/*.json`` and never
mutates them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AptitudeScore:
    """A model's aptitude score for a specific task.

    Returned by :func:`breed_registry.assess_aptitude`. Holds the raw
    0-10 score, a human-readable rating band, and the model's percentile
    rank among registered breeds that have a non-zero score on the same
    task. ``percentile`` is ``None`` when no other breed has been scored
    on the task.

    Attributes:
        model: Breed key as registered in ``registry/index.json``.
        task: Task category (e.g. ``"code_generation"``, ``"analysis"``).
        score: Integer score in the closed interval ``[0, 10]``.
        rating: Human-readable band — ``"excellent"``, ``"good"``,
            ``"fair"``, ``"poor"``, or ``"unsuitable"``.
        percentile: Percentage of scored peers strictly below this score
            on the same task. ``None`` when no peers are scored.
    """

    model: str
    task: str
    score: int  # 0-10
    rating: str  # human-readable rating
    percentile: Optional[float] = None  # percentile among all assessed models

    def __post_init__(self) -> None:
        """Validate that ``score`` is an integer in ``[0, 10]``."""
        if not isinstance(self.score, int):
            raise TypeError(f"Score must be an integer, got {type(self.score).__name__}")
        if not 0 <= self.score <= 10:
            raise ValueError(f"Score must be between 0 and 10, got {self.score}")

    def __repr__(self) -> str:
        return f"AptitudeScore(model={self.model!r}, task={self.task!r}, score={self.score}/10, rating={self.rating!r})"


@dataclass
class ComparisonReport:
    """Head-to-head comparison between two models.

    Returned by :func:`breed_registry.compare_breeds`. Aggregates per-task
    scores for both breeds and decides an overall winner by total score.

    Attributes:
        model_a: Echo of the first breed key passed to ``compare_breeds``.
        model_b: Echo of the second breed key.
        aptitude_comparison: Map of ``task → {model_a: score, model_b: score}``
            covering the union of both breeds' assessed tasks.
        winner: ``"model_a"``, ``"model_b"``, or ``"tie"`` (literal strings).
        margin: Absolute difference of total scores across all tasks.
        advantages_a: Tasks where ``model_a`` strictly outscores ``model_b``.
        advantages_b: Tasks where ``model_b`` strictly outscores ``model_a``.
        cost_notes: One-line cost comparison (which is cheaper, or "both").
        speed_notes: One-line speed comparison (which is faster, or "both").
    """

    model_a: str
    model_b: str
    aptitude_comparison: Dict[str, Dict[str, int]]  # task -> {model_a: score, model_b: score}
    winner: str  # overall winner
    margin: int  # total score difference
    advantages_a: List[str]  # tasks where model_a wins
    advantages_b: List[str]  # tasks where model_b wins
    cost_notes: str
    speed_notes: str

    def summary(self) -> str:
        """Render a multi-line plain-text report.

        Suitable for CLI output, log lines, and quick visual inspection.
        Use the structured fields (``winner``, ``advantages_a``, etc.) for
        programmatic decisions.
        """
        lines = [
            f"Comparison: {self.model_a} vs {self.model_b}",
            f"Overall winner: {self.winner} (margin: {self.margin} points)",
            "",
            f"Advantages {self.model_a}: {', '.join(self.advantages_a) or 'none'}",
            f"Advantages {self.model_b}: {', '.join(self.advantages_b) or 'none'}",
            "",
            f"Cost: {self.cost_notes}",
            f"Speed: {self.speed_notes}",
        ]
        return "\n".join(lines)


@dataclass
class ModelAssessment:
    """Full breed assessment for a model.

    Mirrors the on-disk JSON profile in ``registry/<breed>.json`` 1:1.
    Construct via :meth:`from_dict` to get score validation for free.

    Attributes:
        name: Breed key as registered in ``registry/index.json``.
        lineage: Free-form pedigree blurb.
        breed_group: Coarse group (``"General Purpose"``, ``"Working"``,
            ``"Open Lineage"``, ...).
        temperament: Free-form list of behavioral descriptors.
        working_aptitude: Map of ``task → score (0-10)``.
        cost_profile: One of the ``cost_tiers`` in the registry index.
        speed_profile: One of the ``speed_tiers`` in the registry index.
        trainability: Free-form qualitative description.
        recommended_for: Tasks or scenarios where this breed excels.
        not_recommended_for: Tasks or scenarios where this breed struggles.
        fence_compatibility: How well the model respects conservation
            bytecode. Free-form qualitative description.
        notes: Optional free-form blurb; often leans into the working-dog
            analogy.
    """

    name: str
    lineage: str
    breed_group: str
    temperament: List[str]
    working_aptitude: Dict[str, int]
    cost_profile: str
    speed_profile: str
    trainability: str
    recommended_for: List[str]
    not_recommended_for: List[str]
    fence_compatibility: str
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ModelAssessment":
        """Construct a :class:`ModelAssessment` from a JSON-style dict.

        Validates every score in ``working_aptitude`` is an integer in
        ``[0, 10]``. Raises ``TypeError`` on non-integer scores and
        ``ValueError`` on out-of-range scores.

        Args:
            data: A dict matching the JSON profile schema — see
                :doc:`/docs/SCHEMA` for the full field reference.

        Returns:
            A fully populated :class:`ModelAssessment`.
        """
        working_aptitude = data["working_aptitude"]
        # Validate all aptitude scores are in the 0-10 range
        for task, score in working_aptitude.items():
            if not isinstance(score, int):
                raise TypeError(
                    f"Aptitude score for '{task}' must be an integer, got {type(score).__name__}"
                )
            if not 0 <= score <= 10:
                raise ValueError(
                    f"Aptitude score for '{task}' must be between 0 and 10, got {score}"
                )
        return cls(
            name=data["name"],
            lineage=data["lineage"],
            breed_group=data["breed_group"],
            temperament=data["temperament"],
            working_aptitude=working_aptitude,
            cost_profile=data["cost_profile"],
            speed_profile=data["speed_profile"],
            trainability=data["trainability"],
            recommended_for=data["recommended_for"],
            not_recommended_for=data["not_recommended_for"],
            fence_compatibility=data["fence_compatibility"],
            notes=data.get("notes"),
        )

    def aptitude_for(self, task: str) -> int:
        """Return the aptitude score (0-10) for a given task.

        Returns ``0`` if the breed has no entry for the task — by
        convention "unassessed", not "worst". Callers that need to
        distinguish unassessed from scored-zero should inspect
        ``working_aptitude`` directly.
        """
        return self.working_aptitude.get(task, 0)

    def overall_score(self) -> float:
        """Return the mean of all working-aptitude scores.

        Returns ``0.0`` when the breed has no assessed tasks. Use as a
        coarse general-capability signal; for task-specific ranking,
        use :func:`breed_registry.select_breed`.
        """
        scores = list(self.working_aptitude.values())
        return sum(scores) / len(scores) if scores else 0.0
