# Decisions

Format: date, decision, why, consequence.

## D-001 — Repository root is the kit

Date: 2026-11-17.

The opened folder is the build kit. The product skeleton was added beside the prompt files instead of nesting a second `ngreen-leados/` repository. Prompt files stay unmodified so the next phase can still be checked against them.

## D-002 — Missing sources are gaps, not implied facts

Date: 2026-11-17.

The PDF, screenshot, earlier HTML, and `N_Green_LeadOS_MVP.zip` were not in the workspace. A search outside the workspace was not required to invent their contents. The master spec's statement that an older demo had no authentication is recorded as a document claim, not as a code review. No demo module was copied.

## D-003 — Reference sheet does not assign industries

Date: 2026-11-17.

`reference_accounts.json` lists industry aliases and a product-to-company map. It does not say which industry a company belongs to. Seeded targets keep `industry_id = null` until a person or a sourced claim sets it, with `manual`, `inferred`, or `source_verified`. Guessing "Zepto is Q-Commerce" in the seed would be an unsupported claim.

## D-004 — Canonical industries come from the master spec

Date: 2026-11-17.

Seventeen canonical names, including `Restaurants / Catering`, which the JSON omits. The sixteen JSON strings are aliases mapped in `JSON_INDUSTRY_ALIASES`. Admins can add aliases later. Product headings stay the eleven exact source strings.

## D-005 — Business units stay split

Date: 2026-11-17.

Amazon vs Amazon Fresh, and Flipkart vs Flipkart Minutes, are separate targets. Normalization case-folds and collapses whitespace only. It does not strip tokens like "Fresh" or "Minutes". A parent link requires evidence and a person.

## D-006 — Contracts package is not the generated client

Date: 2026-11-17.

`packages/contracts` holds hand-written Python models so Phase 0 can test rules without fake HTTP routes. Phase 1 puts the generated OpenAPI client in `packages/api-client` so generated files do not overwrite these models.

## D-007 — SQLAlchemy 2.1

Date: 2026-11-17.

Checked sqlalchemy.org on 17 Nov 2026: 2.1.9 is the current series and 2.0.58 is maintenance. The spec asked for SQLAlchemy 2.x. Phase 1 uses 2.1.9 after reading the 2.0 to 2.1 notes, with Alembic 1.20.1.

## D-008 — Python and Node versions

Date: 2026-11-17.

CI for this phase targets Python 3.12. The workstation only has Python 3.14.7, and the Phase 0 unit tests ran there. FastAPI 0.163.1 requires Python >= 3.11 and documents 3.15 support, so 3.14 is acceptable for the contract tests. Phase 1 should still install 3.12 or 3.13 if a wheel is missing, and keep CI on 3.12 until that choice is revisited.

Node on the workstation is v24.21.0. Node.js published security releases on 11 Nov 2026: 26.13.1 (current LTS), 24.22.3, and 22.23.5. Phase 1 should use Node 26.13.1. pnpm and Docker were not installed; they are Phase 1 prerequisites, not Phase 0 blockers.

## D-009 — Zod is unresolved

Date: 2026-11-17.

npm listed Zod 4.6.7. The spec pairs React Hook Form with Zod, and many resolver examples still target Zod 3. Phase 1 verifies the combination before locking the major version.

## D-010 — Live voice default off

Date: 2026-11-17.

`.env.example` sets `VOICE_LIVE_ENABLED=false` and leaves provider keys empty. Eligibility tests cover unknown permission, disabled flag, wrong role, DNC, suppression, revoke, and expiry. The fixture number `+910000000000` is a format sample, not a person.

## D-011 — No stub product API

Date: 2026-11-17.

The spec says routes should come from delivered behavior rather than stub endpoints. Phase 0 therefore has no FastAPI app and no Next.js app. The screen plan is a static HTML file labeled as not the application.

## D-012 — Design reference is not a copy

Date: 2026-11-17.

