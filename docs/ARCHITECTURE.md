# Architecture — Breed Registry

> How the registry is wired, how breeds get in, how the matcher reasons over them, and how the package fits into Working Animal Infrastructure.

---

## 1. Purpose and Position

`breed-registry` is the **selection layer** of Working Animal Architecture. Its job is to answer one question well:

> *Given a task, which foundation model "breed" should be sent the prompt?*

In the working-animal paradigm, this is the equivalent of choosing the right breed of dog for a job — border collie for herding, labrador for retrieving, malinois for bite work. The decision is the single most consequential one you make; everything downstream depends on it.

The package sits alongside (and upstream of) the rest of Working Animal Infrastructure:

```
                ┌──────────────────────────────────────────┐
                │             Task / Prompt                │
                └──────────────────────────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────────────┐
              │             breed-registry                │   ← YOU ARE HERE
              │  (model selection — which breed fits)      │
              └────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────────────┐
              │          conservation-enforcer             │   ← Tier 2 fence
              │  (guardrails, bytecode compliance)         │
              └────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────────────┐
              │           shepherds-console                │   ← Tier 2 ops
              │  (logging, cost tracking, rotation)        │
              └────────────────────────────────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────────────┐
                │        Breed X runs the prompt           │
                └──────────────────────────────────────────┘
```

The breed registry never invokes a model directly. It returns the choice; the caller dispatches.

---

## 2. Package Layout

```
breed-registry/
├── pyproject.toml            # Build metadata, version, deps
├── README.md                 # Quick-start + philosophy
├── CHANGELOG.md              # Release history
├── LICENSE                   # MIT
├── DOCS.md                   # Companion guide (high-level API + ecosystem)
├── docs/
│   ├── ARCHITECTURE.md       # This file
│   ├── API.md                # Full public-API reference
│   ├── EXAMPLES.md           # Worked examples (3+)
│   └── SCHEMA.md             # Field-by-field schema
├── src/breed_registry/
│   ├── __init__.py           # Public surface — re-exports
│   ├── models.py             # Dataclasses: ModelAssessment, ComparisonReport, AptitudeScore
│   └── matcher.py            # Loader + select_breed / compare_breeds / assess_aptitude
├── registry/                 # Curated breed profiles (JSON)
│   ├── index.json            # Manifest of registered breeds + task categories
│   ├── gpt-4.json
│   ├── claude-3.json
│   ├── llama-3.json
│   ├── glm.json
│   └── mistral.json
└── tests/
    └── test_matcher.py       # Behavioural + regression tests
```

The `src/` layout keeps the import path stable across editable installs and avoids shadowing by any stray `breed_registry/` folder at the project root.

---

## 3. Data Flow — From Task to Recommendation

```
            ┌───────────────────────┐
            │  task: "code gen"     │
            └───────────────────────┘
                       │
                       ▼
            ┌──────────────────────────────────────┐
            │ select_breed(task, top_k, max_cost)  │
            └──────────────────────────────────────┘
                       │
        ┌──────────────┴───────────────────────────────┐
        │ 1. _get_registry() returns dict[name, MA]   │
        │ 2. Filter by cost_profile ≤ cost_ceiling     │
        │ 3. For each remaining: breed.aptitude_for() │
        │ 4. Drop zero-score entries                  │
        │ 5. Sort desc by score                       │
        │ 6. Slice [:top_k]                           │
        └──────────────┬───────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │  [gpt-4, llama-3, mistral]               │
        └──────────────────────────────────────────┘
                       │
                       ▼
        caller dispatches prompt to each in turn
```

Three things to notice:

1. **Cost filtering happens before scoring.** Cheap-first triage prevents a $0.0001 model from being out-ranked by a $0.03 model when only "free" is allowed.
2. **Zero-score breeds are dropped from the result.** A breed with no assessment for the requested task is not "the worst at it" — it is *unassessed*. Surface that distinction by returning an empty list rather than a misleading ranking.
3. **The matcher never mutates the registry.** All filtering and sorting operate on transient lists; the loaded assessments are cached but read-only.

---

## 4. Registry Loading

`matcher._load_registry()` reads `registry/index.json`, then for each entry loads the corresponding breed file and constructs a `ModelAssessment` via `ModelAssessment.from_dict()`.

- **Validation:** Scores outside 0–10 or non-integer scores raise `ValueError` / `TypeError` (added in v1.0.1).
- **Missing files:** Emit a `warnings.warn(...)` rather than failing silently (added in v1.0.1).
- **Missing `index.json`:** Raise `FileNotFoundError` — there is no registry at all.
- **Caching:** The loaded registry is memoised in a module-level `_REGISTRY_CACHE`. The first call loads; subsequent calls return the cached dict. Reloading the registry in a long-running process is not supported (and not currently needed).

The registry directory is computed relative to the installed package:

```python
_REGISTRY_DIR = Path(__file__).resolve().parent.parent.parent / "registry"
```

This layout works for both editable installs (`pip install -e .`) and wheel installs.

---

## 5. Decision Logic — How Recommendations Are Made

The matching algorithm is deliberately simple. It is **not** a learned ranker; it is a deterministic lookup scored against a curated table. The choices baked into the design:

