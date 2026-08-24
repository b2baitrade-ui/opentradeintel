import json
from pathlib import Path

import pytest

from opentradeintel.collectors import LocalFileConnector
from opentradeintel.errors import (
    DataValidationError,
    ParseError,
    SourceReadError,
    UnsupportedFormatError,
)
from opentradeintel.parsers import load_catalog, load_tender


def tender_record() -> dict[str, object]:
    return {
        "id": "rfq-001",
        "title": "Organic dried mango",
        "buyer": "Synthetic Buyers Guild",
        "description": "Bulk dried mango slices",
        "products": ["dried mango"],
        "quantity": 20000,
        "unit": "kg",
        "destination": "Germany",
        "deadline": "2026-09-30",
        "currency": "EUR",
        "required_certifications": ["EU Organic"],
        "source": "synthetic-demo",
    }


def product_record(sku: str = "DM-500") -> dict[str, object]:
    return {
        "sku": sku,
        "name": "Dried Mango 500g",
        "description": "Unsweetened dried mango slices",
        "category": "Dried fruit",
        "origin": "Exampleland",
        "certifications": ["EU Organic", "HACCP"],
        "min_order_quantity": 500,
        "available_markets": ["EU", "Singapore"],
        "keywords": ["mango", "organic"],
    }


def write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_local_file_connector_reads_utf8_text(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    path.write_text('{"title": "mangó"}', encoding="utf-8")

    assert LocalFileConnector().read_text(path) == '{"title": "mangó"}'


def test_load_tender_accepts_single_json_object(tmp_path: Path) -> None:
    path = write_json(tmp_path / "tender.json", tender_record())

    tender = load_tender(path)

    assert tender.id == "rfq-001"
    assert tender.quantity == 20000


@pytest.mark.parametrize(
    "payload",
    [[tender_record()], {"tenders": [tender_record()]}],
)
def test_load_tender_accepts_single_record_json_containers(tmp_path: Path, payload: object) -> None:
    path = write_json(tmp_path / "tender.json", payload)

    assert load_tender(path).title == "Organic dried mango"


def test_load_tender_rejects_multiple_records(tmp_path: Path) -> None:
    path = write_json(tmp_path / "tender.json", [tender_record(), tender_record()])

    with pytest.raises(ParseError, match="exactly one tender"):
        load_tender(path)


def test_load_tender_accepts_csv_and_splits_lists(tmp_path: Path) -> None:
    path = tmp_path / "tender.csv"
    path.write_text(
        "id,title,buyer,description,products,quantity,unit,destination,deadline,currency,"
        "required_certifications,source\n"
        'rfq-001,Organic mango,Synthetic Buyers,Bulk order,"mango;dried fruit",20000,kg,'
        'Germany,2026-09-30,EUR,"EU Organic;HACCP",synthetic-demo\n',
        encoding="utf-8",
    )

    tender = load_tender(path)

    assert tender.products == ["mango", "dried fruit"]
    assert tender.required_certifications == ["EU Organic", "HACCP"]


def test_load_catalog_accepts_json_array_and_wrapper(tmp_path: Path) -> None:
    array_path = write_json(tmp_path / "array.json", [product_record()])
    wrapped_path = write_json(tmp_path / "wrapped.json", {"products": [product_record()]})

    assert load_catalog(array_path)[0].sku == "DM-500"
    assert load_catalog(wrapped_path)[0].sku == "DM-500"


def test_load_catalog_accepts_single_json_product(tmp_path: Path) -> None:
    path = write_json(tmp_path / "catalog.json", product_record())

    assert [product.sku for product in load_catalog(path)] == ["DM-500"]


def test_load_catalog_csv_splits_list_columns_and_parses_empty_moq(tmp_path: Path) -> None:
    path = tmp_path / "catalog.csv"
    path.write_text(
        "sku,name,description,category,origin,certifications,min_order_quantity,"
        "available_markets,keywords\n"
        'DM-500,Dried Mango,Dried slices,Dried fruit,Exampleland,"EU Organic;HACCP",,'
        '"EU;Singapore","mango;organic"\n',
        encoding="utf-8",
    )

    product = load_catalog(path)[0]

    assert product.certifications == ["EU Organic", "HACCP"]
    assert product.available_markets == ["EU", "Singapore"]
    assert product.keywords == ["mango", "organic"]
    assert product.min_order_quantity is None


def test_loader_treats_file_suffix_case_insensitively(tmp_path: Path) -> None:
    path = write_json(tmp_path / "tender.JSON", tender_record())

    assert load_tender(path).id == "rfq-001"


def test_loader_reports_missing_source_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(SourceReadError, match=r"missing\.json"):
        load_tender(path)


def test_loader_rejects_unsupported_format(tmp_path: Path) -> None:
    path = tmp_path / "tender.xlsx"
    path.write_text("not implemented", encoding="utf-8")

    with pytest.raises(UnsupportedFormatError, match=r"\.xlsx"):
        load_tender(path)


def test_json_parser_reports_malformed_input_with_filename(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ParseError, match=r"broken\.json"):
        load_catalog(path)


def test_catalog_validation_error_identifies_record_number(tmp_path: Path) -> None:
    invalid = product_record("")
    path = write_json(tmp_path / "catalog.json", [product_record(), invalid])

    with pytest.raises(DataValidationError, match=r"catalog\.json.*record 2"):
        load_catalog(path)