Visual direction is a light cream surface, forest green, and compact tables, which the spec describes. Bizongo was not scraped and no layout, sentence, or asset from that site is in the repo. Tokens used in the Phase 0 wireframe: ink `#14241c`, forest `#1b4332`, leaf `#2d6a4f`, cream `#f6f3ec`.

## D-013 — Phase 1 UI follows the measured reference page

Date: 2026-11-17.

The live page at https://www.bizongo.com/ was measured in a browser, not copied. Computed values used for the staff UI:

- page `#ffffff`, text `#000000`
- quiet panels `#f5f5f5` and `#f9f9f9`
- primary button `#158aff`, label `#f9f9f9`, radius 0, uppercase, weight 700, padding 12.8px 24px
- body face Open Sans

Headlines on that site use Greycliff CF, a commercial face. The app uses Manrope for headings and does not embed their font files. The N Green name, sentences, and wordmark are original. Their logo, photography, partner marks, and sentences are not in the repo. The staff sidebar is part of the Phase 1 shell; the reference homepage does not have one, so the sidebar stays white with black type and a gray active row.

## D-014 — SQLite when Docker is missing

Date: 2026-11-17.

Docker is not installed on the build machine. The default `DATABASE_URL` is a local SQLite file so sign-in and account edits actually persist. Alembic revision `0001_foundation` is the Postgres-oriented migration and was applied to SQLite in tests. `infra/docker-compose.yml` is unchanged for when Docker exists. The UI says "local database" when the driver is SQLite.

## D-015 — DEMO sign-in until Supabase exists

Date: 2026-11-17.

`SUPABASE_URL` is empty. `POST /api/v1/auth/demo/login` checks a seeded password hash and returns an HS256 token with issuer `ngreen-leados-demo`. Application role is loaded from `memberships`. When `SUPABASE_URL` is set, tokens from that issuer are verified with the project JWKS (RS256/ES256 only). There is no public registration.

## D-016 — Phase 2 stays on the local SQLite file

Date: 2026-11-17.

Docker is still not installed, so the running app keeps `sqlite:///./data/local-leados.db`. Alembic revision `0002_crm` creates the catalogue, needs, contacts, opportunities, tasks, and import tables, and was upgraded on SQLite in tests. Startup also adds any missing company columns on an existing SQLite file, because `create_all` does not alter tables that already exist. Postgres remains the Compose target.

## D-017 — Reference targets are hypotheses with no contacts

Date: 2026-11-17.

Startup loads 11 products, 17 canonical industries, 16 aliases, and 20 companies from `data/reference_accounts.json`. Each company gets product needs at `hypothesis`, industry left unset, review label `Reference target – not verified`, and one opportunity at Research with no value. No contact rows are created. Amazon and Amazon Fresh stay separate, as do Flipkart and Flipkart Minutes.

## D-018 — CSV writes only after preview, and formulas are neutralized

Date: 2026-11-17.

`POST /api/v1/imports/preview` does not write. Commit rechecks every row, skips duplicates unless that row number is chosen for update, and records created, updated, skipped, and failed counts. Export prefixes a cell that starts with `=`, `+`, `-`, `@`, tab, or carriage return with a single quote. Outreach Eligible is rejected until the company has a contact whose permission basis is not `unknown`. No provider key is required for this phase.

## D-019 — The supplied N Green marks are the staff-UI logos

Date: 2026-11-17.

The client supplied a geometric N mark and a green wordmark reading N GREEN / SUSTAINABLE PACKAGING. Those files are `apps/web/public/brand/mark.png` (favicon) and `apps/web/public/brand/wordmark.png` (sidebar and login). The earlier note that a reference site's logo was not copied still stands. This is the client's own mark.

## D-020 — Discovery stores search hits and does not fetch the pages

Date: 2026-11-17.

