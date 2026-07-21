# Schema Reference — Breed Registry

> Field-by-field documentation for the registry JSON files and the `ModelAssessment` dataclass.

---

## Two Layers of Schema

The registry is defined in two layers:

1. **Disk format** — JSON files in `registry/`. Hand-edited by humans, loaded at runtime.
2. **Python shape** — the `ModelAssessment` dataclass, populated via `ModelAssessment.from_dict(data)`.

The two layers mirror each other 1:1. The dataclass validates that scores are integers in `[0, 10]`; the JSON files have no built-in validator, so human authors must enforce that constraint by hand (and the tests in `tests/test_matcher.py` will catch violations at load time).

---

## `registry/index.json` — the manifest

```json
{
  "version": "1.0.0",
  "description": "The Breed Registry — model selection as breeding selection",
  "breeds": {
    "<breed-key>": {
      "file": "<filename>.json",
      "breed_group": "<string>",
      "cost_profile": "<tier>",
      "speed_profile": "<tier>",
      "summary": "<one-line description>"
    }
  },
  "task_categories": ["...", "..."],
  "cost_tiers": ["free", "low", "moderate", "high"],
  "speed_tiers": ["fast", "moderate", "slow"]
}
```

### Top-level fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `version` | string | yes | schema version of the manifest |
| `description` | string | yes | human-readable description |
| `breeds` | object | yes | map of breed-key → entry |
| `task_categories` | string[] | yes | task names that any breed might be scored on |
| `cost_tiers` | string[] | yes | allowed values of `cost_profile` (in increasing cost) |
| `speed_tiers` | string[] | yes | allowed values of `speed_profile` (in increasing latency) |

### `breeds.<key>` entry fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `file` | string | yes | relative path to the breed profile JSON (relative to the manifest) |
| `breed_group` | string | yes | displayed in registry listings |
| `cost_profile` | tier | yes | filterable by `select_breed(max_cost=...)` |
| `speed_profile` | tier | yes | informational; used by `compare_breeds` notes |
| `summary` | string | yes | one-line description shown in tables |

The manifest's breed entries do **not** contain working-aptitude scores; those live in each breed's profile file.

---

## `<breed>.json` — the per-breed profile

```json
{
  "name": "<breed-key>",
  "lineage": "<pedigree blurb>",
  "breed_group": "<group>",
  "temperament": ["...", "..."],
  "working_aptitude": {
    "<task>": <score>,
    "..."
  },
  "cost_profile": "<tier>",
  "speed_profile": "<tier>",
  "trainability": "<qualitative blurb>",
  "recommended_for": ["...", "..."],
  "not_recommended_for": ["...", "..."],
  "fence_compatibility": "<qualitative blurb>",
  "notes": "<optional free-text blurb>"
}
```

### Field-by-field reference

#### `name` (string, required)

The breed's canonical key. Must match the key under which it is registered in `index.json`. Hyphenated lowercase by convention (`gpt-4`, `llama-3`, `mistral`).

#### `lineage` (string, required)

A short pedigree blurb. Free-form text, single sentence is typical. Describes the model family and training approach (e.g. *"LLaMA family (Meta) — open-weights lineage, descendant of LLaMA and LLaMA-2"*).

#### `breed_group` (string, required)

Coarse categorical grouping. Current values in use:

| Value | Meaning |
|---|---|
| `General Purpose` | broad capability, suited for many tasks |
| `Working` | lean, efficient, deployment-oriented |
| `Open Lineage` | open-weights, fine-tune-friendly |

New groups may be added freely; the matcher does not key off them.

#### `temperament` (string[], required)

Free-form list of behavioral descriptors. Examples from the bundled registry: `["careful", "verbose", "thorough"]`, `["efficient", "lean", "European-trained"]`. Used for human-readable descriptions; not interpreted by the matcher.

#### `working_aptitude` (object<task, int>, required)

The heart of the registry. Maps each task name to a score in `[0, 10]` (must be an integer). Every score is **hand-curated** by humans who have used the model — these are practitioner assessments, not benchmark numbers.

| Score band | Interpretation |
|---|---|
| 9–10 | top of the working cohort for this task |
| 7–8 | strong, dependable |
| 5–6 | usable, not best-in-class |
| 3–4 | weak, struggle with this task |
| 0–2 | avoid for this task |
| (key absent) | unassessed — the matcher treats this as 0 and excludes the breed from rankings for this task |

If a task is in `task_categories` in the index but missing from a breed's `working_aptitude`, the breed is "unassessed" on that task — a deliberate signal, not an oversight.

**Validation:** `ModelAssessment.from_dict()` raises `TypeError` if any score is non-int and `ValueError` if any score is outside `[0, 10]`.

#### `cost_profile` (string, required)

One of the values in `cost_tiers` in the index:

