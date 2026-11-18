"""Reference catalogue, manual CRM, and CSV import."""

from __future__ import annotations

from support import auth as _auth
from support import login as _login


def test_reference_sheet_is_twenty_unverified_targets_without_contacts(client) -> None:
    owner = _login(client, "owner@ngreen.demo")
    listing = client.get(
        "/api/v1/accounts?page_size=100&source_origin=reference_sheet",
        headers=_auth(owner),
    )
    assert listing.status_code == 200, listing.text
    body = listing.json()
    assert body["total"] == 20
    names = {item["display_name"] for item in body["items"]}
    assert names == {
        "Medplus",
        "Swiggy Instamart",
        "Zepto",
        "D mart",
        "Ratnadeep",
        "Big Basket",
        "Spencers",
        "More",
        "Ushodaya",
        "Vijetha",
        "Jio mart",
        "Spar Hypermarket",
        "Blinkit",
        "Zomato",
        "Amazon Fresh",
        "Flipkart Minutes",
        "Myntra",
        "Amazon",
        "Flipkart",
        "Sneha Chicken",
    }
    assert all(item["industry_id"] is None for item in body["items"])
    assert all(item["review_label"] == "Reference target – not verified" for item in body["items"])
    assert all(item["contact_count"] == 0 for item in body["items"])
    amazon = {
        item["display_name"]: item["id"]
        for item in body["items"]
        if "Amazon" in item["display_name"]
    }
    assert set(amazon) == {"Amazon", "Amazon Fresh"}

    products = client.get("/api/v1/products", headers=_auth(owner))
    assert products.status_code == 200
    catalog = {item["name"]: item["company_count"] for item in products.json()}
    assert len(catalog) == 11
    assert catalog["Stretch Films"] == 0
    assert catalog["Garment Bags"] == 0
    assert catalog["D Cut Bags"] == 0
    assert catalog["Industrial Packaging"] == 1

    industries = client.get("/api/v1/industries", headers=_auth(owner))
    assert len(industries.json()) == 17
    aliases = {
        alias
        for industry in industries.json()
        for alias in industry["aliases"]
    }
    assert "Q-Commerce" in aliases
    assert "Restaurants / Catering" not in aliases

    contacts = client.get("/api/v1/contacts", headers=_auth(owner))
    assert contacts.json()["total"] == 0

    fresh = next(item for item in body["items"] if item["display_name"] == "Amazon Fresh")
    detail = client.get(f"/api/v1/accounts/{fresh['id']}", headers=_auth(owner))
    assert detail.status_code == 200
    need_names = {need["product_name"] for need in detail.json()["needs"]}
    assert "Shrink Films" in need_names
    assert all(need["need_status"] == "hypothesis" for need in detail.json()["needs"])
    assert detail.json()["contacts"] == []


def test_manual_needs_require_a_source_before_they_leave_hypothesis(client) -> None:
    owner = _login(client, "owner@ngreen.demo")
    created = client.post(
        "/api/v1/accounts",
        headers=_auth(owner),
        json={
            "display_name": "Harbour Paper",
            "city": "Hyderabad",
            "product_names": ["Courier Bags", "Carry Bags"],
        },
    )
    assert created.status_code == 201, created.text
    account_id = created.json()["id"]
    needs = {need["product_name"]: need for need in created.json()["needs"]}
    assert set(needs) == {"Courier Bags", "Carry Bags"}
    assert all(need["need_status"] == "hypothesis" for need in needs.values())

    blocked = client.patch(
        f"/api/v1/accounts/{account_id}/product-needs/{needs['Courier Bags']['id']}",
        headers=_auth(owner),
        json={"need_status": "publicly_evidenced"},
    )
    assert blocked.status_code == 422

    sourced = client.patch(
        f"/api/v1/accounts/{account_id}/product-needs/{needs['Courier Bags']['id']}",
        headers=_auth(owner),
        json={
            "need_status": "publicly_evidenced",
            "evidence_note": "Staff note from a buyer meeting on 17 Nov 2026.",
        },
    )
    assert sourced.status_code == 200, sourced.text
    assert sourced.json()["need_status"] == "publicly_evidenced"


