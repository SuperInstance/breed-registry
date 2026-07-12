"""
Task-to-model matching engine for the Breed Registry.

Implements breeding-selection logic: each AI model is treated as a working-animal
breed with temperament, aptitude scores, and working-class compatibility.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Registry data — loaded from JSON at import time
# ---------------------------------------------------------------------------

_REGISTRY_DIR = Path(__file__).resolve().parent.parent.parent / "registry"

def _load_json(path: Path) -> dict[str, Any]:
    """Load JSON from a file path."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_breed_registry() -> dict[str, dict[str, Any]]:
    """Load the full breed registry from the bundled JSON files."""
    index_path = _REGISTRY_DIR / "index.json"
    if not index_path.exists():
        return {}

    index = _load_json(index_path)
    breeds: dict[str, dict[str, Any]] = {}

    for entry in index.get("breeds", []):
        breed_path = _REGISTRY_DIR / entry["path"]
        if breed_path.exists():
            data = _load_json(breed_path)
            breeds[entry["name"]] = data

    return breeds


# Fallback inline registry (used when JSON files aren't on disk, e.g. tests)
_FALLBACK_BREEDS: dict[str, dict[str, Any]] = {
    "gpt-4": {
        "name": "gpt-4", "lineage": "OpenAI", "classification": "Thoroughbred",
        "temperament": {"primary": "analytical", "secondary": "cautious"},
        "working_aptitude": {
            "code_generation": 9, "reasoning": 9, "summarization": 8,
            "creative_writing": 8, "multilingual": 7, "multimodal": 8,
            "long_context": 7, "instruction_following": 9, "tool_use": 9,
            "mathematics": 9,
        },
        "cost_profile": "premium", "speed_profile": "moderate",
        "recommended_for": ["complex reasoning", "production code generation"],
        "fence_compatibility": {"json_mode": True, "function_calling": True},
    },
    "claude-3": {
        "name": "claude-3", "lineage": "Anthropic", "classification": "Warmblood",
        "temperament": {"primary": "thoughtful", "secondary": "articulate"},
        "working_aptitude": {
            "code_generation": 8, "reasoning": 9, "summarization": 9,
            "creative_writing": 9, "multilingual": 7, "multimodal": 7,
            "long_context": 9, "instruction_following": 10, "tool_use": 8,
            "mathematics": 7,
        },
        "cost_profile": "premium", "speed_profile": "moderate",
        "recommended_for": ["long document analysis", "creative writing"],
        "fence_compatibility": {"json_mode": False, "function_calling": True},
    },
    "llama-3": {
        "name": "llama-3", "lineage": "Meta", "classification": "Mustang",
        "temperament": {"primary": "rugged", "secondary": "adaptable"},
        "working_aptitude": {
            "code_generation": 7, "reasoning": 7, "summarization": 7,
            "creative_writing": 7, "multilingual": 6, "multimodal": 5,
            "long_context": 6, "instruction_following": 8, "tool_use": 7,
            "mathematics": 6,
        },
        "cost_profile": "low", "speed_profile": "fast",
        "recommended_for": ["local deployment", "cost-sensitive inference"],
        "fence_compatibility": {"json_mode": False, "function_calling": True},
    },
    "glm": {
        "name": "glm", "lineage": "Zhipu AI", "classification": "Arabian",
        "temperament": {"primary": "efficient", "secondary": "versatile"},
        "working_aptitude": {
            "code_generation": 7, "reasoning": 7, "summarization": 7,
            "creative_writing": 7, "multilingual": 9, "multimodal": 6,
            "long_context": 8, "instruction_following": 8, "tool_use": 7,
            "mathematics": 7,
        },
        "cost_profile": "low", "speed_profile": "fast",
        "recommended_for": ["Chinese-English bilingual tasks", "cost-efficient reasoning"],
        "fence_compatibility": {"json_mode": True, "function_calling": True},
    },
    "mistral": {
        "name": "mistral", "lineage": "Mistral AI", "classification": "Andalusian",
        "temperament": {"primary": "agile", "secondary": "refined"},
        "working_aptitude": {
            "code_generation": 8, "reasoning": 7, "summarization": 7,
            "creative_writing": 8, "multilingual": 8, "multimodal": 5,
            "long_context": 6, "instruction_following": 8, "tool_use": 7,
            "mathematics": 7,
        },
        "cost_profile": "moderate", "speed_profile": "fast",
        "recommended_for": ["European language tasks", "efficient code generation"],
        "fence_compatibility": {"json_mode": True, "function_calling": True},
    },
    "gemini": {
        "name": "gemini", "lineage": "Google", "classification": "Hanoverian",
        "temperament": {"primary": "perceptive", "secondary": "multimodal"},
        "working_aptitude": {
            "code_generation": 8, "reasoning": 8, "summarization": 8,
            "creative_writing": 7, "multilingual": 8, "multimodal": 10,
            "long_context": 9, "instruction_following": 8, "tool_use": 8,
            "mathematics": 8,
        },
        "cost_profile": "moderate", "speed_profile": "fast",
        "recommended_for": ["multimodal reasoning", "image understanding"],
        "fence_compatibility": {"json_mode": True, "function_calling": True},
    },
    "qwen": {
        "name": "qwen", "lineage": "Alibaba", "classification": "Shire",
        "temperament": {"primary": "robust", "secondary": "enduring"},
        "working_aptitude": {
            "code_generation": 8, "reasoning": 8, "summarization": 8,
            "creative_writing": 7, "multilingual": 9, "multimodal": 7,
            "long_context": 10, "instruction_following": 8, "tool_use": 8,
            "mathematics": 9,
        },
        "cost_profile": "low", "speed_profile": "moderate",
        "recommended_for": ["ultra-long context processing", "mathematical reasoning"],
        "fence_compatibility": {"json_mode": True, "function_calling": True},
    },
}