### 5.1 Score-only ranking
`select_breed()` sorts strictly by `working_aptitude[task]`. There is no tie-breaker for cost, speed, or fence compatibility — those are surfaced separately so the *caller* can apply policy.

If you need a "best cheap model" recommendation, pass `max_cost="low"` (or `"free"`); cost filtering happens before scoring.

### 5.2 Single-task matching
The matcher always scores against one task at a time. There is no compound task like `"code generation + analysis"`. If you need compound reasoning, run two lookups and intersect.

### 5.3 Head-to-head comparison
`compare_breeds(a, b)` builds a full per-task matrix and tallies advantages. The "winner" is whoever has the larger *sum* of scores across all tasks — not the most task wins. This matches the intuition that an 8/8/8 model beats a 10/6/6 model on average.

### 5.4 Single-model assessment
`assess_aptitude(model, task)` returns one score, one rating, and a percentile. The percentile is computed against every breed that has a *non-zero* score on the task — a score of 0 means unassessed, not zero-percentile.

---

## 6. Working-Animal Concepts Encoded in the Schema

Every field in a `ModelAssessment` has a working-dog analogue. This is the philosophical commitment of the registry: **breeds are characterised by working aptitude, not conformation**. The schema reflects that.

| Field | Dog analogue | Operational meaning |
|---|---|---|
| `lineage` | Pedigree | Which family this model comes from; informs trust |
| `breed_group` | AKC group (Herding, Sporting, Working) | Coarse task category |
| `temperament` | Breed temperament | Behavioral characteristics that affect output style |
| `working_aptitude` | Instinct tests | Per-task scores (0–10) — the heart of the registry |
| `cost_profile` | Feed cost | API cost tier: `free`, `low`, `moderate`, `high` |
| `speed_profile` | Speed/agility | Latency tier: `fast`, `moderate`, `slow` |
| `trainability` | Ease of training | Free-text qualitative rating |
| `recommended_for` | Best-suited jobs | Where this breed excels |
| `not_recommended_for` | Wrong-fit jobs | Where this breed struggles |
| `fence_compatibility` | Boundary respect | How well the model follows conservation bytecode |
| `notes` | Breed profile blurb | Free-text background |

---

## 7. Extension Points

### 7.1 Add a new breed
1. Create `registry/<model-name>.json` following the schema (see [`SCHEMA.md`](SCHEMA.md)).
2. Add an entry under `"breeds"` in `registry/index.json`.
3. The next call to any matcher function loads it automatically — no Python changes required.

### 7.2 Add a new task category
1. Update `task_categories` in `registry/index.json` (documentation only — the matcher reads task names from each breed's `working_aptitude` keys, not from the index).
2. Populate scores for every breed that should be assessable on the new task.

### 7.3 Custom registry directory
`_load_registry(registry_dir=...)` accepts an optional path. There is currently no public wrapper for this; if you need it, call `_load_registry` directly. A future `load_registry_from(path: Path)` public function is on the wishlist.

### 7.4 Embedding-based ranking (future)
The current matcher is purely tabular. A future iteration could combine the curated scores with a learned embedding-similarity reranker for free-form task descriptions. The schema deliberately leaves room for `notes` to carry corpus samples for that.

---

## 8. Testing Strategy

Tests live in `tests/test_matcher.py` and cover:

- **Smoke tests** for every public function (`list_breeds`, `get_breed`, `select_breed`, `compare_breeds`, `assess_aptitude`).
- **Validation regression tests** (`TestValidationRegression`) — pins the v1.0.1 input-validation fixes.
- **Bug regression tests** — `test_returns_requested_breed_score_not_iterated_score` pins the v1.0.3 variable-shadowing fix in `assess_aptitude`.

Run with:

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

The tests rely on the real `registry/` data files; no mocks. This means they double as a schema conformance check — if you break the schema, the smoke tests will fail.

---

## 9. Versioning and Compatibility

`breed-registry` follows pragmatic SemVer:

- **Patch** — bug fixes, doc improvements, no API change.
- **Minor** — new public functions, new registry fields with sane defaults.
- **Major** — breaking changes to public API or schema.

Current: **v1.0.3** (post-shadowing-fix release). Public API is stable; the `ModelAssessment` dataclass is the contract.

---

## 10. What This Package Is Not

To set expectations clearly:

- **Not** a model invoker. It returns recommendations; you dispatch.
- **Not** a learned ranker. Scores are hand-curated by humans who have used the models.
- **Not** a benchmark harness. The scores are *practitioner assessments*, not MMLU numbers.
- **Not** exhaustive. Five breeds ship by default. Add your own; the matcher will pick them up.
- **Not** opinion-free. The very name — "breed registry" — is a stance: foundation models have *lineages* and *working aptitudes*, not generic "capabilities".

---

## 11. See Also

- [`API.md`](API.md) — full function-by-function reference
- [`EXAMPLES.md`](EXAMPLES.md) — worked usage examples
- [`SCHEMA.md`](SCHEMA.md) — field-by-field schema for `ModelAssessment` and the registry JSON
- [`../README.md`](../README.md) — quick-start and selection philosophy
- [`../DOCS.md`](../DOCS.md) — companion guide with broader ecosystem context