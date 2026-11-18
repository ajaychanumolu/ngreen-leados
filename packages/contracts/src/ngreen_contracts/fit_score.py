"""Sales-research priority score. This is not a probability of winning."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FitScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    industry_alignment: int = Field(ge=0, le=25)
    product_fit: int = Field(ge=0, le=25)
    operational_scale: int = Field(ge=0, le=15)
    geography_supply: int = Field(ge=0, le=10)
    buyer_relevant_evidence: int = Field(ge=0, le=20)
    source_freshness: int = Field(ge=0, le=5)

    @property
    def total(self) -> int:
        return (
            self.industry_alignment
            + self.product_fit
            + self.operational_scale
            + self.geography_supply
            + self.buyer_relevant_evidence
            + self.source_freshness
        )

    @model_validator(mode="after")
    def total_cannot_exceed_100(self) -> FitScoreBreakdown:
        if self.total > 100:
            raise ValueError("fit score total cannot exceed 100")
        return self


class FitScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    breakdown: FitScoreBreakdown
    reasons: list[str] = Field(min_length=1)
    label: str = "sales research priority — not a conversion probability"

    @property
    def total(self) -> int:
        return self.breakdown.total


def unscored(reason: str) -> FitScore:
    """Missing evidence scores zero. It is not a hidden default of 50."""
    return FitScore(
        breakdown=FitScoreBreakdown(
            industry_alignment=0,
            product_fit=0,
            operational_scale=0,
            geography_supply=0,
            buyer_relevant_evidence=0,
            source_freshness=0,
        ),
        reasons=[reason],
    )
