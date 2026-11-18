"""Reference sheet invariants. These names are hypotheses, not customers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ngreen_contracts.reference import load_reference_catalog
from ngreen_contracts.taxonomy import (
    CANONICAL_INDUSTRIES,
    JSON_INDUSTRY_ALIASES,
    SEPARATE_BUSINESS_UNITS,
    normalize_company_name,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "reference_accounts.json"
KIT_PATH = ROOT / "reference_accounts.json"


@pytest.fixture(scope="module")
def catalog():
    return load_reference_catalog(DATA_PATH)


def test_kit_copy_matches_data_copy() -> None:
    kit = json.loads(KIT_PATH.read_text(encoding="utf-8"))
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert kit == data


def test_twenty_distinct_targets_and_eleven_products(catalog) -> None:
    assert catalog.distinct_reference_target_count == 20
    assert len(catalog.targets()) == 20
    assert len(catalog.packaging_product_to_target_companies) == 11
    normalized = [item.normalized_name for item in catalog.targets()]
    assert len(normalized) == len(set(normalized))


def test_empty_products_stay_empty(catalog) -> None:
    products = catalog.packaging_product_to_target_companies
    assert products["Stretch Films"] == []
    assert products["Garment Bags"] == []
    assert products["D Cut Bags"] == []


def test_business_units_are_not_merged(catalog) -> None:
    names = set(catalog.distinct_reference_targets)
    for left, right in SEPARATE_BUSINESS_UNITS:
        assert left in names and right in names
        assert normalize_company_name(left) != normalize_company_name(right)


def test_every_target_is_a_hypothesis_without_an_industry(catalog) -> None:
    for target in catalog.targets():
        assert target.source_origin == "reference_sheet"
        assert target.review_label == "Reference target – not verified"
        assert target.need_status == "hypothesis"
        assert target.industry_id is None
        assert target.product_hypotheses


def test_known_product_rows_match_the_sheet(catalog) -> None:
    products = catalog.packaging_product_to_target_companies
    assert "Jio mart" in products["Carry Bags"]
    assert "Jio mart" not in products["Grocery Bags"]
    assert "Spar Hypermarket" in products["Carry Bags"]
    assert "Spar Hypermarket" not in products["Garbage Bags"]
    assert "Zomato" in products["Shrink Films"]
    assert "Zomato" not in products["Garbage Bags on Rolls"]
    assert products["Courier Bags"] == ["Medplus", "Myntra", "Amazon", "Flipkart"]
    assert products["Industrial Packaging"] == ["Sneha Chicken"]
    assert "Amazon" not in products["Carry Bags"]
    assert "Amazon Fresh" in products["Carry Bags"]
    assert "Flipkart" not in products["Grocery Bags"]
    assert "Flipkart Minutes" in products["Grocery Bags"]


def test_display_name_normalization_keeps_d_mart_spacing() -> None:
    assert normalize_company_name("D mart") == "d mart"
    assert normalize_company_name("  D   mart ") == "d mart"


def test_industry_aliases_cover_the_json_list_and_leave_one_canonical_unaliased() -> None:
    assert set(JSON_INDUSTRY_ALIASES.values()).issubset(set(CANONICAL_INDUSTRIES))
    missing = set(CANONICAL_INDUSTRIES) - set(JSON_INDUSTRY_ALIASES.values())
    assert missing == {"Restaurants / Catering"}


def test_sheet_contains_no_contact_or_volume_fields() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    forbidden = {"phone", "email", "revenue", "contact", "plastic_use", "volume"}
    assert forbidden.isdisjoint(payload.keys())
    assert "do not infer" in payload["warning"]
