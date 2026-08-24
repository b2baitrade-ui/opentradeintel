"""Explainable result contracts returned by every public interface."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from opentradeintel.models.domain import Product, Tender


class ScoreBreakdown(BaseModel):
    """The five bounded components of a deterministic match score."""

    model_config = ConfigDict(extra="forbid")

    product_similarity: int = Field(ge=0, le=40)
    category: int = Field(ge=0, le=15)
    certifications: int = Field(ge=0, le=20)
    market: int = Field(ge=0, le=15)
    moq: int = Field(ge=0, le=10)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> int:
        """Return the exact total of all score components."""
        return (
            self.product_similarity + self.category + self.certifications + self.market + self.moq
        )


class MatchResult(BaseModel):
    """A ranked product plus human-readable score evidence."""

    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    product: Product
    reasons: list[str]
    warnings: list[str]
    breakdown: ScoreBreakdown

    @model_validator(mode="after")
    def score_matches_breakdown(self) -> Self:
        """Prevent interfaces from presenting a score inconsistent with its evidence."""
        if self.score != self.breakdown.total:
            raise ValueError("score must equal the score breakdown total")
        return self


class MatchResponse(BaseModel):
    """Shared response returned by the service, API, and MCP adapter."""

    model_config = ConfigDict(extra="forbid")

    tender: Tender
    matches: list[MatchResult]
