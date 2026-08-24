"""Stable product ranking over the deterministic scorer."""

from collections.abc import Sequence

from opentradeintel.matching.scorer import cpv_overlap, score_product
from opentradeintel.models import MatchResult, Product, Tender


class DeterministicMatcher:
    """Score and rank products without randomness or external services."""

    def match(
        self,
        tender: Tender,
        products: Sequence[Product],
        limit: int | None = None,
    ) -> list[MatchResult]:
        if limit is not None and limit <= 0:
            raise ValueError("match limit must be positive")
        results = [score_product(tender, product) for product in products]
        ranked = sorted(
            results,
            key=lambda result: (
                -result.score,
                -len(cpv_overlap(tender, result.product)),
                result.product.sku.casefold(),
            ),
        )
        return ranked if limit is None else ranked[:limit]
