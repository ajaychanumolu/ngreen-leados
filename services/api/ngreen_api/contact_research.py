"""Official public business channels only. A listing is not permission to call."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.models import Company, Contact, UsageEvent
from ngreen_api.research_search import SerperProvider, public_domain
from ngreen_api.settings import get_settings

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
_PHONE_WORDS = ("phone", "mobile", "call", "tel", "contact", "whatsapp")
_BLOCKED_HOSTS = (
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "apollo.io",
    "zoominfo.com",
    "lusha.com",
    "rocketreach.co",
    "signalhire.com",
    "naukri.com",
    "glassdoor.com",
    "justdial.com",
    "wikipedia.org",
)
_PERSONAL_EMAIL = (
    "gmail.com",
    "yahoo.com",
    "yahoo.co.in",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "rediffmail.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
)
PUBLIC_NOTE = "Public business email from an official page. This is not permission to call."
PHONE_NOTE = "Public mobile from an official page. This is not permission to call."
BOTH_NOTE = "Public email and mobile from an official page. This is not permission to call."
_STORED = "Stored public email or mobile. Permission stays unknown."


@dataclass(frozen=True)
class DiscoverResult:
    created: list[Contact]
    skipped_sources: int
    message: str


def discover_public_contacts(db: Session, company: Company, actor_id: uuid.UUID) -> DiscoverResult:
    settings = get_settings()
    if not settings.serper_api_key:
        return DiscoverResult(
            [],
            0,
            "DEMO contact search does not invent an email or a phone number.",
        )
    provider = SerperProvider(settings.serper_api_key)
    query = f"\"{company.display_name}\" official contact"
    hits = provider.search(query, 5)
    db.add(
        UsageEvent(
            organization_id=company.organization_id,
            run_id=None,
            kind="contact_search",
            units=1,
            mode="live",
        )
    )
    created: list[Contact] = []
    skipped = 0
    seen: set[str] = set()
    for hit in hits:
        found = business_emails(
            hit.title,
            hit.snippet,
            hit.url,
            company.display_name,
            company.canonical_domain,
        )
        phones = business_phones(
            hit.title,
            hit.snippet,
            hit.url,
            company.display_name,
            company.canonical_domain,
        )
        if not found and not phones:
            skipped += 1
            continue
        for email in found:
            if email in seen or _already_stored(db, company, email):
                continue
            seen.add(email)
            phone = phones[0] if phones else None
            phones = []
            contact = Contact(
                organization_id=company.organization_id,
                company_id=company.id,
                display_name=None,
                role_title="Public business channel",
                email=email,
                phone=phone,
                source_note=BOTH_NOTE if phone else PUBLIC_NOTE,
                source_url=hit.url[:500],
                checked_at=datetime.now(UTC),
                owner_user_id=actor_id,
                validity="unverified",
                permission_basis="unknown",
                channel_scope="both" if phone else "email",
                created_by=actor_id,
            )
            db.add(contact)
            created.append(contact)
            if len(created) >= 3:
                return DiscoverResult(created, skipped, _STORED)
        if phones and not _phone_stored(db, company, phones[0]):
            contact = Contact(
                organization_id=company.organization_id,
                company_id=company.id,
                display_name=None,
                role_title="Public business channel",
                email=None,
                phone=phones[0],
                source_note=PHONE_NOTE,
                source_url=hit.url[:500],
                checked_at=datetime.now(UTC),
                owner_user_id=actor_id,
                validity="unverified",
                permission_basis="unknown",
                channel_scope="phone",
                created_by=actor_id,
            )
            db.add(contact)
            created.append(contact)
            phones = []
            if len(created) >= 3:
                return DiscoverResult(created, skipped, _STORED)
    if not created:
        return DiscoverResult(
            created,
            skipped,
            "No official-domain email or mobile was in the search snippets.",
        )
    return DiscoverResult(created, skipped, _STORED)


def business_emails(
    title: str,
    snippet: str,
    url: str,
    company_name: str,
    company_domain: str | None,
) -> list[str]:
    page = public_domain(url)
    if page is None or _blocked(page):
        return []
    if company_domain and page != company_domain and not page.endswith(f".{company_domain}"):
        return []
    haystack = f"{title} {snippet}".casefold()
    if company_name.casefold() not in haystack:
        return []
    found: list[str] = []
    for match in _EMAIL.findall(snippet):
        email = match.strip(".").casefold()
        host = email.split("@", 1)[1]
        if _personal(host):
            continue
        if company_domain:
            official = company_domain
        else:
            official = page
        if host != official and not host.endswith(f".{official}"):
            continue
        if email not in found:
            found.append(email)
    return found


def business_phones(
    title: str,
    snippet: str,
    url: str,
    company_name: str,
    company_domain: str | None,
) -> list[str]:
    """A mobile is kept only when the snippet itself shows it on an official page."""
    page = public_domain(url)
    if page is None or _blocked(page):
        return []
    if company_domain and page != company_domain and not page.endswith(f".{company_domain}"):
        return []
    haystack = f"{title} {snippet}".casefold()
    if company_name.casefold() not in haystack:
        return []
    if not any(word in snippet.casefold() for word in _PHONE_WORDS):
        return []
    found: list[str] = []
    for match in _PHONE.findall(snippet):
        digits = re.sub(r"\D", "", match)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if len(digits) != 10:
            continue
        number = f"+91{digits}"
        if number not in found:
            found.append(number)
    return found[:2]


def channel_hash(organization_id: uuid.UUID, kind: str, value: str) -> str:
    material = f"{organization_id}|{kind}|{value.casefold().strip()}"
    return hashlib.sha256(material.encode()).hexdigest()


def _blocked(host: str) -> bool:
    return any(host == name or host.endswith(f".{name}") for name in _BLOCKED_HOSTS)


def _personal(host: str) -> bool:
    return any(host == name or host.endswith(f".{name}") for name in _PERSONAL_EMAIL)


def _already_stored(db: Session, company: Company, email: str) -> bool:
    existing = db.scalar(
        select(Contact.id).where(
            Contact.organization_id == company.organization_id,
            Contact.company_id == company.id,
            Contact.email == email,
        )
    )
    return existing is not None


def _phone_stored(db: Session, company: Company, phone: str) -> bool:
    existing = db.scalar(
        select(Contact.id).where(
            Contact.organization_id == company.organization_id,
            Contact.company_id == company.id,
            Contact.phone == phone,
        )
    )
    return existing is not None
