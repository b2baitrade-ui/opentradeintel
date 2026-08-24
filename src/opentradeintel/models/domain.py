"""Domain models for tenders and supplier products."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveDecimal = Annotated[Decimal, Field(gt=0)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


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

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        """Trim and uppercase an optional ISO-style currency code."""
        if isinstance(value, str):
            return value.strip().upper()
        return value


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
