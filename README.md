# The Breed Registry

> Model selection as breeding selection. Maps tasks to recommended base models.

Working Animal Architecture treats AI models as working animal breeds — each with
distinct temperaments, aptitudes, and working profiles. The Breed Registry assesses
models across standardized criteria and recommends the right breed for the job.

## Core Concepts

| Concept        | Registry Term      |
|---------------|-------------------|
| AI Model       | Breed             |
| Model Family   | Lineage           |
| Task Type      | Working Class     |
| Score (0–10)   | Aptitude Score    |

## Breeds Assessed

- **GPT-4** — Thoroughbred: premium reasoning, high cost
- **Claude 3** — Warmblood: balanced reasoning and instruction-following
- **Llama 3** — Mustang: rugged, open, self-reliant
- **GLM** — Arabian: compact, efficient, strong in multilingual terrain
- **Mistral** — Andalusian: agile, refined, European pedigree
- **Gemini** — Hanoverian: multimodal strength, Google lineage
- **Qwen** — Shire: massive context, heavy-load carrier

## Usage

```python
from breed_registry import select_breed, compare_breeds, assess_aptitude

# Pick the best model for a task
result = select_breed("code_generation")
print(result.recommended)  # "gpt-4"

# Compare two models head-to-head
comparison = compare_breeds("gpt-4", "claude-3")
print(comparison.winner)  # depends on task weighting

# Assess a specific model for a specific task
score = assess_aptitude("llama-3", "summarization")
print(score.overall)  # 7.8
```

## License

MIT — See [LICENSE](LICENSE).