| Tier | Meaning |
|---|---|
| `free` | open-weights / self-hosted, no per-token cost |
| `low` | cheap API or small self-hosted models |
| `moderate` | mid-range API cost |
| `high` | premium API cost |

The matcher uses this field to enforce `max_cost` ceilings: `cost_order = {"free": 0, "low": 1, "moderate": 2, "high": 3}`, and breeds whose numeric order exceeds the ceiling are dropped before scoring.

#### `speed_profile` (string, required)

One of the values in `speed_tiers` in the index:

| Tier | Meaning |
|---|---|
| `fast` | low latency, suitable for real-time |
| `moderate` | mid latency |
| `slow` | high latency, batch-friendly |

The matcher does not filter by speed, but `compare_breeds` includes speed comparisons in its notes.

#### `trainability` (string, required)

Free-form qualitative description of how well the breed responds to fine-tuning. Examples: `"excellent — one of the most fine-tuned breeds in existence"`, `"high (responds well to RLHF and constitutional methods)"`. Not parsed by the matcher.

#### `recommended_for` (string[], required)

List of tasks or scenarios where the breed excels. Free-form text. Typically 4–7 entries.

#### `not_recommended_for` (string[], required)

List of tasks or scenarios where the breed struggles. Free-form text. May be empty for very capable general-purpose models, but should be honest.

#### `fence_compatibility` (string, required)

Free-form qualitative description of how well the model respects conservation bytecode and similar guardrails. Phrases used in the bundled registry include:

- `"excellent — follows conservation bytecode well"`
- `"good — respects conservation bytecode reliably"`
- `"moderate — varies by fine-tune"`

This is the qualitative measure of how the model interacts with the conservation-enforcer. The matcher does not currently key off it directly; it is surfaced for human review.

#### `notes` (string, optional)

A free-form paragraph that often leans into the working-dog analogy. Examples:

- *"The German Shepherd of models. Versatile, capable, expensive to feed."*
- *"The lean European working dog. Bred for efficiency over flash."*

If omitted, the loader passes `None`.

---

## Python Dataclasses

### `ModelAssessment`

Mirrors the JSON profile 1:1. See [`API.md`](API.md#class-modelassessment) for the full dataclass declaration.

Key methods:

```python
assessment.aptitude_for(task: str) -> int
```

Returns the score for `task`, or `0` if the breed has no entry for that task.

```python
assessment.overall_score() -> float
```

Mean of all working-aptitude scores. Returns `0.0` for empty dicts.

```python
ModelAssessment.from_dict(data: dict) -> ModelAssessment
```

Validates scores and constructs the instance.

### `ComparisonReport`

Returned by `compare_breeds`. See [`API.md`](API.md#class-comparisonreport).

### `AptitudeScore`

Returned by `assess_aptitude`. See [`API.md`](API.md#class-aptitudescore). Validated in `__post_init__` to ensure `0 <= score <= 10` and `isinstance(score, int)`.

---

## Constraints Summary

| Constraint | Enforced by | Failure mode |
|---|---|---|
| `working_aptitude[*]` is integer | `ModelAssessment.from_dict`, `AptitudeScore.__post_init__` | `TypeError` |
| `working_aptitude[*]` in `[0, 10]` | `ModelAssessment.from_dict`, `AptitudeScore.__post_init__` | `ValueError` |
| `cost_profile` is one of `cost_tiers` | convention; matcher defaults unknown to `"high"` (tier 3) | silent fall-through |
| `speed_profile` is one of `speed_tiers` | convention; matcher defaults unknown to `"slow"` (tier 2) | silent fall-through |
| Required fields present | convention; missing fields raise `KeyError` at dict access time | `KeyError` |
| Score keys match `task_categories` | convention | n/a |

The dataclass validation is *strict* (it raises) because the matcher must never silently accept a malformed score. The tier-name validation is *lenient* (silent fallback to the worst tier) because it is safer to include a breed in "high cost" than to fail to recommend it when the user did not specify a cost ceiling.

---

## Adding a Task Category

When you need a new task category that no breed has been scored on yet:

1. **Add the name to `task_categories`** in `registry/index.json`. This is documentation only — the matcher reads scores from per-breed `working_aptitude` keys, not from this list.
2. **Populate scores** for every breed you want to be rankable on the new task. Use `0` if the breed is genuinely poor; **omit the key** if unassessed (the matcher treats both as "no recommendation", but they communicate different things to humans reading the JSON).
3. **Document the task** in this file's working-aptitude table.

---

## Versioning the Schema

- v1.0.0 — initial release with five breeds.
- v1.0.1 — added strict score validation; no schema changes.
- v1.0.2 — internal fix only; no schema changes.
- v1.0.3 — `assess_aptitude` correctness fix; no schema changes.

The schema has been stable since v1.0.0. New fields can be added freely as long as they are optional or have defaults — existing breed files remain loadable.