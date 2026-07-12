"""
Tests for The Breed Registry matching engine.
"""

import json
from pathlib import Path

import pytest

from breed_registry.matcher import (
    BREED_REGISTRY,
    BreedMatcher,
    _classify_task,
    assess_aptitude,
    compare_breeds,
    select_breed,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_REGISTRY = {
    "gpt-4": {
        "model": "gpt-4",
        "dog_breed": "Border Collie",
        "temperament": {"intelligence": 10},
        "working_aptitude": {
            "code_generation": 9.5,
            "reasoning": 9.5,
            "creative_writing": 8.0,
            "summarization": 8.5,
            "math": 9.0,
            "multilingual": 7.0,
            "instruction_following": 9.0,
            "long_context": 7.5,
        },
        "cost": {"input_per_1k_tokens": 0.03, "output_per_1k_tokens": 0.06, "tier": "expensive"},
        "speed": {"latency_tier": "moderate"},
        "recommended_for": ["complex reasoning"],
        "tagline": "elite",
    },
    "glm": {
        "model": "glm",
        "dog_breed": "Jack Russell Terrier",
        "temperament": {"intelligence": 7},
        "working_aptitude": {
            "code_generation": 7.0,
            "reasoning": 7.0,
            "creative_writing": 6.5,
            "summarization": 7.0,
            "math": 7.5,
            "multilingual": 8.0,
            "instruction_following": 7.0,
            "long_context": 6.5,
        },
        "cost": {"input_per_1k_tokens": 0.0005, "output_per_1k_tokens": 0.001, "tier": "very cheap"},
        "speed": {"latency_tier": "very fast"},
        "recommended_for": ["high-volume tasks"],
        "tagline": "feisty",
    },
}


@pytest.fixture
def matcher() -> BreedMatcher:
    return BreedMatcher(registry=SAMPLE_REGISTRY)


# ---------------------------------------------------------------------------
# Task classification
# ---------------------------------------------------------------------------

class TestClassifyTask:
    def test_code_task(self):
        profile = _classify_task("write a Python function to sort a list")
        assert "code_generation" in profile
        assert profile["code_generation"] > 0

    def test_math_task(self):
        profile = _classify_task("calculate the factorial of 10")
        assert "math" in profile

    def test_summarization_task(self):
        profile = _classify_task("summarize this legal contract")
        assert "summarization" in profile

    def test_default_fallback(self):
        profile = _classify_task("hello world")
        assert "reasoning" in profile

    def test_weights_normalized(self):
        profile = _classify_task("debug code and write tests")
        total = sum(profile.values())
        assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# select_breed
# ---------------------------------------------------------------------------

class TestSelectBreed:
    def test_selects_best_for_code(self, matcher):
        result = matcher.select("implement a REST API endpoint")
        assert result["model"] == "gpt-4"

    def test_cost_sensitive_boosts_cheap(self, matcher):
        expensive = matcher.select("write code", cost_sensitive=False)
        cheap = matcher.select("write code", cost_sensitive=True)
        # With cost sensitivity, the cheaper model should get a boost
        assert cheap["model"] == "glm"

    def test_speed_sensitive_boosts_fast(self, matcher):
        result = matcher.select("classify this text", speed_sensitive=True)
        assert result["model"] == "glm"

    def test_returns_required_fields(self, matcher):
        result = matcher.select("write a poem")
        assert "model" in result
        assert "dog_breed" in result
        assert "score" in result
        assert "recommended_for" in result

    def test_empty_registry_raises(self):
        empty_matcher = BreedMatcher(registry={})
        with pytest.raises(RuntimeError, match="empty"):
            empty_matcher.select("anything")


# ---------------------------------------------------------------------------
# compare_breeds
# ---------------------------------------------------------------------------

class TestCompareBreeds:
    def test_gpt4_beats_glm_overall(self, matcher):
        result = matcher.compare("gpt-4", "glm")
        assert result["winner"] == "gpt-4"
        assert result["score_a"] >= result["score_b"]

    def test_breakdown_has_all_categories(self, matcher):
        result = matcher.compare("gpt-4", "glm")
        categories = [b["category"] for b in result["breakdown"]]
        assert "code_generation" in categories
        assert "reasoning" in categories
        assert "math" in categories

    def test_unknown_model_raises(self, matcher):
        with pytest.raises(KeyError):
            matcher.compare("gpt-4", "nonexistent")


# ---------------------------------------------------------------------------
# assess_aptitude
# ---------------------------------------------------------------------------

class TestAssessAptitude:
    def test_returns_score(self, matcher):
        result = matcher.assess("gpt-4", "write a sorting algorithm")
        assert "working_aptitude" in result
        assert isinstance(result["working_aptitude"], float)
        assert 0 <= result["working_aptitude"] <= 10

    def test_recommended_flag(self, matcher):
        result = matcher.assess("gpt-4", "complex reasoning and code generation")
        assert result["recommended"] is True

    def test_returns_temperament(self, matcher):
        result = matcher.assess("glm", "translate to Chinese")
        assert "temperament" in result
        assert result["temperament"]["intelligence"] == 7

    def test_unknown_model_raises(self, matcher):
        with pytest.raises(KeyError):
            matcher.assess("nonexistent", "anything")


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

class TestModuleFunctions:
    def test_select_breed_function(self):
        result = select_breed("write code")
        assert "model" in result

    def test_compare_breeds_function(self):
        result = compare_breeds("gpt-4", "claude-3")
        assert "winner" in result

    def test_assess_aptitude_function(self):
        result = assess_aptitude("gpt-4", "math calculation")
        assert "working_aptitude" in result
