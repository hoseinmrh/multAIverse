import hashlib
import random
from collections.abc import Sequence
from typing import TypeVar

ChoiceT = TypeVar("ChoiceT")


def derive_seed(root_seed: int, *parts: object) -> int:
    """Derive a stable sub-seed without relying on Python's randomized hash()."""

    material = "\x1f".join([str(root_seed), *(str(part) for part in parts)])
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


class SeededRandom:
    """Namespaced deterministic PRNG streams for replay-safe simulation."""

    def __init__(self, root_seed: int) -> None:
        self.root_seed = root_seed

    def stream(self, *parts: object) -> random.Random:
        return random.Random(derive_seed(self.root_seed, *parts))

    def chance(self, probability: float, *parts: object) -> bool:
        bounded_probability = max(0.0, min(1.0, probability))
        return self.stream(*parts).random() < bounded_probability

    def choice(self, values: Sequence[ChoiceT], *parts: object) -> ChoiceT:
        if not values:
            raise ValueError("Cannot select from an empty sequence")
        return values[self.stream(*parts).randrange(len(values))]

    def weighted_choice(
        self,
        values: Sequence[tuple[ChoiceT, float]],
        *parts: object,
    ) -> ChoiceT:
        if not values:
            raise ValueError("Cannot select from an empty weighted sequence")
        if any(weight < 0 for _, weight in values):
            raise ValueError("Weights must be nonnegative")
        total = sum(weight for _, weight in values)
        if total <= 0:
            raise ValueError("At least one weight must be positive")
        threshold = self.stream(*parts).random() * total
        cumulative = 0.0
        for value, weight in values:
            cumulative += weight
            if threshold < cumulative:
                return value
        return values[-1][0]
