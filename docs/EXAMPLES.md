# Examples — Breed Registry

> Worked usage examples. Every example here is runnable end-to-end against the bundled registry and verified by the test suite.

---

## Setup

```bash
pip install -e .
```

Or, without installing:

```bash
PYTHONPATH=src python3 ...
```

---

## Example 1 — Register a New Breed (data-only workflow)

The simplest "register" workflow is data-only — no Python code changes. Just add a JSON file and an entry in the index.

### Step 1: Create the breed profile

Create `registry/qwen-2.5.json`:

```json
{
  "name": "qwen-2.5",
  "lineage": "Qwen family (Alibaba) — open-weights lineage with strong multilingual and code training",
  "breed_group": "Working",
  "temperament": ["efficient", "multilingual", "code-oriented", "pragmatic"],
  "working_aptitude": {
    "code_generation": 8,
    "analysis": 8,
    "creative_writing": 7,
    "math": 8,
    "following_instructions": 8,
    "conservation_compliance": 8
  },
  "cost_profile": "low",
  "speed_profile": "fast",
  "trainability": "good (responds well to instruction tuning)",
  "recommended_for": [
    "code generation",
    "multilingual tasks",
    "mathematical reasoning",
    "production deployments needing cost efficiency"
  ],
  "not_recommended_for": [
    "maximum-depth English creative writing",
    "tasks requiring long-context comprehension beyond 32k"
  ],
  "fence_compatibility": "good — respects conservation bytecode reliably",
  "notes": "The efficient Asian working breed. Strong on code and math, very cost-effective, multilingual out of the box."
}
```

### Step 2: Register in the index

Edit `registry/index.json` to add the new entry under `"breeds"`:

```json
{
  "breeds": {
    "qwen-2.5": {
      "file": "qwen-2.5.json",
      "breed_group": "Working",
      "cost_profile": "low",
      "speed_profile": "fast",
      "summary": "Efficient multilingual breed, strong on code and math"
    },
    ...
  }
}
```

### Step 3: Confirm registration

```python
from breed_registry import list_breeds, get_breed

print(list_breeds())
# ['claude-3', 'glm', 'gpt-4', 'llama-3', 'mistral', 'qwen-2.5']

qwen = get_breed("qwen-2.5")
print(qwen.working_aptitude["code_generation"])  # 8
print(qwen.cost_profile)                          # low
```

No code change required. The matcher picks up the new breed on the next call.

---

## Example 2 — Query: Picking the Best Breed for a Task

Use `select_breed` to rank registered breeds against a task description. This is the most common operation.

### Pick the top 3 breeds for code generation

```python
from breed_registry import select_breed

recs = select_breed("code_generation", top_k=3)
for r in recs:
    score = r.aptitude_for("code_generation")
    print(f"  {r.name:<10}  score={score}/10  cost={r.cost_profile}")
```

Output (with the bundled registry):

```
  gpt-4       score=9/10  cost=high
  claude-3    score=8/10  cost=high
  llama-3     score=7/10  cost=free (open weights)
```

### Filter by cost ceiling

```python
from breed_registry import select_breed

# Only free or low cost — drop the high-cost GPT-4 and Claude-3
cheap = select_breed("code_generation", max_cost="low")
for r in cheap:
    print(f"  {r.name:<10}  cost={r.cost_profile}  score={r.aptitude_for('code_generation')}/10")
```

Output:

```
  glm         cost=low    score=7/10
  mistral     cost=low    score=7/10
```

### Discover the best analytical breed

```python
from breed_registry import select_breed

top_analyst = select_breed("analysis", top_k=1)[0]
print(f"Best breed for analysis: {top_analyst.name}")
print(f"  lineage:        {top_analyst.lineage}")
print(f"  temperament:    {', '.join(top_analyst.temperament)}")
print(f"  fence:          {top_analyst.fence_compatibility}")
print(f"  best for:       {', '.join(top_analyst.recommended_for)}")
```

Output:

```
Best breed for analysis: claude-3
  lineage:        Claude family (Anthropic) — trained with Constitutional AI methodology
  temperament:    careful, analytical, nuanced, safety-conscious
  fence:          excellent — bred for compliance, respects boundaries instinctively
  best for:       deep analysis, careful reasoning, long-context comprehension, ...
```

### Unknown task → empty list

```python
from breed_registry import select_breed

result = select_breed("unicorn_juggling")
assert result == []   # no breed has been assessed on this task
print("No breeds assessed on this task — picker returned empty.")
```

---

## Example 3 — Compare Two Breeds Head-to-Head

Use `compare_breeds` to get a full per-task matrix plus a textual summary.

```python
from breed_registry import compare_breeds

report = compare_breeds("gpt-4", "claude-3")

print(report.summary())
```

Output:

```
Comparison: gpt-4 vs claude-3
Overall winner: claude-3 (margin: 3 points)

Advantages gpt-4: code_generation
Advantages claude-3: analysis, conservation_compliance, creative_writing

Cost: Both are high cost
Speed: Both are moderate speed
```

Drilling into the structured fields:

```python
# Who wins on which tasks?
print("GPT-4 advantages:", report.advantages_a)
print("Claude-3 advantages:", report.advantages_b)

# Per-task scores
for task, scores in sorted(report.aptitude_comparison.items()):
    a, b = scores["gpt-4"], scores["claude-3"]
    arrow = "→" if a > b else ("←" if b > a else "=")
    print(f"  {task:<25}  gpt-4={a}  claude-3={b}  {arrow}")

# Margin tells you the *size* of the win, not just who
print(f"Winner: {report.winner} by {report.margin} total points")
```

