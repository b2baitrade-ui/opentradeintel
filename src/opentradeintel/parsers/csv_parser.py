"""CSV parsers with semicolon-separated list fields."""

import csv
import io
from pathlib import Path

from pydantic import ValidationError

from opentradeintel.errors import DataValidationError, ParseError
from opentradeintel.models import Product, Tender

TENDER_LIST_FIELDS = frozenset({"products", "required_certifications", "cpv_codes", "nuts_codes"})
PRODUCT_LIST_FIELDS = frozenset({"certifications", "available_markets", "keywords", "cpv_codes"})
OPTIONAL_SCALAR_FIELDS = frozenset(
    {
        "quantity",
        "unit",
        "destination",
        "deadline",
        "currency",
        "min_order_quantity",
        "source_id",
        "source_url",
        "estimated_value",
        "publication_date",
    }
)


def _rows(text: str, source: Path) -> list[dict[str, str | None]]:
    try:
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise ParseError(f"CSV source '{source}' has no header row")
        return list(reader)
    except csv.Error as error:
        raise ParseError(f"Invalid CSV in '{source}': {error}") from error


def _coerce_row(row: dict[str, str | None], list_fields: frozenset[str]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in row.items():
        if value is None:
            result[key] = [] if key in list_fields else None
        elif key in list_fields:
            result[key] = [part.strip() for part in value.split(";") if part.strip()]
        elif key in OPTIONAL_SCALAR_FIELDS and not value.strip():
            result[key] = None
        else:
            result[key] = value.strip()
    return result


class CSVTenderParser:
    """Parse a CSV document containing exactly one tender row."""

    def parse(self, text: str, source: Path) -> Tender:
        records = _rows(text, source)
        if len(records) != 1:
            raise ParseError(f"'{source}' must contain exactly one tender record")
        try:
            return Tender.model_validate(_coerce_row(records[0], TENDER_LIST_FIELDS))
        except ValidationError as error:
            raise DataValidationError(f"Invalid tender in '{source}', record 1: {error}") from error


class CSVCatalogParser:
    """Parse one product per CSV row."""

    def parse(self, text: str, source: Path) -> list[Product]:
        products: list[Product] = []
        for index, row in enumerate(_rows(text, source), start=1):
            try:
                products.append(Product.model_validate(_coerce_row(row, PRODUCT_LIST_FIELDS)))
            except ValidationError as error:
                raise DataValidationError(
                    f"Invalid product in '{source}', record {index}: {error}"
                ) from error
        return products
