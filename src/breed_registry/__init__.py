"""
The Breed Registry — model selection as breeding selection.

Treat AI models like dog breeds. Pick the right one for the job.
"""

from .matcher import (
    select_breed,
    compare_breeds,
    assess_aptitude,
    BreedMatcher,
    BREED_REGISTRY,
)

__version__ = "1.0.0"
__all__ = [
    "select_breed",
    "compare_breeds",
    "assess_aptitude",
    "BreedMatcher",
    "BREED_REGISTRY",
]

