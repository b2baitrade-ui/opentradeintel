"""Domain models for tenders and supplier products."""

import re
from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveDecimal = Annotated[Decimal, Field(gt=0)]
NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


def _unique_codes(
    codes: list[str],
    pattern: str,
    label: str,
    *,
    strip_cpv_check_digit: bool = False,
) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_code in codes:
        code = raw_code.strip().upper()
        if strip_cpv_check_digit and re.fullmatch(r"\d{8}-\d", code):
            code = code[:8]
        if not re.fullmatch(pattern, code):
            raise ValueError(f"invalid {label} code: {raw_code}")
        if code not in seen:
            normalized.append(code)
            seen.add(code)
    return normalized


class Tender(BaseModel):
    """A normalized procurement request or request for quotation."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    title: NonEmptyString
    buyer: NonEmptyString
    description: NonEmptyString
    products: list[NonEmptyString] = Field(default_factory=list)
    quantity: PositiveDecimal | None = None
    unit: NonEmptyString | None = None
    destination: NonEmptyString | None = None
    deadline: date | None = None
    currency: CurrencyCode | None = None
    required_certifications: list[NonEmptyString] = Field(default_factory=list)
    source: NonEmptyString
    source_id: NonEmptyString | None = None
    source_url: NonEmptyString | None = None
    cpv_codes: list[NonEmptyString] = Field(default_factory=list)
    nuts_codes: list[NonEmptyString] = Field(default_factory=list)
    estimated_value: NonNegativeDecimal | None = None
    publication_date: date | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        """Trim and uppercase an optional ISO-style currency code."""
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("cpv_codes", mode="after")
    @classmethod
    def normalize_cpv_codes(cls, value: list[str]) -> list[str]:
        """Normalize TED-style CPV codes and discard verification digits."""
        return _unique_codes(value, r"\d{8}", "CPV", strip_cpv_check_digit=True)

    @field_validator("nuts_codes", mode="after")
    @classmethod
    def normalize_nuts_codes(cls, value: list[str]) -> list[str]:
        """Uppercase and deduplicate general place-of-performance codes."""
        return _unique_codes(value, r"[A-Z0-9-]{2,10}", "NUTS")


class Product(BaseModel):
    """A supplier catalog product that can be matched to a tender."""

    model_config = ConfigDict(extra="forbid")

    sku: NonEmptyString
    name: NonEmptyString
    description: NonEmptyString
    category: NonEmptyString
    origin: NonEmptyString
    certifications: list[NonEmptyString] = Field(default_factory=list)
    min_order_quantity: PositiveDecimal | None = None
    available_markets: list[NonEmptyString] = Field(default_factory=list)
    keywords: list[NonEmptyString] = Field(default_factory=list)
    cpv_codes: list[NonEmptyString] = Field(default_factory=list)

    @field_validator("cpv_codes", mode="after")
    @classmethod
    def normalize_cpv_codes(cls, value: list[str]) -> list[str]:
        """Normalize supplier CPV codes for exact deterministic comparison."""
        return _unique_codes(value, r"\d{8}", "CPV", strip_cpv_check_digit=True)