An empty `SERPER_API_KEY` selects the DEMO adapter. Its titles are fixed fixtures and its links are on example.com, with a snippet that says they are not evidence of packaging use. A key selects Serper only. A provider error fails the run and stores no invented companies. The local worker is an in-process thread (`RESEARCH_WORKER=inline`) because Docker and Redis are not running. `redis` is available when Dramatiq and Redis are installed; if that handoff fails, the same thread runs the job and the failure is not hidden as a successful live search. Result URLs are not fetched. Hosts that are loopback, private, link-local, or reserved are dropped. Approving a candidate creates an account with industry unset, a hypothesis product need, and no contacts. A duplicate must be merged.

## D-021 — The header mark is type, not the soft wordmark file

Date: 2026-11-17.

The supplied wordmark PNG is 132×45 and looks soft at header size. The shell and login page now use a 34px green badge with a vector N, “N Green” in Bricolage Grotesque, and “Sustainable Packaging” in IBM Plex Mono. The badge green is sampled from the wordmark (`#307830`). The PNG remains in `public/brand` and is not shown in the header.

## D-022 — Scores cite snippets, and known leads are not searched again

Date: 2026-11-17.

A later run skips a company whose normalized name or earlier research identity is already stored. Fit points are awarded only when the quote is a substring of a stored snippet. Instruction-like sentences and quotes the model invents are dropped. A contradicting snippet keeps those points at zero. Empty `AI_API_KEY` uses the mock extractor. `AI_PROVIDER=openai` with a key calls the chat completions API, and the same quote check still applies. The score is a research priority, not a purchase.

## D-023 — Public business emails are not permission to call

Date: 2026-11-17.

Contact research stores an email only when it appears in a search snippet on that mailbox's own public site. Personal webmail, directory hosts, and login-gated profiles are dropped. Phone numbers are not taken from search. Permission stays `unknown`. Opt-out writes a hash, not the raw address, and a later permission grant cannot override it. `evaluate_live_call` is the only eligibility check, and `VOICE_LIVE_ENABLED` defaults to false, so no contact can be dialed. Groq is an optional chat provider at `api.groq.com`; a model error is stored and is not replaced with a mock success.

## D-024 — Search for packaging buyers, and rehearse calls offline

Date: 2026-11-17.

Search queries ask for procurement, tenders, and retailers, hotels, restaurants, and supermarkets. They exclude supplier, manufacturer, and wholesaler wording. Directory hosts such as Justdial and IndiaMART are not stored as leads. A DEMO rehearsal never dials. The transcript parser proposes an outcome, and a person accepts it before the CRM stage or a follow-up task is written. Do-not-call is immediate. A webhook without the shared secret is rejected, and the same provider call id plus event id is stored once.

## D-027 — Erasure keeps the suppression hash and drops the transcript

Date: 2026-11-17.

An owner or a manager can export one contact and then erase it. Erasure deletes the address, phone, permission rows, and rehearsal transcript. The audit summary names the action and does not copy the address. The channel hash stays, so a later row with the same address cannot be rehearsed. SQLite backup uses the database backup API. Staging was not deployed because that was not authorized.

## D-026 — Reports divide stored credits and do not forecast revenue

Date: 2026-11-17.

The funnel, stage age, yield, fit average, team load, overdue list, and spend log are queries. Search credits divided by stored or approved candidates are provider units. The ratio is null when that count is zero. Approved means a person accepted a research candidate. It is not an order. Opportunity amounts stay off the report. Overdue uses the date in Asia/Kolkata at read time, so a missed background job cannot hide a due task. Owner, manager, and read-only can open the report. Sales and researcher cannot. Retry remains on the research run.

## D-025 — The Vapi adapter is installed and live calling stays disabled

Date: 2026-11-17.

Legal and telecom approval has not been given, and no named test contact was approved. `POST /api/v1/calls/start` therefore returns 403 and does not call Vapi. The adapter itself posts one customer number to `https://api.vapi.ai/call` only after the live flag, legal approval, a saved assistant, an imported caller-number id, the named contact, permission, suppression, India weekday hours, and the caps of one in-flight call and one call per day all pass. Webhooks accept the shared secret as a bearer token or `X-Vapi-Secret`. A timestamp older than five minutes is rejected.