Use `compare_breeds` when you are torn between two specific breeds and want a multi-dimensional view, not a single ranking.

---

## Example 4 — Assess a Single Model's Aptitude (with Percentile)

Use `assess_aptitude` for a precise, single-point lookup that also reports where the model ranks among its peers.

```python
from breed_registry import assess_aptitude

score = assess_aptitude("claude-3", "analysis")
print(f"Model:    {score.model}")
print(f"Task:     {score.task}")
print(f"Score:    {score.score}/10")
print(f"Rating:   {score.rating}")
print(f"Percentile: {score.percentile}%")
```

Output:

```
Model:    claude-3
Task:     analysis
Score:    10/10
Rating:   excellent
Percentile: 80.0%
```

Interpretation: Claude-3 is at the top of the registry for `analysis` — 80% of the cohort that has a non-zero score on this task scored strictly below 10 (GPT-4 is at 9; the others are at 7).

For a less obvious breed:

```python
from breed_registry import assess_aptitude

score = assess_aptitude("llama-3", "conservation_compliance")
print(f"llama-3 / conservation_compliance: {score.score}/10 ({score.rating}) "
      f"— percentile {score.percentile}%")
```

```
llama-3 / conservation_compliance: 6/10 (fair) — percentile 0.0%
```

Interpretation: Llama-3 is at the *bottom* of the cohort for conservation compliance — its score is the lowest non-zero value among registered breeds. (Note: `0.0%` percentile means "no breed scored strictly below me", not "I scored zero".)

---

## Example 5 — Programmatically Walk the Registry

```python
from breed_registry import list_breeds, get_breed

print(f"{'breed':<10} {'group':<16} {'cost':<9} {'speed':<9} {'avg':<5}")
print("-" * 55)
for name in list_breeds():
    a = get_breed(name)
    print(f"{a.name:<10} {a.breed_group:<16} {a.cost_profile:<9} "
          f"{a.speed_profile:<9} {a.overall_score():.1f}")
```

Output:

```
breed      group            cost      speed     avg
-------------------------------------------------------
claude-3   General Purpose  high      moderate  8.8
glm        General Purpose  low       fast      7.3
gpt-4      General Purpose  high      moderate  8.3
llama-3    Open Lineage     free (open weights)  fast (especially smaller variants)  6.7
mistral    Working          low       fast      7.0
```

Note: the bundled `llama-3` and `mistral` JSON files include parenthetical
notes inside their `cost_profile` / `speed_profile` strings (e.g. `"free (open weights)"`).
The matcher treats these as opaque tier labels; the parentheticals are
purely for human readers.

Use this pattern to render a dashboard, write a status report, or feed downstream ranking logic.

---

## Example 6 — Filtering by Multiple Constraints

`select_breed` supports a single cost ceiling; for finer-grained filtering, score the recommendations yourself:

```python
from breed_registry import select_breed

def fast_and_cheap(task: str, top_k: int = 3) -> list:
    """Picks breeds that are both fast and cheap for a task."""
    candidates = select_breed(task, top_k=top_k * 3)  # over-fetch
    filtered = [a for a in candidates if a.speed_profile == "fast"]
    return filtered[:top_k]

for a in fast_and_cheap("code_generation"):
    print(f"  {a.name:<10}  speed={a.speed_profile}  cost={a.cost_profile}")
```

```
  glm         speed=fast  cost=low
  mistral     speed=fast  cost=low
```

---

## Example 7 — Loading a Custom Registry

If you maintain a private registry directory, load it explicitly:

```python
from pathlib import Path
from breed_registry.matcher import _load_registry

my_dir = Path("/opt/myorg/breeds")
breeds = _load_registry(registry_dir=my_dir)
```

Then build a matcher manually using the loaded dict:

```python
# Public-API only: top-k is built into select_breed. For custom registries,
# iterate the loaded assessments directly.
def custom_select(breeds, task, top_k=3):
    scored = [(b.aptitude_for(task), b) for b in breeds.values()]
    scored = [(s, b) for s, b in scored if s > 0]
    scored.sort(reverse=True)
    return [b for _, b in scored[:top_k]]

top3 = custom_select(_load_registry(my_dir), "analysis", top_k=3)
```

Note: the private API (`_load_registry`) is subject to change. If you need stable custom-registry support, file an issue and we will promote it.

---

## Error-Handling Patterns

Always guard against unregistered breeds:

```python
from breed_registry import get_breed

def safe_overall(name: str) -> float:
    try:
        return get_breed(name).overall_score()
    except KeyError as e:
        # The error message already lists valid keys
        raise SystemExit(f"Unknown breed: {e}") from None
```

Validate task categories against what you actually use:

```python
from breed_registry import select_breed

VALID_TASKS = {"code_generation", "analysis", "creative_writing",
               "math", "following_instructions", "conservation_compliance"}

def safe_select(task: str, top_k: int = 3):
    if task not in VALID_TASKS:
        raise ValueError(f"Unknown task {task!r}; pick from {VALID_TASKS}")
    return select_breed(task, top_k=top_k)
```

Treat empty `select_breed` results as "unassessed", not "no good options":

```python
recs = select_breed("some_brand_new_task")
if not recs:
    print("No breed has been scored on this task yet. "
          "Pick a default and add scores to the registry.")
else:
    use(recs[0])
```