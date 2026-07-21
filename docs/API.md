# API Reference — Breed Registry

> Full reference for every public symbol in `breed_registry`. If a name isn't listed here, it's private and may change without notice.

---

## Module Layout

```
breed_registry/
├── __init__        — re-exports the public API
├── models          — data classes (ModelAssessment, ComparisonReport, AptitudeScore)
└── matcher         — loader + public functions (select_breed, compare_breeds, ...)
```

Importing from the top-level package is the supported pattern:

```python
from breed_registry import (
    select_breed,
    compare_breeds,
    assess_aptitude,
    list_breeds,
    get_breed,
    ModelAssessment,
    ComparisonReport,
    AptitudeScore,
)
```

---

## `breed_registry.__init__`

Re-exports the public API surface and pins the package version.

| Symbol | Type | Notes |
|---|---|---|
| `__version__` | `str` | e.g. `"1.0.3"` |
| `select_breed` | function | Task → ranked recommendations |
| `compare_breeds` | function | Head-to-head comparison |
| `assess_aptitude` | function | Single breed × task lookup |
| `list_breeds` | function | All registered breed keys |
| `get_breed` | function | Full assessment by key |
| `ModelAssessment` | dataclass | Full breed profile |
| `ComparisonReport` | dataclass | Two-breed comparison result |
| `AptitudeScore` | dataclass | Single-model × single-task score |

`__all__` enumerates the same list.

---

## `breed_registry.matcher`

### `list_breeds() -> list[str]`

Return every registered breed key, sorted alphabetically.

```python
>>> list_breeds()
['claude-3', 'glm', 'gpt-4', 'llama-3', 'mistral']
```

**Returns:** sorted `list[str]`.

**Raises:** nothing (the registry is guaranteed to be loadable or `_load_registry` would have raised earlier).

**Notes:** cheap; reads from the cached registry. Does not include retired or invalid entries — anything that fails to load is dropped (with a warning).

---

### `get_breed(name: str) -> ModelAssessment`

Fetch the full `ModelAssessment` for one registered breed.

```python
>>> gpt4 = get_breed("gpt-4")
>>> gpt4.breed_group
'General Purpose'
>>> gpt4.working_aptitude["code_generation"]
9
```

**Args:**
- `name` (`str`): breed key as it appears in `registry/index.json`. Case-sensitive. Hyphenated lowercase by convention (`gpt-4`, `llama-3`).

**Returns:** `ModelAssessment`.

**Raises:**
- `KeyError` — when the breed is not registered. The exception message lists the available keys to make the mistake easy to recover from.

---

### `select_breed(task: str, top_k: int = 3, max_cost: Optional[str] = None) -> list[ModelAssessment]`

Rank registered breeds by their working-aptitude score on a given task.

```python
>>> recs = select_breed("code_generation", top_k=3)
>>> [(r.name, r.aptitude_for("code_generation")) for r in recs]
[('gpt-4', 9), ('llama-3', 7), ('mistral', 7)]
```

**Args:**
- `task` (`str`): task category — must match a key in at least one breed's `working_aptitude` dict (e.g. `"code_generation"`, `"analysis"`, `"creative_writing"`, `"math"`, `"following_instructions"`, `"conservation_compliance"`). Unknown tasks return an empty list.
- `top_k` (`int`, default `3`): maximum number of recommendations to return. Must be a positive integer.
- `max_cost` (`str | None`, default `None`): cost ceiling. One of `"free"`, `"low"`, `"moderate"`, `"high"`. When set, breeds whose `cost_profile` exceeds the ceiling are excluded **before** scoring. `None` means "no ceiling".

**Returns:** `list[ModelAssessment]`, best match first. Empty if no breed has a non-zero score on the task (within the cost ceiling).

**Raises:**
- `TypeError` — when `task` is not a `str`, `top_k` is not an `int`, or `max_cost` is not a `str` or `None`.
- `ValueError` — when `top_k < 1`, or `max_cost` is a string but not one of the four allowed tiers.

**Algorithm:**

