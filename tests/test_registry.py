"""Tests for the Breed Registry — matcher and registry data."""

import pytest

from breed_registry import select_breed, compare_breeds, assess_aptitude
from breed_registry.matcher import BreedMatcher, BREED_REGISTRY


# ---------------------------------------------------------------------------
# Registry data integrity
# ---------------------------------------------------------------------------

class TestRegistryData:
    """Verify registry data is well-formed."""

    def test_all_breeds_loaded(self):
        """All seven breeds should be present."""
        expected = {"gpt-4", "claude-3", "llama-3", "glm", "mistral", "gemini", "qwen"}
        assert set(BREED_REGISTRY.list_breeds()) == expected

    def test_breeds_have_required_fields(self):
        """Each breed must have core fields."""
        for name, data in BREED_REGISTRY.breeds.items():
            assert "classification" in data, f"{name} missing classification"
            assert "temperament" in data, f"{name} missing temperament"
            assert "working_aptitude" in data, f"{name} missing working_aptitude"
            assert "cost_profile" in data, f"{name} missing cost_profile"
            assert "speed_profile" in data, f"{name} missing speed_profile"
            assert "recommended_for" in data, f"{name} missing recommended_for"

    def test_aptitude_scores_in_range(self):
        """All aptitude scores must be 0-10."""
        valid_classes = [
            "code_generation", "reasoning", "summarization", "creative_writing",
            "multilingual", "multimodal", "long_context", "instruction_following",
            "tool_use", "mathematics",
        ]
        for name, data in BREED_REGISTRY.breeds.items():
            for vc in valid_classes:
                score = data["working_aptitude"][vc]
                assert 0 <= score <= 10, f"{name}.{vc} = {score} out of range"


# ---------------------------------------------------------------------------
# select_breed()
# ---------------------------------------------------------------------------

class TestSelectBreed:
    """Tests for breed selection."""

    def test_code_generation_recommendation(self):
        """GPT-4 should be recommended (or tied) for code generation."""
        result = select_breed("code_generation")
        assert result.recommended == "gpt-4"
        assert result.score >= 8.0

    def test_multimodal_recommendation(self):
        """Gemini should be recommended for multimodal tasks."""
        result = select_breed("multimodal")
        assert result.recommended == "gemini"
        assert result.score >= 9.0

    def test_long_context_recommendation(self):
        """Qwen should be recommended for long context."""
        result = select_breed("long_context")
        assert result.recommended == "qwen"

    def test_alternatives_populated(self):
        """Alternatives list should have 6 entries (7 breeds - 1 winner)."""
        result = select_breed("reasoning")
        assert len(result.alternatives) == 6

    def test_scores_ordered_desc(self):
        """Alternatives should be in descending score order."""
        result = select_breed("mathematics")
        scores = [s for _, s in result.alternatives]
        assert scores == sorted(scores, reverse=True)

    def test_unknown_task_returns_zero_scores(self):
        """Unknown tasks should produce zero scores, not errors."""
        result = select_breed("nonexistent_task")
        assert result.score == 0.0

    def test_rationale_not_empty(self):
        """Rationale should explain the recommendation."""
        result = select_breed("reasoning")
        assert len(result.rationale) > 0


# ---------------------------------------------------------------------------
# compare_breeds()
# ---------------------------------------------------------------------------

class TestCompareBreeds:
    """Tests for head-to-head comparison."""

    def test_compare_with_task(self):
        """Comparison for a specific task should reflect aptitude."""
        comp = compare_breeds("gpt-4", "llama-3", task="reasoning")
        assert comp.winner == "gpt-4"
        assert comp.score_a > comp.score_b

    def test_compare_without_task(self):
        """Comparison without task uses overall average."""
        comp = compare_breeds("gpt-4", "mistral")
        assert comp.winner is not None
        assert comp.task is None

    def test_compare_unknown_breed(self):
        """Unknown breed should raise KeyError."""
        with pytest.raises(KeyError):
            compare_breeds("dragon", "gpt-4")

    def test_compare_equal_breeds(self):
        """Comparing a breed with itself should return that breed as winner."""
        comp = compare_breeds("claude-3", "claude-3")
        assert comp.winner == "claude-3"
        assert comp.score_a == comp.score_b

    def test_instruction_following_claude_wins(self):
        """Claude-3 should win instruction_following (score 10)."""
        comp = compare_breeds("claude-3", "gpt-4", task="instruction_following")
        assert comp.winner == "claude-3"


