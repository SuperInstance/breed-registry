"""
Tests for the Breed Registry matcher.
"""

import pytest

from breed_registry import (
    select_breed,
    compare_breeds,
    assess_aptitude,
    list_breeds,
    get_breed,
)
from breed_registry.models import AptitudeScore, ComparisonReport, ModelAssessment


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestListBreeds:
    def test_returns_all_registered_breeds(self):
        breeds = list_breeds()
        assert "gpt-4" in breeds
        assert "claude-3" in breeds
        assert "llama-3" in breeds
        assert "glm" in breeds
        assert "mistral" in breeds

    def test_returns_sorted(self):
        breeds = list_breeds()
        assert breeds == sorted(breeds)


class TestGetBreed:
    def test_returns_assessment(self):
        assessment = get_breed("gpt-4")
        assert assessment.name == "gpt-4"
        assert assessment.breed_group == "General Purpose"
        assert "code_generation" in assessment.working_aptitude

    def test_raises_for_unknown_breed(self):
        with pytest.raises(KeyError, match="not registered"):
            get_breed("nonexistent-model")

    def test_assessment_has_all_fields(self):
        assessment = get_breed("claude-3")
        assert assessment.lineage
        assert assessment.temperament
        assert assessment.cost_profile
        assert assessment.speed_profile
        assert assessment.trainability
        assert assessment.recommended_for
        assert assessment.not_recommended_for
        assert assessment.fence_compatibility


# ---------------------------------------------------------------------------
# select_breed tests
# ---------------------------------------------------------------------------

class TestSelectBreed:
    def test_returns_recommendations(self):
        recommendations = select_breed("code_generation")
        assert len(recommendations) > 0
        assert all(isinstance(r, ModelAssessment) for r in recommendations)

    def test_sorted_by_aptitude(self):
        recommendations = select_breed("analysis", top_k=5)
        scores = [r.aptitude_for("analysis") for r in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_respects_top_k(self):
        recommendations = select_breed("code_generation", top_k=2)
        assert len(recommendations) <= 2

    def test_gpt4_top_for_code_generation(self):
        recommendations = select_breed("code_generation", top_k=1)
        assert recommendations[0].name == "gpt-4"

    def test_claude3_top_for_analysis(self):
        recommendations = select_breed("analysis", top_k=1)
        assert recommendations[0].name == "claude-3"

    def test_cost_filter_free(self):
        recommendations = select_breed("code_generation", max_cost="free")
        for r in recommendations:
            assert r.cost_profile == "free"

    def test_cost_filter_low(self):
        recommendations = select_breed("code_generation", max_cost="low")
        for r in recommendations:
            assert r.cost_profile in ("free", "low")

    def test_unknown_task_returns_empty(self):
        recommendations = select_breed("nonexistent_task")
        assert len(recommendations) == 0


# ---------------------------------------------------------------------------
# compare_breeds tests
# ---------------------------------------------------------------------------

class TestCompareBreeds:
    def test_returns_comparison_report(self):
        report = compare_breeds("gpt-4", "llama-3")
        assert isinstance(report, ComparisonReport)
        assert report.model_a == "gpt-4"
        assert report.model_b == "llama-3"

    def test_comparison_has_all_tasks(self):
        report = compare_breeds("gpt-4", "claude-3")
        breed_a = get_breed("gpt-4")
        breed_b = get_breed("claude-3")
        all_tasks = set(breed_a.working_aptitude.keys()) | set(breed_b.working_aptitude.keys())
        assert set(report.aptitude_comparison.keys()) == all_tasks

    def test_winner_is_determined(self):
        report = compare_breeds("gpt-4", "llama-3")
        assert report.winner in ("gpt-4", "llama-3", "tie")
        assert report.margin >= 0

    def test_gpt4_vs_llama3_gpt4_wins(self):
        report = compare_breeds("gpt-4", "llama-3")
        assert report.winner == "gpt-4"

    def test_advantages_populated(self):
        report = compare_breeds("gpt-4", "llama-3")
        # GPT-4 should have advantages in at least some tasks
        assert len(report.advantages_a) > 0 or len(report.advantages_b) > 0

    def test_summary_method_works(self):
        report = compare_breeds("gpt-4", "claude-3")
        summary = report.summary()
        assert "gpt-4" in summary
        assert "claude-3" in summary
        assert "winner" in summary.lower()

    def test_raises_for_unknown_model(self):
        with pytest.raises(KeyError):
            compare_breeds("gpt-4", "nonexistent")


# ---------------------------------------------------------------------------
# assess_aptitude tests
# ---------------------------------------------------------------------------

class TestAssessAptitude:
    def test_returns_aptitude_score(self):
        score = assess_aptitude("mistral", "analysis")
        assert isinstance(score, AptitudeScore)
        assert score.model == "mistral"
        assert score.task == "analysis"
        assert 0 <= score.score <= 10

    def test_rating_matches_score(self):
        score = assess_aptitude("gpt-4", "code_generation")
        assert score.score == 9
        assert score.rating == "excellent"

    def test_percentile_calculated(self):
        score = assess_aptitude("gpt-4", "code_generation")
        assert score.percentile is not None
        assert 0.0 <= score.percentile <= 100.0

    def test_claude3_perfect_analysis(self):
        score = assess_aptitude("claude-3", "analysis")
        assert score.score == 10

    def test_raises_for_unknown_model(self):
        with pytest.raises(KeyError):
            assess_aptitude("nonexistent", "code_generation")


# ---------------------------------------------------------------------------
# ModelAssessment unit tests
# ---------------------------------------------------------------------------

class TestModelAssessment:
    def test_overall_score(self):
        assessment = get_breed("gpt-4")
        overall = assessment.overall_score()
        assert overall > 0
        assert overall <= 10

    def test_aptitude_for_known_task(self):
        assessment = get_breed("gpt-4")
        assert assessment.aptitude_for("code_generation") == 9

    def test_aptitude_for_unknown_task(self):
        assessment = get_breed("gpt-4")
        assert assessment.aptitude_for("nonexistent") == 0

    def test_from_dict_roundtrip(self):
        original = get_breed("gpt-4")
        data = {
            "name": original.name,
            "lineage": original.lineage,
            "breed_group": original.breed_group,
            "temperament": original.temperament,
            "working_aptitude": original.working_aptitude,
            "cost_profile": original.cost_profile,
            "speed_profile": original.speed_profile,
            "trainability": original.trainability,
            "recommended_for": original.recommended_for,
            "not_recommended_for": original.not_recommended_for,
            "fence_compatibility": original.fence_compatibility,
            "notes": original.notes,
        }
        rebuilt = ModelAssessment.from_dict(data)
        assert rebuilt.name == original.name
        assert rebuilt.overall_score() == original.overall_score()
