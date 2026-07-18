# breed-registry — Documentation

**Model selection as breeding selection. Structured registry for foundation model "breeds" with working-aptitude scoring and task-based recommendations.**

> Companion guide to README.md. This document covers the data model, matching algorithm, and programmatic API.

---

## What this package does

The Breed Registry is the **model selection layer** of Working Animal Infrastructure. Each foundation model is registered like a working dog at a confirmation show — assessed for **working aptitude**, not conformation. The registry provides:

1. **Structured breed profiles** — fields for lineage, breed group, temperament, working aptitude scores per task category, cost profile, speed profile, trainability.
2. **Task-based matcher** — given a task description (e.g. "code generation", "creative writing", "constraint discovery"), score all registered breeds and recommend the top picks with reasoning.
3. **Socratic casting order** — for multi-model orchestration, recommend casting order thin → thick (cheap discovery first, expensive synthesis second).

This package is what tells your orchestrator which model to send which prompt to.

---

## Architecture context

Sits alongside `conservation-enforcer` (Tier 2 enforcement) and `shepherds-console` (Tier 2 ops) in Working Animal Infrastructure.

The flow:

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Task (string)   │ ───> │  breed_registry  │ ───> │ Pick: breed X    │
│  e.g. "code"     │      │  rank(task, k=3) │      │ confidence 0.85  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                │
                                ├── thin → discovery breeds first
                                ├── thick → synthesis breeds last
                                └── balanced → equal cast
```

The discovery / synthesis dichotomy comes from the **chart-thickness metaphor** (see `docs/GAMMA_ETA_SPEC.md` in the `conservation-enforcer` package). Thin charts (cheap, narrow) discover. Thick charts (expensive, broad) synthesize.

---

## Data model

### `breed_registry.models.Breed`

```python
@dataclass
class Breed:
    name: str                          # "DeepSeek V4 Flash"
    lineage: str                       # "DeepSeek-AI"
    breed_group: BreedGroup            # GENERAL | WORKING | HERDING | ...
    temperament: list[str]             # ["careful", "concise"]
    working_aptitude: dict[TaskType, int]   # {CODE: 8, REASONING: 7, ...}
    cost_profile: CostProfile          # $/1K tokens
    speed_profile: SpeedProfile        # latency in ms
    trainability: int                  # 0-10
    recommended_for: list[str]         # ["code completion", "agent loops"]
    chart_thickness: ChartThickness    # THIN | BALANCED | THICK | ULTRA_THICK
```

### `breed_registry.models.TaskType`

Enumeration of task categories: `CODE`, `REASONING`, `CREATIVE_WRITING`, `CONSTRAINT_DISCOVERY`, `SYNTHESIS`, `DATA_EXTRACTION`, `CONVERSATION`, `MATH`, `MULTILINGUAL`, `VISION`, `AUDIO`.

---

## API reference

### `breed_registry.matcher.BreedMatcher`

```python
from breed_registry import BreedMatcher, load_registry

matcher = BreedMatcher(breeds=load_registry())

# Top-K picks for a task
top = matcher.rank(task="code completion", k=3)
for pick in top:
    print(f"{pick.breed.name}: score={pick.score:.3f}, why={pick.reasoning}")

# Single recommendation with confidence
rec = matcher.recommend(task="creative poetry", min_confidence=0.7)
if rec:
    print(f"Use {rec.breed.name} (confidence {rec.confidence:.2f})")
```

### `breed_registry.matcher.SocraticCaster`

For multi-model orchestration: returns the casting order.

```python
from breed_registry.matcher import SocraticCaster

caster = SocraticCaster(breeds=[...])
order = caster.cast_order(task="discovery")  # [thin_breed, balanced, thick]
for breed in order:
    send_to_breed(breed, prompt)
```

### `breed_registry.__init__.load_registry()`

Load the curated registry shipped with the package (defaults to ~12 well-known foundation models).

---

## Usage example

```python
from breed_registry import BreedMatcher, load_registry

matcher = BreedMatcher(breeds=load_registry())

# Discover the best breed for constraint discovery
result = matcher.rank(task="constraint discovery", k=3)
for entry in result:
    print(f"  {entry.breed.name}: {entry.score:.2f}  ({entry.reasoning})")

# Example output:
#   deepseek-ai/DeepSeek-V4-Flash: 0.86  (thin chart, high constraint-discovery score, cheap)
#   openai/gpt-4o-mini: 0.71          (balanced chart, broad capability, mid cost)
#   anthropic/claude-3-opus: 0.62    (thick chart, exhaustive but expensive)
```

---

## Ecosystem

- **Registry data:** `registry/*.yaml` — hand-curated breed profiles
- **Tests:** `tests/test_matcher.py`, `tests/test_models.py`
- **Related:** `conservation-enforcer` (enforcement layers), `shepherds-console` (ops dashboard), `AI-Writings/SOCRATIC_CASTING_PROTOCOL.md` (the theory)

## License

MIT — see `LICENSE`.
