# Changelog

All notable changes to `breed-registry` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.2 — 2026-07-20

### Fixed
- **Eliminated double `aptitude_for()` call in `assess_aptitude`.** The `assess_aptitude` method was calling `aptitude_for()` twice on the same candidate — once to check viability and again to compute the score. This doubled computation time for aptitude assessments on large registries. Now caches the first result and reuses it.

## v1.0.1 — 2026-07-18

### Fixed
- **Audit fixes from code review.** Score validation now enforces range bounds; input validation added for breeding pair selection; edge cases in cross-registry queries hardened.
- Added 7 regression tests.

## v1.0.0 — 2026-07-18

### Initial Release
- Package: breed-registry — model selection as breeding selection
- Registry management, aptitude assessment, cross-breeding support
- Tests passing
