# N Green LeadOS — product requirements

Status: Phase 0. Approved for planning and skeleton only.
Date: 17 November 2026.
Source of truth: `MASTER_PROMPT.md`. This PRD reconciles that specification with the files actually present in the repository.

## 1. Product

N Green LeadOS is a B2B sales-research application for one Indian sustainable-packaging manufacturer. Staff use it to:

1. Keep a catalogue of packaging products N Green can talk about.
2. Hold companies that might buy those products, from two origins: a manual/CSV list, and later a sourced web search.
3. Review evidence before a company becomes a CRM account.
4. Record public business contacts and a separate permission to place an automated promotional call.
5. Run a mocked calling assistant first. Live calling stays off until a later, explicit approval.
6. Track opportunities, tasks, and reports from rows in the database.

A company name in the reference sheet is a research target. It is not proof of plastic use, revenue, a buyer, a phone number, or intent to purchase.

## 2. What this version is not

Out of scope, including the longer packaging-operations vision described as a future PDF topic:

- Factory ERP, capacity planning, production orders, and inventory.
- Government EPR filing.
- Omnichannel marketing, WhatsApp sends, and LinkedIn scraping.
- Automated cold calls to numbers harvested from the web.
- A general web-browsing agent.
- Claims that a prospect "currently uses plastic" or that a material is certified, unless a stored source or a buyer statement says so.
- Multi-organization SaaS. The schema keeps `organization_id` so a second tenant is possible later. The pilot is one organization: N Green.

Phase 10 (quotes, samples, stock, procurement, compliance integrations) is not in this build. The data model should leave room for an external reference on an opportunity, and nothing more.

## 3. Personas

| Role | Can do | Cannot do |
| --- | --- | --- |
| Owner/Admin | Everything staff can do, plus taxonomy, roles, budgets, integrations, audit | Place a live call with the provider flag off |
| Researcher/Analyst | Discovery runs, evidence review, merge/reject, manual company data | Authorize a live call |
| Sales/BD Executive | Assigned accounts, notes, tasks, CRM stage, calls when permission and the live flag allow | Change org-wide integrations |
| Manager | Quality review, assignment, calling-eligibility approval, analytics | Skip the permission check |
| Read-only stakeholder | Dashboards | Edit, import, or call |

Server-side checks enforce this. Hiding a button is not the control.

## 4. Inputs actually reviewed

| Input | Result |
| --- | --- |
| `MASTER_PROMPT.md` | Read. Governs scope, taxonomies, phases, and safety rules. |
| `PHASE_BY_PHASE_PROMPTS.md` | Read. Phase 0 is the only authorized build step. |
| `README_START_HERE.md` | Read. Confirms the kit is a prompt pack, not an application. |
| `reference_accounts.json` | Read and copied to `data/reference_accounts.json`. Validated by tests. |
| N Green PDF | Not in the workspace. The master spec already says it is a longer-term vision and not proof of a software platform. No PDF claims were added. |
| Product screenshot | Not in the workspace. The JSON header says it was extracted from a screenshot dated 16 Nov 2026. Product rows below follow the JSON, which matches section 4 of the master spec. |
| `N_Green_LeadOS_MVP.zip` and any FastAPI/SQLite demo | Not in the workspace. No demo code was inspected, reused, or described beyond the master spec's own sentence that an earlier demo had no authentication. |
| Earlier HTML concepts | Not in the workspace. |
| Bizongo | Used only as the spec's aesthetic direction: light surfaces, clear hierarchy, compact tables, green accent. No pages, text, or assets were copied. |

## 5. Reference targets

Eleven product headings. Twenty distinct company names. Three products have no companies and stay empty: Stretch Films, Garment Bags, D Cut Bags.

Every row is `source_origin = reference_sheet`, `need_status = hypothesis`, industry unset. The UI label is **Reference target – not verified**.

Amazon and Amazon Fresh are different business units. Flipkart and Flipkart Minutes are different business units. Similar names are not merged because of a parent company. Display name and normalized name are stored separately (`D mart` normalizes to `d mart`).

