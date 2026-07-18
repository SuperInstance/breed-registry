"""
Data models for the Breed Registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AptitudeScore:
    """A model's aptitude score for a specific task."""

    model: str
    task: str
    score: int  # 0-10
    rating: str  # human-readable rating
    percentile: Optional[float] = None  # percentile among all assessed models

    def __repr__(self) -> str:
        return f"AptitudeScore(model={self.model!r}, task={self.task!r}, score={self.score}/10, rating={self.rating!r})"


@dataclass
class ComparisonReport:
    """Head-to-head comparison between two models."""

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
    """Full breed assessment for a model."""

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
        return cls(
            name=data["name"],
            lineage=data["lineage"],
            breed_group=data["breed_group"],
            temperament=data["temperament"],
            working_aptitude=data["working_aptitude"],
            cost_profile=data["cost_profile"],
            speed_profile=data["speed_profile"],
            trainability=data["trainability"],
            recommended_for=data["recommended_for"],
            not_recommended_for=data["not_recommended_for"],
            fence_compatibility=data["fence_compatibility"],
            notes=data.get("notes"),
        )

    def aptitude_for(self, task: str) -> int:
        """Return the aptitude score (0-10) for a given task."""
        return self.working_aptitude.get(task, 0)

    def overall_score(self) -> float:
        """Average aptitude across all assessed tasks."""
        scores = list(self.working_aptitude.values())
        return sum(scores) / len(scores) if scores else 0.0
