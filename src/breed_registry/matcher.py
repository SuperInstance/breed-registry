"""
Task-to-model matching engine for The Breed Registry.

Core concept: Different models are like different dog breeds.
You would not use a Greyhound to herd sheep, and you would not
use a Border Collie for a sprint race. Match the breed to the task.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

_REGISTRY_DIR = Path(__file__).resolve().parent.parent.parent / "registry"

# Fallback: bundled data if registry dir not found (e.g. installed via pip)
if not _REGISTRY_DIR.exists():
    _REGISTRY_DIR = Path(os.environ.get("BREED_REGISTRY_PATH", _REGISTRY_DIR))


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_registry() -> dict[str, dict[str, Any]]:
    """Load all breed assessments from the registry directory."""
    models_dir = _REGISTRY_DIR / "models"
    breeds: dict[str, dict[str, Any]] = {}
    if models_dir.exists():
        for p in sorted(models_dir.glob("*.json")):
            data = _load_json(p)
            breeds[data["model"]] = data
    return breeds


BREED_REGISTRY: dict[str, dict[str, Any]] = _load_registry()


# ---------------------------------------------------------------------------
# Task taxonomy — maps natural-language task descriptions to scoring keys
# ---------------------------------------------------------------------------

TASK_KEYWORDS: dict[str, list[str]] = {
    "code_generation": [
        r"\bcode\b", r"\bprogram", r"\bfunction\b", r"\bclass\b",
        r"\bdebug\b", r"\bimplement\b", r"\brefactor\b", r"\bapi\b",
        r"\bscript\b", r"\bpull request\b", r"\balgorithm\b",
    ],
    "reasoning": [
        r"\breason", r"\banalyz", r"\blogic\b", r"\bdeduce\b",
        r"\binfer\b", r"\bwhy\b", r"\bcause\b", r"\bstrategy\b",
        r"\bdecide\b", r"\bevaluat",
    ],
    "creative_writing": [
        r"\bcreative\b", r"\bstory\b", r"\bpoem\b", r"\bscreenplay\b",
        r"\bnarrative\b", r"\bfiction\b", r"\bessay\b", r"\bsong\b",
        r"\bmarketing copy\b", r"\bbrand voice\b",
    ],
    "summarization": [
        r"\bsummar", r"\btl;?dr\b", r"\bdigest\b", r"\bcondense\b",
        r"\babstract\b", r"\bbrief\b", r"\bkey points\b",
        r"\blegal contract\b", r"\bdocument\b",
    ],
    "math": [
        r"\bmath\b", r"\bcalcul", r"\bequation\b", r"\balgebra\b",
        r"\bgeometr", r"\bstatistic", r"\bprobabilit", r"\barithmet",
        r"\btheorem\b", r"\bproof\b",
    ],
    "multilingual": [
        r"\btranslat", r"\bmultilingual\b", r"\bchinese\b", r"\bjapanese\b",
        r"\bfrench\b", r"\bgerman\b", r"\bspanish\b", r"\bkorean\b",
        r"\barabic\b", r"\blanguage\b",
    ],
    "instruction_following": [
        r"\binstruct", r"\bstep.by.step\b", r"\bfollow directions\b",
        r"\bformat\b", r"\brules\b", r"\btemplate\b", r"\bchecklist\b",
    ],
    "long_context": [
        r"\blong\b", r"\blarge document\b", r"\bbook\b", r"\bhuge\b",
        r"\bentire\b", r"\bthousand", r"\bcontext window\b",
        r"\bresearch paper\b", r"\bfull text\b",
    ],
}

# Cost sensitivity weight: when the user mentions cost/speed, we adjust.
COST_KEYWORDS = [r"\bcheap\b", r"\bbudget\b", r"\bcost\b", r"\bafford",
                 r"\bfree\b", r"\binexpensive\b", r"\bfrugal\b"]
SPEED_KEYWORDS = [r"\bfast\b", r"\bquick\b", r"\breal.time\b", r"\blow latenc",
                  r"\binstant\b", r"\bspeed\b", r"\brapid\b"]


def _classify_task(task_description: str) -> dict[str, float]:
    """
    Convert a natural-language task description into a weighted profile
    of aptitude categories.

    Returns a dict like {"code_generation": 1.0, "reasoning": 0.5, ...}
    """
    text = task_description.lower()
    profile: dict[str, float] = {}

    for category, patterns in TASK_KEYWORDS.items():
        weight = 0.0
        for pat in patterns:
            if re.search(pat, text):
                weight += 1.0
        if weight > 0:
            profile[category] = min(weight, 3.0)  # cap

    # Fallback: if nothing matched, default to general/reasoning
    if not profile:
        profile["reasoning"] = 1.0
        profile["summarization"] = 0.5

    # Normalise
    total = sum(profile.values())
    if total > 0:
        profile = {k: v / total for k, v in profile.items()}

    return profile


def _score_model(
    model_data: dict[str, Any],
    task_profile: dict[str, float],
) -> float:
    """Compute a weighted aptitude score for a model against a task profile."""
    aptitude = model_data.get("working_aptitude", {})
    score = 0.0
    for category, weight in task_profile.items():
        score += aptitude.get(category, 5.0) * weight
    return round(score, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class BreedMatcher:
    """
    The breeding selection officer.

    Usage::

        matcher = BreedMatcher()
        best = matcher.select("write a Python web scraper")
        print(best["model"])
    """

    def __init__(self, registry: dict[str, dict[str, Any]] | None = None) -> None:
        self.registry = registry or BREED_REGISTRY

    def select(
        self,
        task_description: str,
        *,
        cost_sensitive: bool = False,
        speed_sensitive: bool = False,
        open_weight_only: bool = False,
    ) -> dict[str, Any]:
        """
        Select the best breed (model) for a given task.

        Args:
            task_description: Natural-language description of the task.
            cost_sensitive: Boost cheaper models in scoring.
            speed_sensitive: Boost faster models in scoring.
            open_weight_only: Restrict to open-weight models only.

        Returns:
            Dict with model name, score, dog_breed, and recommendation.
        """
        if not self.registry:
            raise RuntimeError("Breed registry is empty — no models loaded.")

        # Detect cost/speed sensitivity from text if not explicitly set
        text = task_description.lower()
        if not cost_sensitive:
            cost_sensitive = any(re.search(k, text) for k in COST_KEYWORDS)
        if not speed_sensitive:
            speed_sensitive = any(re.search(k, text) for k in SPEED_KEYWORDS)

        task_profile = _classify_task(task_description)

        scored: list[dict[str, Any]] = []
        for model_name, data in self.registry.items():
            # Filter open-weight if requested
            if open_weight_only:
                index_data = _load_json(
                    _REGISTRY_DIR / "index.json"
                ) if (_REGISTRY_DIR / "index.json").exists() else {}
                breeds_index = index_data.get("breeds", {})
                model_index = breeds_index.get(model_name, {})
                if not model_index.get("open_weight", False):
                    continue

            base_score = _score_model(data, task_profile)

            # Cost adjustment
            if cost_sensitive:
                cost_tier = data.get("cost", {}).get("tier", "moderate")
                cost_bonus = {
                    "very cheap": 2.0,
                    "cheap": 1.5,
                    "free (self-hosted)": 2.5,
                    "moderate": 0.0,
                    "expensive": -2.0,
                }.get(cost_tier, 0.0)
                base_score += cost_bonus

            # Speed adjustment
            if speed_sensitive:
                latency = data.get("speed", {}).get("latency_tier", "moderate")
                speed_bonus = {
                    "very fast": 2.0,
                    "fast": 1.0,
                    "moderate": 0.0,
                    "depends on hardware": 0.0,
                }.get(latency, 0.0)
                base_score += speed_bonus

            scored.append({
                "model": model_name,
                "dog_breed": data.get("dog_breed", "Unknown"),
                "score": round(base_score, 2),
                "recommended_for": data.get("recommended_for", []),
                "tagline": data.get("tagline", ""),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[0] if scored else {}

    def compare(self, model_a: str, model_b: str) -> dict[str, Any]:
        """
        Compare two breeds head-to-head across all working aptitude categories.

        Returns a dict with per-category scores and an overall winner.
        """
        a = self.registry.get(model_a)
        b = self.registry.get(model_b)
        if not a:
            raise KeyError(f"Model {model_a} not found in registry.")
        if not b:
            raise KeyError(f"Model {model_b} not found in registry.")

        apt_a = a.get("working_aptitude", {})
        apt_b = b.get("working_aptitude", {})

        categories = sorted(set(apt_a) | set(apt_b))
        a_wins = 0
        b_wins = 0
        breakdown: list[dict[str, Any]] = []

        for cat in categories:
            sa = apt_a.get(cat, 5.0)
            sb = apt_b.get(cat, 5.0)
            winner = "tie"
            if sa > sb:
                a_wins += 1
                winner = model_a
            elif sb > sa:
                b_wins += 1
                winner = model_b
            breakdown.append({
                "category": cat,
                model_a: sa,
                model_b: sb,
                "winner": winner,
            })

        overall_winner = (
            model_a if a_wins > b_wins
            else model_b if b_wins > a_wins
            else "tie"
        )

        return {
            "model_a": model_a,
            "model_b": model_b,
            "dog_breed_a": a.get("dog_breed", "?"),
            "dog_breed_b": b.get("dog_breed", "?"),
            "breakdown": breakdown,
            "score_a": a_wins,
            "score_b": b_wins,
            "winner": overall_winner,
        }

    def assess(self, model: str, task: str) -> dict[str, Any]:
        """
        Assess a specific models