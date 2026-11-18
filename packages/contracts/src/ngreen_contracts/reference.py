"""Load and check the supplied reference-account sheet.

The sheet is a list of research targets. It is not evidence that a company
buys packaging, uses plastic, or has given anyone permission to call.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ngreen_contracts.taxonomy import (
    DISTINCT_REFERENCE_TARGET_COUNT,
    EMPTY_REFERENCE_PRODUCTS,
    JSON_INDUSTRY_ALIASES,
    PRODUCT_HEADINGS,
    REFERENCE_REVIEW_LABEL,
    REFERENCE_SOURCE_ORIGIN,
    SEPARATE_BUSINESS_UNITS,
    normalize_company_name,
)


class ReferenceCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    warning: str = Field(min_length=1)
    industries: list[str]
    packaging_product_to_target_companies: dict[str, list[str]]
    distinct_reference_target_count: int
    distinct_reference_targets: list[str]
    currently_empty_reference_product_categories: list[str]

    @model_validator(mode="after")
    def check_invariants(self) -> ReferenceCatalog:
        products = self.packaging_product_to_target_companies
        if tuple(products) != PRODUCT_HEADINGS:
            raise ValueError(
                "product headings must match the 11 source headings, in order"
            )
        if self.distinct_reference_target_count != DISTINCT_REFERENCE_TARGET_COUNT:
            raise ValueError("distinct_reference_target_count must be 20")
        if len(self.distinct_reference_targets) != len(set(self.distinct_reference_targets)):
            raise ValueError("distinct_reference_targets contains a duplicate")
        if len(self.distinct_reference_targets) != DISTINCT_REFERENCE_TARGET_COUNT:
            raise ValueError("distinct_reference_targets must contain 20 names")

        observed: list[str] = []
        for product, companies in products.items():
            if len(companies) != len(set(companies)):
                raise ValueError(f"duplicate company under {product}")
            observed.extend(companies)
        if set(observed) != set(self.distinct_reference_targets):
            raise ValueError(
                "union of product lists does not match distinct_reference_targets"
            )

        empty = [
            product for product, companies in products.items() if len(companies) == 0
        ]
        if empty != list(EMPTY_REFERENCE_PRODUCTS):
            raise ValueError(f"unexpected empty product categories: {empty}")
        if self.currently_empty_reference_product_categories != list(EMPTY_REFERENCE_PRODUCTS):
            raise ValueError("currently_empty_reference_product_categories drifted")

        if self.industries != list(JSON_INDUSTRY_ALIASES):
            raise ValueError(
                "reference industry list must stay the alias list, not company assignments"
            )
        unknown_aliases = [
            name for name in self.industries if name not in JSON_INDUSTRY_ALIASES
        ]
        if unknown_aliases:
            raise ValueError(f"unmapped industry aliases: {unknown_aliases}")

        for left, right in SEPARATE_BUSINESS_UNITS:
            if left not in self.distinct_reference_targets:
                raise ValueError(f"missing business unit {left}")
            if right not in self.distinct_reference_targets:
                raise ValueError(f"missing business unit {right}")
            if normalize_company_name(left) == normalize_company_name(right):
                raise ValueError(f"{left} and {right} collapsed to the same name")
        return self

    def products_for(self, display_name: str) -> list[str]:
        return [
            product
            for product, companies in self.packaging_product_to_target_companies.items()
            if display_name in companies
        ]

    def targets(self) -> list[ReferenceTarget]:
        return [
            ReferenceTarget(
                display_name=name,
                normalized_name=normalize_company_name(name),
                product_hypotheses=self.products_for(name),
            )
            for name in self.distinct_reference_targets
        ]


class ReferenceTarget(BaseModel):
    """One seeded company. Industry is unset because the sheet does not assign one."""

    model_config = ConfigDict(extra="forbid")

    display_name: str
    normalized_name: str
    product_hypotheses: list[str] = Field(min_length=1)
    source_origin: str = REFERENCE_SOURCE_ORIGIN
    review_label: str = REFERENCE_REVIEW_LABEL
    industry_id: None = None
    need_status: str = "hypothesis"


def load_reference_catalog(path: Path) -> ReferenceCatalog:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ReferenceCatalog.model_validate(payload)
