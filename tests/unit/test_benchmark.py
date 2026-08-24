from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmarks.run import (
    BenchmarkCase,
    BenchmarkDataset,
    evaluate,
    load_dataset,
    render_report,
)
from opentradeintel.models import Product, Tender

PROJECT_ROOT = Path(__file__).parents[2]
DATASET_PATH = PROJECT_ROOT / "benchmarks" / "dataset.json"


def tied_product(sku: str) -> Product:
    return Product(
        sku=sku,
        name="Standard widget",
        description="Synthetic benchmark item.",
        category="Widget",
        origin="Exampleland",
        min_order_quantity=Decimal("1"),
        keywords=["widget"],
    )


def tied_tender(case_id: str) -> Tender:
    return Tender(
        id=case_id,
        title="Standard widget",
        buyer="Synthetic Benchmark Buyer",
        description="Widget procurement.",
        quantity=Decimal("10"),
        source="synthetic-benchmark",
    )


def test_evaluate_uses_standard_precision_and_reciprocal_rank() -> None:
    dataset = BenchmarkDataset(
        products=[tied_product(sku) for sku in ["A", "B", "C", "D"]],
        opportunities=[
            BenchmarkCase(tender=tied_tender("case-1"), relevant_skus=["A"]),
            BenchmarkCase(tender=tied_tender("case-2"), relevant_skus=["D"]),
        ],
    )

    result = evaluate(dataset)

    assert result.metrics.model_dump() == {
        "precision_at_1": 0.5,
        "precision_at_3": 0.1667,
        "mrr": 0.625,
    }
    assert result.false_positives[0].model_dump() == {
        "opportunity_id": "case-2",
        "predicted_sku": "A",
        "score": 100,
        "relevant_skus": ["D"],
    }
    assert result.false_negatives[0].model_dump() == {
        "opportunity_id": "case-2",
        "relevant_sku": "D",
        "rank": 4,
    }


def test_committed_benchmark_has_minimum_size_and_only_synthetic_records() -> None:
    dataset = load_dataset(DATASET_PATH)

    assert len(dataset.opportunities) >= 20
    assert len(dataset.products) >= 30
    assert len({case.tender.id for case in dataset.opportunities}) == len(dataset.opportunities)
    assert len({product.sku for product in dataset.products}) == len(dataset.products)
    assert all(case.tender.source == "synthetic-benchmark" for case in dataset.opportunities)


def test_committed_benchmark_output_is_reproducible() -> None:
    dataset = load_dataset(DATASET_PATH)

    first = render_report(evaluate(dataset))
    second = render_report(evaluate(dataset))

    assert first == second
    assert "precision@1:" in first
    assert "precision@3:" in first
    assert "MRR:" in first
    assert "False-positive examples:" in first
    assert "False-negative examples:" in first


def test_benchmark_dataset_rejects_duplicate_product_skus() -> None:
    with pytest.raises(ValidationError, match="product SKUs must be unique"):
        BenchmarkDataset(
            products=[tied_product("A"), tied_product("A")],
            opportunities=[BenchmarkCase(tender=tied_tender("case-1"), relevant_skus=["A"])],
        )


def test_benchmark_dataset_rejects_duplicate_opportunity_ids() -> None:
    with pytest.raises(ValidationError, match="opportunity IDs must be unique"):
        BenchmarkDataset(
            products=[tied_product("A")],
            opportunities=[
                BenchmarkCase(tender=tied_tender("case-1"), relevant_skus=["A"]),
                BenchmarkCase(tender=tied_tender("case-1"), relevant_skus=["A"]),
            ],
        )


def test_benchmark_dataset_rejects_unknown_relevance_labels() -> None:
    with pytest.raises(ValidationError, match="references unknown SKUs: UNKNOWN"):
        BenchmarkDataset(
            products=[tied_product("A")],
            opportunities=[BenchmarkCase(tender=tied_tender("case-1"), relevant_skus=["UNKNOWN"])],
        )
