"""Parser protocols for future format extensions."""

from pathlib import Path
from typing import Protocol

from opentradeintel.models import Product, Tender


class TenderParser(Protocol):
    """Convert raw source text into one tender."""

    def parse(self, text: str, source: Path) -> Tender:
        """Parse and validate one tender record."""
        ...


class CatalogParser(Protocol):
    """Convert raw source text into a product catalog."""

    def parse(self, text: str, source: Path) -> list[Product]:
        """Parse and validate zero or more product records."""
        ...