1. Resolve the registry (cached on first call).
2. Filter out breeds whose `cost_profile` exceeds `max_cost`.
3. Score each remaining breed via `assessment.aptitude_for(task)`.
4. Drop breeds with `score == 0` (they're unassessed on this task, not worst).
5. Sort descending by score; stable (preserves index order on ties).
6. Slice the first `top_k` entries.

---

### `compare_breeds(model_a: str, model_b: str) -> ComparisonReport`

Build a head-to-head comparison report covering every task both breeds have been assessed on.

```python
>>> report = compare_breeds("gpt-4", "claude-3")
>>> report.winner
'claude-3'
>>> report.margin
3
>>> print(report.summary())
Comparison: gpt-4 vs claude-3
Overall winner: claude-3 (margin: 3 points)

Advantages gpt-4: code_generation
Advantages claude-3: analysis, conservation_compliance, creative_writing

Cost: Both are high cost
Speed: Both are moderate speed
```

**Args:**
- `model_a` (`str`): first breed key.
- `model_b` (`str`): second breed key.

**Returns:** `ComparisonReport` with:

| Field | Type | Meaning |
|---|---|---|
| `model_a` | `str` | echo of the first key |
| `model_b` | `str` | echo of the second key |
| `aptitude_comparison` | `dict[str, dict[str, int]]` | task → `{model_a: score, model_b: score}` |
| `winner` | `str` | `"model_a"`, `"model_b"`, or `"tie"` |
| `margin` | `int` | absolute difference of total scores |
| `advantages_a` | `list[str]` | tasks where `model_a` outscores `model_b` |
| `advantages_b` | `list[str]` | tasks where `model_b` outscores `model_a` |
| `cost_notes` | `str` | one-line cost comparison |
| `speed_notes` | `str` | one-line speed comparison |

The `summary()` method renders a multi-line human-readable block; useful for logs and CLI output.

**Raises:**
- `KeyError` — if either model is not registered.

**Notes:** the comparison iterates over the *union* of both breeds' task keys, so any task assessed for only one of them contributes asymmetrically to the totals.

---

### `assess_aptitude(model: str, task: str) -> AptitudeScore`

Look up one model's score on one task and return a fully populated `AptitudeScore` with rating and percentile.

```python
>>> score = assess_aptitude("claude-3", "analysis")
>>> score
AptitudeScore(model='claude-3', task='analysis', score=10/10, rating='excellent')
>>> score.percentile
100.0
```

**Args:**
- `model` (`str`): breed key.
- `task` (`str`): task category.

**Returns:** `AptitudeScore` with fields `model`, `task`, `score`, `rating`, `percentile`. `percentile` is the percentage of other registered breeds (with a non-zero score on the same task) that score *strictly below* the requested model. `None` when no other breed has a non-zero score on the task.

**Raises:**
- `KeyError` — if `model` is not registered.

**Notes:** a score of `0` means "unassessed on this task", not "worst at it". The percentile is calculated against scored entries only.

---

## `breed_registry.models`

### `class AptitudeScore`

Single-model × single-task result returned by `assess_aptitude`.

```python
@dataclass
class AptitudeScore:
    model: str
    task: str
    score: int                       # 0-10
    rating: str                      # human-readable
    percentile: Optional[float] = None
```

**Validation (in `__post_init__`):**
- `score` must be an `int` (raises `TypeError` otherwise).
- `score` must satisfy `0 <= score <= 10` (raises `ValueError` otherwise).

**Rating bands** (from `_score_to_rating()`):

| Score range | Rating |
|---|---|
| 9–10 | `"excellent"` |
| 7–8 | `"good"` |
| 5–6 | `"fair"` |
| 3–4 | `"poor"` |
| 0–2 | `"unsuitable"` |

**Repr:** `AptitudeScore(model='...', task='...', score=N/10, rating='...')`.

---

### `class ComparisonReport`

Head-to-head comparison returned by `compare_breeds`. See the full field table above.

```python
@dataclass
class ComparisonReport:
    model_a: str
    model_b: str
    aptitude_comparison: Dict[str, Dict[str, int]]
    winner: str                      # "model_a" | "model_b" | "tie"
    margin: int
    advantages_a: List[str]
    advantages_b: List[str]
    cost_notes: str
    speed_notes: str

    def summary(self) -> str: ...
```

`summary()` renders a multi-line plain-text report.

---

### `class ModelAssessment`

The core dataclass — one breed's full profile. Loaded from JSON via `ModelAssessment.from_dict(data)`.

```python
@dataclass
class ModelAssessment:
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
```

**Class method:**

```python
@classmethod
def from_dict(cls, data: dict) -> "ModelAssessment"
```

Constructs a `ModelAssessment` from a JSON-style dict. Validates every score in `working_aptitude` is an integer in `[0, 10]`; raises `TypeError` for non-ints and `ValueError` for out-of-range scores.

**Methods:**

```python
def aptitude_for(self, task: str) -> int
```

Return the score for `task`. Returns `0` if the breed has no entry for the task — by convention, "unassessed" rather than "worst".

```python
def overall_score(self) -> float
```

Mean of all working-aptitude scores. Returns `0.0` if no tasks are assessed.

---

## Private Surface (Subject to Change)

These exist but are not part of the public contract:

- `breed_registry.matcher._REGISTRY_DIR` — `Path` to the bundled `registry/` directory.
- `breed_registry.matcher._REGISTRY_CACHE` — module-level memoised dict.
- `breed_registry.matcher._load_registry(registry_dir=None)` — loader used internally; also useful in tests and custom deployments.
- `breed_registry.matcher._get_registry()` — returns the cache (loads on first call).
- `breed_registry.matcher._score_to_rating(score: int) -> str` — maps 0–10 to a band string.

Avoid depending on these from outside the package. If you need them, file an issue describing the use-case and we will consider promoting them to public.

---

## Exceptions Summary

| Exception | When |
|---|---|
| `FileNotFoundError` | `registry/index.json` is missing at the resolved path |
| `KeyError` | `get_breed`/`compare_breeds`/`assess_aptitude` called with an unregistered model |
| `TypeError` | invalid argument types to `AptitudeScore`, `ModelAssessment.from_dict`, or `select_breed` |
| `ValueError` | out-of-range scores, non-positive `top_k`, invalid `max_cost` tier |
| `warnings.warn` (not exception) | a breed listed in `index.json` has no corresponding file |

---

## Thread Safety

The registry loader uses a module-level cache and is **not** thread-safe on first call. In multi-threaded contexts, call `list_breeds()` once at startup before forking workers; subsequent calls reuse the populated cache without contention.