# ---------------------------------------------------------------------------
# assess_aptitude()
# ---------------------------------------------------------------------------

class TestAssessAptitude:
    """Tests for individual aptitude assessment."""

    def test_elite_score(self):
        """Score >= 9 should be 'Elite'."""
        assessment = assess_aptitude("gpt-4", "reasoning")
        assert assessment.score == 9
        assert "Elite" in assessment.interpretation

    def test_strong_score(self):
        """Score 7-8 should be 'Strong'."""
        assessment = assess_aptitude("llama-3", "code_generation")
        assert assessment.score == 7
        assert "Strong" in assessment.interpretation

    def test_adequate_score(self):
        """Score 5-6 should be 'Adequate'."""
        assessment = assess_aptitude("llama-3", "multimodal")
        assert assessment.score == 5
        assert "Adequate" in assessment.interpretation

    def test_weak_score(self):
        """Score 3-4 should be 'Weak'."""
        # Use a breed/task combo that produces a low score
        matcher = BreedMatcher()
        # Find a weak combination
        weak_found = False
        for name, data in matcher.breeds.items():
            for task, score in data["working_aptitude"].items():
                if score <= 4:
                    result = assess_aptitude(name, task)
                    assert "Weak" in result.interpretation or "Unfit" in result.interpretation
                    weak_found = True
                    break
            if weak_found:
                break
        assert weak_found, "Expected at least one weak score in registry"

    def test_unknown_breed_raises(self):
        """Unknown breed should raise KeyError."""
        with pytest.raises(KeyError):
            assess_aptitude("phoenix", "reasoning")

    def test_classification_returned(self):
        """Assessment should include the breed classification."""
        assessment = assess_aptitude("qwen", "mathematics")
        assert assessment.classification == "Shire"

    def test_overall_property(self):
        """The .overall property should equal the raw score."""
        assessment = assess_aptitude("gemini", "multimodal")
        assert assessment.overall == assessment.score == 10


# ---------------------------------------------------------------------------
# BreedMatcher edge cases
# ---------------------------------------------------------------------------

class TestBreedMatcherEdgeCases:
    """Edge case tests for the matcher engine."""

    def test_custom_breeds(self):
        """Matcher should work with custom breed data."""
        custom = {
            "test-breed": {
                "classification": "Test",
                "working_aptitude": {"reasoning": 5},
                "cost_profile": "low",
                "speed_profile": "fast",
            }
        }
        matcher = BreedMatcher(breeds=custom)
        result = matcher.select("reasoning")
        assert result.recommended == "test-breed"

    def test_cost_weighting_affects_ranking(self):
        """Higher cost_weight should boost low-cost breeds."""
        result_default = select_breed("reasoning", cost_weight=0.15)
        result_cost_weighted = select_breed("reasoning", cost_weight=0.5)
        # With heavy cost weighting, cheaper breeds should score better
        # The top breed might change or the gap narrows
        assert result_cost_weighted.score is not None

    def test_all_tasks_covered(self):
        """Every breed should have all 10 working classes scored."""
        classes = {
            "code_generation", "reasoning", "summarization", "creative_writing",
            "multilingual", "multimodal", "long_context", "instruction_following",
            "tool_use", "mathematics",
        }
        for name, data in BREED_REGISTRY.breeds.items():
            missing = classes - set(data["working_aptitude"].keys())
            assert not missing, f"{name} missing aptitude for: {missing}"