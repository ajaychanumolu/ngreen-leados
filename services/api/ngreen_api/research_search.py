"""Search providers. An empty Serper key uses the DEMO fixture, never a silent live call."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

from ngreen_contracts.taxonomy import normalize_company_name

CANDIDATE_LABEL = "Research candidate – not a verified buyer"
DEMO_SNIPPET = (
    "DEMO search fixture. This is not evidence that the business buys packaging or uses plastic."
)
_FIXTURE_LABELS = ("North Depot", "South Stores", "Central Yard", "East Counter", "West Gate")


class ProviderOutage(Exception):
    """The search provider failed. Callers must store the error and invent nothing."""


@dataclass(frozen=True)
class Hit:
    title: str
    url: str
    snippet: str


_SELLER_MARKS = (
    "supplier",
    "manufacturer",
    "wholesaler",
    "we manufacture",
    "we supply",
    "packaging company",
    "exporters of",
    "customized",
    "bags for",
    "delivery bags",
    "paper bags",
    "packaging solutions",
)
_BUYER_MARKS = (
    "procurement",
    "looking for",
    "rfq",
    "we buy",
    "packaging requirement",
    "we need",
    "we use",
    "our stores",
    "customer",
)
_PLASTIC_ITEMS = (
    "garbage bags on rolls",
    "perforated rolls",
    "shrink films",
    "stretch films",
    "industrial packaging",
    "garment bags",
    "grocery bags",
    "garbage bags",
    "courier bags",
    "carry bags",
    "d cut bags",
    "plastic packaging",
    "plastic bags",
    "plastic pouches",
)
_SELLER_HOSTS = (
    "justdial.com",
    "indiamart.com",
    "tradeindia.com",
    "exportersindia.com",
    "alibaba.com",
    "made-in-china.com",
    "tenderkart.in",
    "indiantenders.in",
    "tendershark.com",
    "tendertiger.com",
    "bidassist.com",
    "wikipedia.org",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
)


def _customer_examples(industry: str | None) -> str:
    """Search terms for buyers. These names are not stored as leads by themselves."""
    low = (industry or "").casefold()
    if not low or "commerce" in low or "quick" in low:
        return 'zepto OR blinkit OR "swiggy instamart" OR retailer'
    if "hotel" in low or "hospitality" in low:
        return "hotel OR restaurant"
    if "super" in low or "hyper" in low or "fmcg" in low:
        return "supermarket OR hypermarket OR retailer"
    if "logistic" in low:
        return "logistics OR courier customer"
    if "pharma" in low:
        return "pharmacy OR hospital"
    return industry or "retailer"


def mentioned_plastic(text: str) -> list[str]:
    low = " ".join(text.split()).casefold()
    return [item for item in _PLASTIC_ITEMS if item in low]


def plan_queries(product: str, geography: str, industry: str | None, max_queries: int) -> list[str]:
    place = " ".join(geography.split()) or "India"
    audience = _customer_examples(industry)
    plastic = '"plastic bags" OR "plastic packaging" OR "carry bags" OR "courier bags"'
    drafted = [
        f"{audience} {plastic} {place} -supplier -manufacturer -wholesaler",
        (
            f'{audience} ("we use" OR using) "{product}" plastic {place} '
            "-supplier -manufacturer -wholesaler"
        ),
        (
            f"{audience} contact (email OR phone OR mobile) {place} "
            "-supplier -manufacturer -wholesaler"
        ),
    ]
    planned: list[str] = []
    for item in drafted:
        text = " ".join(item.split())[:300]
        if text not in planned:
            planned.append(text)
    return planned[:max_queries]


def looks_like_packaging_seller(title: str, snippet: str, domain: str) -> bool:
    """A packaging vendor or a seller directory is not a lead for N Green."""
    host = domain.casefold()
    if host.startswith("www."):
        host = host[4:]
    if any(host == mark or host.endswith("." + mark) for mark in _SELLER_HOSTS):
        return True
    text = f"{title} {snippet}".casefold()
    seller = any(mark in text for mark in _SELLER_MARKS)
    buyer = any(mark in text for mark in _BUYER_MARKS)
    return seller and not buyer


def public_domain(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return None
    host = (parsed.hostname or "").casefold().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host or host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
    ):
        return None
    return host


def content_hash(url: str, snippet: str) -> str:
    return hashlib.sha256(f"{url}\n{snippet}".encode()).hexdigest()


class DemoProvider:
    name = "demo"

    def search(self, query: str, limit: int) -> list[Hit]:
        hits: list[Hit] = []
        for index, label in enumerate(_FIXTURE_LABELS, start=1):
            if len(hits) >= limit:
                break
            slug = normalize_company_name(label).replace(" ", "-")
            hits.append(
                Hit(
                    title=f"DEMO {label}",
                    url=f"https://example.com/demo/research/{slug}",
                    snippet=DEMO_SNIPPET,
                )
            )
            del index
        del query
        return hits


class SerperProvider:
    """https://serper.dev/ — POST /search with header X-API-KEY. No page fetch."""

    name = "serper"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, limit: int) -> list[Hit]:
        if not self.api_key:
            raise ProviderOutage("SERPER_API_KEY is empty.")
        payload = json.dumps({"q": query, "num": limit, "gl": "in", "hl": "en"}).encode()
        request = urllib.request.Request(
            "https://google.serper.dev/search",
            data=payload,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raise ProviderOutage(f"Serper returned {exc.code}.") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderOutage("Serper could not be reached.") from exc
        hits: list[Hit] = []
        for item in body.get("organic") or []:
            if len(hits) >= limit:
                break
            url = str(item.get("link") or "")
            if public_domain(url) is None:
                continue
            title = str(item.get("title") or url)[:300]
            snippet = str(item.get("snippet") or "")[:1000]
            hits.append(Hit(title=title, url=url[:500], snippet=snippet))
        return hits


def provider_for(api_key: str) -> DemoProvider | SerperProvider:
    if api_key:
        return SerperProvider(api_key)
    return DemoProvider()
