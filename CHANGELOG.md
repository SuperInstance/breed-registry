# Changelog

All notable changes to `breed-registry` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] — 2026-07-21

### Fixed
- **`assess_aptitude` returned the wrong breed's score.** The inner
  registry-iteration loop shadowed the outer `score` variable, so the
  function effectively returned the *last* iterated model's score for
  the requested task instead of the requested breed's score. Renamed
  the inner variable to `candidate` and the outer to `target_score` to
  eliminate the shadowing. Added regression test
  `test_returns_requested_breed_score_not_iterated_score` to prevent
  recurrence. *Found by documentation audit; the v1.0.2 "fix" only
  restructured the loop without addressing the shadowing.*

### Documentation
- **New `docs/ARCHITECTURE.md`** — package layout, data flow, decision
  logic, extension points, testing strategy, and what the package is not.
- **New `docs/API.md`** — full reference for every public symbol,
  including validation rules, error matrix, and thread-safety notes.
- **New `docs/EXAMPLES.md`** — seven worked examples covering
  registration, querying, comparison, single-task assessment, custom
  filtering, and error handling.
- **New `docs/SCHEMA.md`** — field-by-field reference for the registry
  JSON files and the `ModelAssessment` / `ComparisonReport` /
  `AptitudeScore` dataclasses, with constraint summary and adding-a-task
  instructions.
- **README rewritten** — corrected the breed profile table to match
  the actual schema; removed references to non-existent fields and
  tasks; added a documentation map and a quick-start block.
- **Improved docstrings** in `src/breed_registry/__init__.py`,
  `matcher.py`, and `models.py` — added Attributes sections, Args /
  Returns / Raises blocks, and cross-references to the new docs.

## v1.0.2 — 2026-07-20

### Fixed
- Eliminated double `aptitude_for()` call in `assess_aptitude`. The `assess_aptitude` method was calling `aptitude_for()` twice on the same candidate — once to check viability and again to compute the score. This doubled computation time for aptitude assessments on large registries. Now caches the first result and reuses it.

## v1.0.1 — 2026-07-18

### Fixed
- **Audit fixes from code review.** Score validation now enforces range bounds; input validation added for breeding pair selection; edge cases in cross-registry queries hardened.
- Added 7 regression tests.

## v1.0.0 — 2026-07-18

### Initial Release
- Package: breed-registry — model selection as breeding selection
- Registry management, aptitude assessment, cross-breeding support
- Tests passing