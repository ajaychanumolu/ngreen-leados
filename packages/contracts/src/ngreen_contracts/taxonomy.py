"""Canonical taxonomies for N Green LeadOS.

Display names are preserved exactly. Normalized names are a separate field
and are never used to merge distinct business units.
"""

from __future__ import annotations

PRODUCT_HEADINGS: tuple[str, ...] = (
    "Carry Bags",
    "Grocery Bags",
    "Garbage Bags",
    "Garbage Bags on Rolls",
    "Perforated Rolls",
    "Courier Bags",
    "Shrink Films",
    "Stretch Films",
    "Industrial Packaging",
    "Garment Bags",
    "D Cut Bags",
)

# Products with no companies on the supplied reference sheet stay empty.
EMPTY_REFERENCE_PRODUCTS: tuple[str, ...] = (
    "Stretch Films",
    "Garment Bags",
    "D Cut Bags",
)

# Master specification section 3. The shorter strings in reference_accounts.json
# are aliases of these names, not a second industry list.
CANONICAL_INDUSTRIES: tuple[str, ...] = (
    "Q-Commerce / Quick Commerce",
    "E-Commerce",
    "Pharma",
    "Facility Management",
    "FMCG",
    "Logistics",
    "Supermarket / Hypermarket Chains",
    "Hotels / Hospitality",
    "Food Service / QSR / Cloud Kitchens",
    "Healthcare / Hospitals",
    "Retail Chains",
    "Fashion / Apparel / Textiles",
    "Manufacturing / Industrial",
    "Warehousing / Fulfilment",
    "Agriculture / Horticulture",
    "Restaurants / Catering",
    "Other",
)

# Keys are the industry strings in reference_accounts.json.
JSON_INDUSTRY_ALIASES: dict[str, str] = {
    "Q-Commerce": "Q-Commerce / Quick Commerce",
    "E-Commerce": "E-Commerce",
    "Pharma": "Pharma",
    "Facility Management": "Facility Management",
    "FMCG": "FMCG",
    "Logistics": "Logistics",
    "Supermarket / Hypermarket Chains": "Supermarket / Hypermarket Chains",
    "Hotels": "Hotels / Hospitality",
    "Food Service / QSR": "Food Service / QSR / Cloud Kitchens",
    "Healthcare": "Healthcare / Hospitals",
    "Retail": "Retail Chains",
    "Fashion / Apparel": "Fashion / Apparel / Textiles",
    "Manufacturing": "Manufacturing / Industrial",
    "Warehousing": "Warehousing / Fulfilment",
    "Agriculture": "Agriculture / Horticulture",
    "Other": "Other",
}

DISTINCT_REFERENCE_TARGET_COUNT = 20
REFERENCE_SOURCE_ORIGIN = "reference_sheet"
REFERENCE_REVIEW_LABEL = "Reference target – not verified"

# Business units that must stay separate even when the names share a brand.
SEPARATE_BUSINESS_UNITS: tuple[tuple[str, str], ...] = (
    ("Amazon", "Amazon Fresh"),
    ("Flipkart", "Flipkart Minutes"),
)


def normalize_company_name(display_name: str) -> str:
    """Case-fold and collapse whitespace. Does not strip brand tokens."""
    collapsed = " ".join(display_name.strip().split())
    if not collapsed:
        raise ValueError("display_name must not be empty")
    return collapsed.casefold()