def test_outreach_stage_requires_permission_and_records_the_reason(client) -> None:
    sales = _login(client, "sales@ngreen.demo")
    researcher = _login(client, "researcher@ngreen.demo")
    created = client.post(
        "/api/v1/accounts",
        headers=_auth(researcher),
        json={"display_name": "Coastal Stores"},
    )
    account_id = created.json()["id"]
    opportunity_id = created.json()["opportunity_id"]
    denied = client.patch(
        f"/api/v1/opportunities/{opportunity_id}/stage",
        headers=_auth(researcher),
        json={"to_stage": "validated_account", "reason": "Researcher cannot move stages."},
    )
    assert denied.status_code == 403

    blocked = client.patch(
        f"/api/v1/opportunities/{opportunity_id}/stage",
        headers=_auth(sales),
        json={"to_stage": "outreach_eligible", "reason": "Trying to call without permission."},
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "permission_required"

    contact = client.post(
        "/api/v1/contacts",
        headers=_auth(sales),
        json={
            "company_id": account_id,
            "display_name": "Desk contact",
            "source_note": "Typed by staff from a business card they already hold.",
            "permission_basis": "recorded_consent",
        },
    )
    assert contact.status_code == 201, contact.text
    moved = client.patch(
        f"/api/v1/opportunities/{opportunity_id}/stage",
        headers=_auth(sales),
        json={"to_stage": "outreach_eligible", "reason": "Consent is on the contact record."},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["stage"] == "outreach_eligible"
    events = client.get(f"/api/v1/opportunities/{opportunity_id}/events", headers=_auth(sales))
    assert len(events.json()) == 2
    assert events.json()[-1]["reason"] == "Consent is on the contact record."

    sample = client.patch(
        f"/api/v1/opportunities/{opportunity_id}/stage",
        headers=_auth(sales),
        json={"to_stage": "sample_trial_requested", "reason": "Buyer asked for a sample."},
    )
    assert sample.status_code == 200
    tasks = client.get("/api/v1/tasks", headers=_auth(sales))
    assert any(item["title"] == "Review sample request" for item in tasks.json()["items"])


def test_csv_preview_reports_errors_and_commit_is_partial(client) -> None:
    owner = _login(client, "owner@ngreen.demo")
    sales = _login(client, "sales@ngreen.demo")
    before = client.get("/api/v1/accounts?page_size=1", headers=_auth(owner)).json()["total"]
    preview_body = {
        "csv_text": "\n".join(
            [
                "display_name,products",
                ",Carry Bags",
                "Bad Product Co,Not A Product",
                "Medplus,Carry Bags",
                "=Danger Mills,Carry Bags",
                "Fixture Twin,Carry Bags",
                "Fixture Twin,Carry Bags",
            ]
        )
    }
    denied = client.post("/api/v1/imports/preview", headers=_auth(sales), json=preview_body)
    assert denied.status_code == 403
    preview = client.post("/api/v1/imports/preview", headers=_auth(owner), json=preview_body)
    assert preview.status_code == 200, preview.text
    rows = {row["display_name"]: row for row in preview.json()["rows"]}
    assert preview.json()["rows"][0]["status"] == "error"
    assert preview.json()["rows"][0]["message"] == "Company name is empty."
    assert rows["Bad Product Co"]["status"] == "error"
    assert rows["Medplus"]["status"] == "duplicate"
    assert rows["=Danger Mills"]["status"] == "ready"
    assert preview.json()["duplicates"] >= 2
    after_preview = client.get("/api/v1/accounts?page_size=1", headers=_auth(owner)).json()["total"]
    assert after_preview == before

    commit = client.post(
        "/api/v1/imports/commit",
        headers=_auth(owner),
        json={
            "csv_text": "\n".join(
                [
                    "display_name,city,products",
                    "Fixture Partial Ok,Pune,Carry Bags",
                    "Fixture Partial Bad,Pune,Not A Real Product",
                ]
            ),
            "update_rows": [],
        },
    )
    assert commit.status_code == 200, commit.text
    report = commit.json()
    assert report["created"] == 1
    assert report["failed"] == 1
    saved = client.get("/api/v1/accounts?q=Fixture%20Partial%20Ok", headers=_auth(owner))
    assert saved.json()["total"] == 1
    missing = client.get("/api/v1/accounts?q=Fixture%20Partial%20Bad", headers=_auth(owner))
    assert missing.json()["total"] == 0


def test_csv_imports_fifty_fixtures_without_a_second_copy(client) -> None:
    owner = _login(client, "owner@ngreen.demo")
    header = "display_name,city,state,country,notes,products,tags,owner_email"
    lines = [header]
    for number in range(1, 51):
        lines.append(
            f"Fixture Buyer {number:02d},Hyderabad,Telangana,India,Fixture row,Carry Bags,fixture,"
        )
    csv_text = "\n".join(lines)
    first = client.post(
        "/api/v1/imports/commit",
        headers=_auth(owner),
        json={"csv_text": csv_text, "update_rows": []},
    )
    assert first.status_code == 200, first.text
    assert first.json()["created"] == 50
    assert first.json()["failed"] == 0
    second = client.post(
        "/api/v1/imports/commit",
        headers=_auth(owner),
        json={"csv_text": csv_text, "update_rows": []},
    )
    assert second.json()["created"] == 0
    assert second.json()["skipped"] == 50
    listing = client.get(
        "/api/v1/accounts?page_size=100&source_origin=csv_import", headers=_auth(owner)
    )
    assert listing.json()["total"] == 50

    tagged = client.get("/api/v1/accounts?tag=fixture&page_size=100", headers=_auth(owner))
    assert tagged.json()["total"] == 50
    industrial = client.get(
        "/api/v1/accounts?product=Industrial%20Packaging&page_size=100", headers=_auth(owner)
    )
    assert [item["display_name"] for item in industrial.json()["items"]] == ["Sneha Chicken"]


def test_export_prefixes_formula_cells(client) -> None:
    owner = _login(client, "owner@ngreen.demo")
    created = client.post(
        "/api/v1/accounts",
        headers=_auth(owner),
        json={"display_name": "=Danger Mills"},
    )
    assert created.status_code == 201, created.text
    exported = client.get("/api/v1/accounts/export?q=%3DDanger%20Mills", headers=_auth(owner))
    assert exported.status_code == 200
    assert "'=Danger Mills" in exported.text
    assert "\n=Danger Mills" not in exported.text