| Company | Hypothesis products from the sheet | Industry |
| --- | --- | --- |
| Medplus | Carry Bags; Garbage Bags; Garbage Bags on Rolls; Courier Bags | Unassigned |
| Swiggy Instamart | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Shrink Films | Unassigned |
| Zepto | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls | Unassigned |
| D mart | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| Ratnadeep | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| Big Basket | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Shrink Films | Unassigned |
| Spencers | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| More | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| Ushodaya | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| Vijetha | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| Jio mart | Carry Bags | Unassigned |
| Spar Hypermarket | Carry Bags | Unassigned |
| Blinkit | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Perforated Rolls | Unassigned |
| Zomato | Carry Bags; Grocery Bags; Garbage Bags; Shrink Films | Unassigned |
| Amazon Fresh | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Shrink Films | Unassigned |
| Flipkart Minutes | Carry Bags; Grocery Bags; Garbage Bags; Garbage Bags on Rolls; Shrink Films | Unassigned |
| Myntra | Courier Bags | Unassigned |
| Amazon | Courier Bags | Unassigned |
| Flipkart | Courier Bags | Unassigned |
| Sneha Chicken | Industrial Packaging | Unassigned |

The JSON file also lists sixteen short industry names. Those are aliases of the seventeen canonical industries in the master spec. They are not assignments of these companies. `Restaurants / Catering` is canonical and has no alias in the JSON. See `docs/DECISIONS.md`.

## 6. Main flows

Research path, later phases:

`Search plan → provider search → candidate → dedupe → evidence review → approved account → permitted contact → demo or live call → human-reviewed insight → CRM stage → report`

Manual path, Phase 2:

`Form or CSV → validation preview → duplicate review → CRM or research queue`

Rules that bind both paths:

- A researched candidate is not an active CRM account until a person approves it.
- Unknown calling permission means do not call. A public web listing is not permission.
- A call marked do-not-call suppresses future outreach.
- Replaying the same provider event must not create a second task or a second stage change.
- No call result can set an opportunity to Won by itself.
- Demo provider results are labeled DEMO. A provider error is shown as an error.

## 7. Fit score

The score is a sales-research priority from 0 to 100, with the caps in the master spec (25 / 25 / 15 / 10 / 20 / 5). Missing evidence scores 0 for that component. The score is not a probability of conversion and is not a validation that the company buys packaging.

## 8. Calling

Phase 6 is a mock voice provider only. Phase 7 may add a real adapter behind `VOICE_LIVE_ENABLED`, default `false`. A live attempt still rechecks permission at execution time. Indian promotional calling needs a qualified reading of TRAI TCCCPR and the provider's own rules before any real dial. This product does not implement a bypass.

The structured call result is the `CallInsight` model in `packages/contracts`. Product phrases outside the eleven headings are stored as `unmapped:` plus the raw phrase.

## 9. Success, for a later pilot

The funnel to measure, once the database exists:

researched candidates → validated accounts → permissioned calls → engaged buyers → meetings → samples or quotes → won orders.

Phase 0 has none of these counts. The overview wireframe shows an em dash, not a sample number.

## 10. Acceptance scenarios and the phase that owns them

| # | Scenario | Phase |
| --- | --- | --- |
| 1 | Sign-in and role-appropriate data | 1 |
| 2 | 20 reference targets, no invented contacts | 2 |
| 3 | Manual company, hypothesis changed to sourced | 2 |
| 4 | CSV preview, row errors, partial failure | 2 |
| 5 | Search shows links and hypotheses | 3, extraction in 4 |
| 6 | Provider outage is an error | 3 |
| 7 | Same domain suggests a duplicate; business units stay separate | 3 |
| 8 | Unknown consent cannot enter a live queue | 5, gate already encoded |
| 9 | Mock "interested" creates a reviewable insight and a task | 6 |
| 10 | Mock "never contact me" suppresses and blocks | 6 |
| 11 | Replay one webhook, one activity | 6 |
| 12 | Admin audit, usage, citations, provider errors | 8 and 9 |
| 13 | No API keys, local demo still runs | 3 and 6, skeleton flag in Phase 0 |

## 11. Phase 0 outcome

Delivered: this PRD, architecture, ERD, security notes, decisions, phase plan, screen plan, API plan, reference-data contracts, and tests. Not delivered: login, database tables, pages that fetch data, search, or calls.
