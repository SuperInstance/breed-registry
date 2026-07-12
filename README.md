# The Breed Registry 🐕🧬

**Model selection as breeding selection.**

Choosing an LLM shouldn't be harder than choosing a dog. The Breed Registry treats AI models like dog breeds — each with distinct temperament, working aptitude, cost, and fence compatibility — so you can match the right model to the right task using a vocabulary everyone already understands.

## Why Breeds?

| Dog Breed | LLM Analog | Why It Fits |
|---|---|---|
| Border Collie | GPT-4 | Elite working intelligence, high cost, needs mental stimulation |
| Labrador | Claude 3 | Reliable, gentle, great with instructions (family-safe) |
| Husky | LLaMA 3 | Energetic, open-range, runs well in cold (open-source) |
| Jack Russell | GLM | Small, fast, feisty — punches above its weight |
| Greyhound | Mistral | Lean, blisteringly fast, built for a single purpose |
| Golden Retriever | Gemini | Friendly, multimodal, fetches anything you throw |
| Australian Shepherd | Qwen | Hardworking, versatile, herds complex tasks efficiently |

## Quick Start

```python
from breed_registry import select_breed, compare_breeds, assess_aptitude

# Pick the best model for a task
best = select_breed("summarize a legal contract")
print(best["model"])  # → claude-3

# Compare two models head-to-head
versus = compare_breeds("gpt-4", "llama-3")
print(versus["winner"])  # → depends on the task profile

# Score a specific model on a specific task
score = assess_aptitude("mistral", "code generation")
print(score["working_aptitude"])  # → 7.5
```

## Registry Structure

```
registry/
├── index.json                # Master index of all breeds
└── models/
    ├── gpt-4.json            # Border Collie
    ├── claude-3.json         # Labrador
    ├── llama-3.json          # Husky
    ├── glm.json              # Jack Russell
    ├── mistral.json          # Greyhound
    ├── gemini.json           # Golden Retriever
    └── qwen.json             # Australian Shepherd
```

Each breed assessment includes:

- **Temperament** — personality traits (precision, caution, creativity, etc.)
- **Working Aptitude** — scored 1–10 across task categories
- **Cost & Speed** — $/1K tokens and latency tiers
- **Recommended For** — best-use scenarios
- **Fence Compatibility** — how well it stays on-task (guardrails)

## License

MIT — see [LICENSE](LICENSE).
