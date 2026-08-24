"""HTTP-only request and small response schemas."""

from pydantic import BaseModel, ConfigDict, Field

from opentradeintel.models import Product, Tender


class HealthResponse(BaseModel):
    """Liveness response."""

    status: str


class VersionResponse(BaseModel):
    """Installed package version response."""

    version: str


class MatchRequest(BaseModel):
    """In-memory tender and catalog payload for deterministic matching."""

    model_config = ConfigDict(extra="forbid")

    tender: Tender
    products: list[Product]
    limit: int | None = Field(default=None, gt=0)
