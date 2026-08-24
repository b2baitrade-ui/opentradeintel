"""JSON parsers for tender and catalog records."""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from opentradeintel.errors import DataValidationError, ParseError
from opentradeintel.models import Product, Tender


def _decode(text: str, source: Path) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ParseError(
            f"Invalid JSON in '{source}' at line {error.lineno}, column {error.colno}"
        ) from error


def _records(payload: Any, wrapper: str, source: Path) -> list[Any]:
    if isinstance(payload, dict) and wrapper in payload:
        wrapped = payload[wrapper]
        if not isinstance(wrapped, list):
            raise ParseError(f"'{wrapper}' in '{source}' must be a JSON array")
        return wrapped
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ParseError(f"Top-level JSON in '{source}' must be an object or array")


class JSONTenderParser:
    """Parse a JSON document containing exactly one tender."""

    def parse(self, text: str, source: Path) -> Tender:
        records = _records(_decode(text, source), "tenders", source)
        if len(records) != 1:
            raise ParseError(f"'{source}' must contain exactly one tender record")
        try:
            return Tender.model_validate(records[0])
        except ValidationError as error:
            raise DataValidationError(f"Invalid tender in '{source}', record 1: {error}") from error


class JSONCatalogParser:
    """Parse a JSON product object, array, or products wrapper."""

    def parse(self, text: str, source: Path) -> list[Product]:
        records = _records(_decode(text, source), "products", source)
        products: list[Product] = []
        for index, record in enumerate(records, start=1):
            try:
                products.append(Product.model_validate(record))
            except ValidationError as error:
                raise DataValidationError(
                    f"Invalid product in '{source}', record {index}: {error}"
                ) from error
        return products
