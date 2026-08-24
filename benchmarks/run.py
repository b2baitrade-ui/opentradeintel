"""Run the synthetic deterministic matcher benchmark."""

from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from opentradeintel.matching import DeterministicMatcher
from opentradeintel.models import Product, Tender

DEFAULT_DATASET = Path(__file__).with_name("dataset.json")


class BenchmarkCase(BaseModel):
    """One opportunity and its hand-authored binary relevance labels."""

    model_config = ConfigDict(extra="forbid")

    tender: Tender
    relevant_skus: list[str] = Field(min_length=1)


class BenchmarkDataset(BaseModel):
    """Validated benchmark products and opportunities."""

    model_config = ConfigDict(extra="forbid")

    products: list[Product] = Field(min_length=1)
    opportunities: list[BenchmarkCase] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identifiers_and_labels(self) -> Self:
        skus = [product.sku for product in self.products]
        if len(set(skus)) != len(skus):
            raise ValueError("benchmark product SKUs must be unique")
        opportunity_ids = [case.tender.id for case in self.opportunities]
        if len(set(opportunity_ids)) != len(opportunity_ids):
            raise ValueError("benchmark opportunity IDs must be unique")
        known_skus = set(skus)
        for case in self.opportunities:
            unknown = sorted(set(case.relevant_skus) - known_skus)
            if unknown:
                raise ValueError(
                    f"benchmark opportunity '{case.tender.id}' references unknown SKUs: "
                    f"{', '.join(unknown)}"
                )
        return self


class RankingMetrics(BaseModel):
    """Aggregate ranking metrics rounded to four decimal places."""

    model_config = ConfigDict(extra="forbid")

    precision_at_1: float = Field(ge=0, le=1)
    precision_at_3: float = Field(ge=0, le=1)
    mrr: float = Field(ge=0, le=1)


class FalsePositiveExample(BaseModel):
    """A top-ranked product absent from the relevance labels."""

    model_config = ConfigDict(extra="forbid")

    opportunity_id: str
    predicted_sku: str
    score: int
    relevant_skus: list[str]


class FalseNegativeExample(BaseModel):
    """A relevant product ranked below the first three results."""

    model_config = ConfigDict(extra="forbid")

    opportunity_id: str
    relevant_sku: str
    rank: int | None


class BenchmarkResult(BaseModel):
    """Machine-readable benchmark result and diagnostic examples."""

    model_config = ConfigDict(extra="forbid")

    product_count: int
    opportunity_count: int
    metrics: RankingMetrics
    false_positives: list[FalsePositiveExample]
    false_negatives: list[FalseNegativeExample]


def load_dataset(path: Path = DEFAULT_DATASET) -> BenchmarkDataset:
    """Load and validate one UTF-8 JSON benchmark dataset."""
    return BenchmarkDataset.model_validate_json(path.read_text(encoding="utf-8"))


def evaluate(dataset: BenchmarkDataset) -> BenchmarkResult:
    """Evaluate standard precision@k and mean reciprocal rank locally."""
    matcher = DeterministicMatcher()
    precision_at_1_sum = 0.0
    precision_at_3_sum = 0.0
    reciprocal_rank_sum = 0.0
    false_positives: list[FalsePositiveExample] = []
    false_negatives: list[FalseNegativeExample] = []

    for case in dataset.opportunities:
        ranking = matcher.match(case.tender, dataset.products)
        ranked_skus = [result.product.sku for result in ranking]
        relevant = set(case.relevant_skus)
        top_one = ranked_skus[:1]
        top_three = ranked_skus[:3]
        precision_at_1_sum += len(relevant.intersection(top_one))
        precision_at_3_sum += len(relevant.intersection(top_three)) / 3

        first_relevant_rank = next(
            (index for index, sku in enumerate(ranked_skus, start=1) if sku in relevant),
            None,
        )
        if first_relevant_rank is not None:
            reciprocal_rank_sum += 1 / first_relevant_rank

        if top_one and top_one[0] not in relevant and len(false_positives) < 5:
            false_positives.append(
                FalsePositiveExample(
                    opportunity_id=case.tender.id,
                    predicted_sku=top_one[0],
                    score=ranking[0].score,
                    relevant_skus=case.relevant_skus,
                )
            )

        for relevant_sku in case.relevant_skus:
            rank = ranked_skus.index(relevant_sku) + 1 if relevant_sku in ranked_skus else None
            if (rank is None or rank > 3) and len(false_negatives) < 5:
                false_negatives.append(
                    FalseNegativeExample(
                        opportunity_id=case.tender.id,
                        relevant_sku=relevant_sku,
                        rank=rank,
                    )
                )

    count = len(dataset.opportunities)
    return BenchmarkResult(
        product_count=len(dataset.products),
        opportunity_count=count,
        metrics=RankingMetrics(
            precision_at_1=round(precision_at_1_sum / count, 4),
            precision_at_3=round(precision_at_3_sum / count, 4),
            mrr=round(reciprocal_rank_sum / count, 4),
        ),
        false_positives=false_positives,
        false_negatives=false_negatives,
    )


def render_report(result: BenchmarkResult) -> str:
    """Render stable human-readable metrics and diagnostics."""
    lines = [
        "OpenTradeIntel synthetic matcher benchmark",
        f"Products: {result.product_count}",
        f"Opportunities: {result.opportunity_count}",
        f"precision@1: {result.metrics.precision_at_1:.4f}",
        f"precision@3: {result.metrics.precision_at_3:.4f}",
        f"MRR: {result.metrics.mrr:.4f}",
        "False-positive examples:",
    ]
    if result.false_positives:
        lines.extend(
            "  "
            f"{item.opportunity_id}: predicted {item.predicted_sku} "
            f"(score {item.score}); relevant {', '.join(item.relevant_skus)}"
            for item in result.false_positives
        )
    else:
        lines.append("  none at rank 1")
    lines.append("False-negative examples:")
    if result.false_negatives:
        lines.extend(
            f"  {item.opportunity_id}: {item.relevant_sku} ranked {item.rank or 'not ranked'}"
            for item in result.false_negatives
        )
    else:
        lines.append("  none below rank 3")
    return "\n".join(lines)


def main() -> None:
    """Run the committed dataset and print its reproducible baseline."""
    print(render_report(evaluate(load_dataset())))


if __name__ == "__main__":
    main()