# Cost profile multipliers (lower cost = better)
_COST_WEIGHTS: dict[str, float] = {
    "low": 1.0,
    "moderate": 0.7,
    "premium": 0.4,
}

_SPEED_WEIGHTS: dict[str, float] = {
    "fast": 1.0,
    "moderate": 0.7,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AptitudeAssessment:
    """Assessment of a single breed for a single working class."""

    breed: str
    task: str
    score: int
    cost_profile: str
    speed_profile: str
    classification: str
    interpretation: str

    @property
    def overall(self) -> int:
        """Raw aptitude score (0-10)."""
        return self.score

    def __repr__(self) -> str:
        return (
            f"AptitudeAssessment(breed={self.breed!r}, task={self.task!r}, "
            f"score={self.score}/10, {self.interpretation})"
        )


@dataclass
class BreedRecommendation:
    """Recommendation result for a working class."""

    task: str
    recommended: str
    score: float
    alternatives: list[tuple[str, float]] = field(default_factory=list)
    rationale: str = ""

    def __repr__(self) -> str:
        alts = ", ".join(f"{n}({s:.1f})" for n, s in self.alternatives[:3])
        return (
            f"BreedRecommendation(task={self.task!r}, "
            f"recommended={self.recommended!r}, score={self.score:.1f}, "
            f"alternatives=[{alts}])"
        )


@dataclass
class BreedComparison:
    """Head-to-head comparison between two breeds."""

    breed_a: str
    breed_b: str
    score_a: float
    score_b: float
    winner: str
    task: str | None = None
    detail: dict[str, dict[str, int]] = field(default_factory=dict)

    def __repr__(self) -> str:
        task_str = f", task={self.task!r}" if self.task else ""
        return (
            f"BreedComparison({self.breed_a!r}({self.score_a:.1f}) vs "
            f"{self.breed_b!r}({self.score_b:.1f}), "
            f"winner={self.winner!r}{task_str})"
        )


# ---------------------------------------------------------------------------
# Core matcher engine
# ---------------------------------------------------------------------------

class BreedMatcher:
    """Matching engine that maps working classes (tasks) to breeds (models)."""

    def __init__(self, breeds: dict[str, dict[str, Any]] | None = None) -> None:
        self.breeds = breeds or _load_breed_registry() or _FALLBACK_BREEDS

    # -- public API --

    def select(
        self,
        task: str,
        *,
        cost_weight: float = 0.15,
        speed_weight: float = 0.10,
    ) -> BreedRecommendation:
        """Select the best breed for a working class.

        Weights aptitude score by cost and speed profiles to compute
        a composite score. Returns the top breed and ranked alternatives.
        """
        scored: list[tuple[str, float]] = []
        for name, data in self.breeds.items():
            aptitude = data["working_aptitude"].get(task, 0)
            cost_factor = _COST_WEIGHTS.get(data.get("cost_profile", "moderate"), 0.7)
            speed_factor = _SPEED_WEIGHTS.get(data.get("speed_profile", "moderate"), 0.7)
            composite = aptitude * (
                1.0
                + cost_weight * (cost_factor - 0.7) / 0.3
                + speed_weight * (speed_factor - 0.7) / 0.3
            )
            composite = round(max(0.0, min(10.0, composite)), 2)
            scored.append((name, composite))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = scored[0]

        return BreedRecommendation(
            task=task,
            recommended=best_name,
            score=best_score,
            alternatives=scored[1:],
            rationale=f"Highest composite aptitude for '{task}' "
            f"(base={self.breeds[best_name]['working_aptitude'].get(task, 0)}/10)",
        )

    def compare(self, a: str, b: str, task: str | None = None) -> BreedComparison:
        """Compare two breeds head-to-head.

        If *task* is given, compares aptitude for that working class.
        Otherwise, compares overall average aptitude across all classes.
        """
        breed_a = self.breeds.get(a)
        breed_b = self.breeds.get(b)
        if breed_a is None:
            raise KeyError(f"Breed not found: {a!r}")
        if breed_b is None:
            raise KeyError(f"Breed not found: {b!r}")

        if task:
            score_a = float(breed_a["working_aptitude"].get(task, 0))
            score_b = float(breed_b["working_aptitude"].get(task, 0))
            detail = {
                a: {"task_score": int(score_a)},
                b: {"task_score": int(score_b)},
            }
        else:
            avg_a = self._overall_average(breed_a)
            avg_b = self._overall_average(breed_b)
            score_a = round(avg_a, 2)
            score_b = round(avg_b, 2)
            detail = {
                a: {"overall_average": score_a},
                b: {"overall_average": score_b},
            }

        if score_a >= score_b:
            winner = a
        else:
            winner = b

        return BreedComparison(
            breed_a=a,
            breed_b=b,
            score_a=score_a,
            score_b=score_b,
            winner=winner,
            task=task,
            detail=detail,
        )

    def assess(self, model: str, task: str) -> AptitudeAssessment:
        """Assess a single breed for a single working class."""
        breed = self.breeds.get(model)
        if breed is None:
            raise KeyError(f"Breed not found: {model!r}")

        score = breed["working_aptitude"].get(task, 0)
        if score >= 9:
            interpretation = "Elite — top-tier aptitude"
        elif score >= 7:
            interpretation = "Strong — well-suited"
        elif score >= 5:
            interpretation = "Adequate — usable with supervision"
        elif score >= 3:
            interpretation = "Weak — not recommended"
        else:
            interpretation = "Unfit — avoid for this task"

        return AptitudeAssessment(
            breed=model,
            task=task,
            score=score,
            cost_profile=breed.get("cost_profile", "unknown"),
            speed_profile=breed.get("speed_profile", "unknown"),
            classification=breed.get("classification", "unknown"),
            interpretation=interpretation,
        )

    # -- helpers --

    @staticmethod
    def _overall_average(breed: dict[str, Any]) -> float:
        scores = breed["working_aptitude"].values()
        return sum(scores) / len(scores) if scores else 0.0

    def list_breeds(self) -> list[str]:
        """Return all registered breed names."""
        return sorted(self.breeds.keys())


# Module-level singleton
BREED_REGISTRY = BreedMatcher()