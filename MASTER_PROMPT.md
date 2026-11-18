# N GREEN LEADOS — MASTER SPECIFICATION & CODING-AGENT PROMPT
Version: 1.0 • 17 November 2026 • Owner: N Green (client project)

> **How to use:** Attach this Markdown file, `reference_accounts.json`, and (optionally) the supplied `N_Green_LeadOS_MVP.zip`, `MVP_SCOPE.md`, `Content N Green.pdf`, and original packaging-product screenshot to your AI coding agent. Paste the **START COMMAND** below. Do not ask the agent to build all phases at once. When it finishes, use the matching prompt in `PHASE_BY_PHASE_PROMPTS.md` to authorize exactly one phase at a time.

## START COMMAND — COPY TO YOUR CODING AGENT

You are my principal product engineer, full-stack developer, AI-research systems designer, backend engineer, QA lead and security-conscious technical collaborator. Build **N Green LeadOS**, a professional, modular, production-oriented **B2B sustainable-packaging lead intelligence + CRM + permission-gated AI calling application** for an Indian sustainable packaging manufacturer, **in strictly controlled phases**. Start with **PHASE 0 ONLY**: audit inputs, inspect any existing code, reconcile feature requirements, produce PRD/architecture/data model/backlog and initial project skeleton, and STOP. Do not implement subsequent phases until I explicitly write `APPROVE PHASE N`. Perform actual code changes and run tests in the repository, not just narrate intended work. Never simulate a deployed app, real web research, a made phone call, or passing tests. When a provider credential is missing, implement a functioning mock adapter and label it DEMO. At the end of every phase give file tree, implemented behavior, commands, test outputs, screenshots if possible, unresolved risks, and the exact next-phase gate. Keep code readable enough for another developer to maintain.

Treat the remaining contents of this document as project requirements; treat user-supplied brand/company names as **research targets/hypotheses**, not proof of current plastic use, revenue, contacts, or purchasing intent. The purpose is a sales-research product, **not** N Green's much larger packaging-supply-chain automation vision.

---

## 1. Business definition and boundaries

N Green has operated as a manufacturer of sustainable/biodegradable packaging. The client reports that it currently has **no working internal technology platform**. The client now wants a sales-tech MVP to:

1. Find businesses in India that **might** use significant quantities of packaging products that N Green could supply in compliant alternatives.
2. Identify probable packaging applications for each prospect company, organized by industry and packaging product. The app may display examples such as `Zepto → potential requirements: carry bags, grocery bags, garbage bags, garbage bags on rolls`, but MUST label these as unverified hypotheses until backed by evidence or a buyer's confirmation.
3. Enrich potential accounts using **lawful public business information** and links to evidence, including verified official-domain general corporate contact channels where available. No invented phone numbers, emails, names, purchasing volumes or "currently uses plastic" facts.
4. Combine **two lead origins**: (A) online research discovery; (B) manually entered or uploaded pre-existing leads and contacts.
5. Human-review and deduplicate researched candidates before they become CRM accounts.
6. Operate an AI outbound calling assistant **only for contacts where the organization has validated an appropriate legal basis/permission and telecom requirements**. Prioritize a mocked call assistant, with the real adapter disabled by default until approved.
7. Capture structured conversation results (needs, material and product, quantity if stated, purchasing role, buyer interest, timeline, current supplier only if stated, next step, meeting interest, objections, opt-out); write a call summary and update CRM following configurable rules.
8. Let staff edit, override, approve, reject, assign, filter and export records; every automated recommendation and CRM change should have traceable evidence or a clear origin.
9. Ultimately measure business results: researched accounts → validated accounts → permissioned calls → engaged buyers → meetings → samples/quotes → won orders.

**Non-goals for this version:** factory ERP, manufacturer capacity planning, government EPR filing automation, finished packaging ordering and production management, omnichannel mass marketing, LinkedIn login scraping, automated cold calling harvested numbers, unverifiable competitor/plastic-use claims, and a general-purpose autonomous web browsing bot. Build integration boundaries for future ERP/procurement connections; do not build those modules now.

## 2. Required user personas

- **Owner/Admin:** sees complete team pipeline, settings, import rules, audit logs, budgets, and integrations.
- **Researcher/Analyst:** runs discovery, validates evidence, merges or rejects duplicates, adds manual data.
- **Sales/BD Executive:** manages assigned accounts, authorized calls, meeting notes, tasks, CRM stage.
- **Manager:** reviews quality, assigns leads, approves calling eligibility, sees analytics.
- **Read-only stakeholder:** dashboards only, no calling or editing.

For the first production pilot support one organization (N Green) with multiple staff, but retain `organization_id` and permission boundaries for later multi-tenant evolution.

## 3. Required industry taxonomy

Primary CRM industry categories (must support extension and admin-managed aliases):

1. Q-Commerce / Quick Commerce
2. E-Commerce
3. Pharma
4. Facility Management
5. FMCG
6. Logistics
7. Supermarket / Hypermarket Chains
8. Hotels / Hospitality
9. Food Service / QSR / Cloud Kitchens
10. Healthcare / Hospitals
11. Retail Chains
12. Fashion / Apparel / Textiles
13. Manufacturing / Industrial
14. Warehousing / Fulfilment
15. Agriculture / Horticulture
16. Restaurants / Catering
17. Other (editable)

Do not assume the sector means that all companies use the same plastic product. Store whether category assignment was manual, inferred, or source-verified.

## 4. Packaging product taxonomy — preserve exact source headings

1. Carry Bags
2. Grocery Bags
3. Garbage Bags
4. Garbage Bags on Rolls
5. Perforated Rolls
6. Courier Bags
7. Shrink Films
8. Stretch Films
9. Industrial Packaging
10. Garment Bags
11. D Cut Bags

Seed initial targets from the supplied reference screenshot or `reference_accounts.json` without inventing additional target-to-product rows. A company may have multiple applicable products. Product categories that have no source-listed companies must stay empty, not be populated speculatively. A user may add potential requirements manually with a hypothesis label.

**Exact product → source reference companies:**

- Carry Bags: Medplus; Swiggy Instamart; Zepto; D mart; Ratnadeep; Big Basket; Spencers; More; Ushodaya; Vijetha; Jio mart; Spar Hypermarket; Blinkit; Zomato; Amazon Fresh; Flipkart Minutes.
- Grocery Bags: Swiggy Instamart; Zepto; D mart; Ratnadeep; Big Basket; Spencers; More; Ushodaya; Vijetha; Blinkit; Zomato; Amazon Fresh; Flipkart Minutes.
- Garbage Bags: Medplus; Swiggy Instamart; Zepto; D mart; Ratnadeep; Big Basket; Spencers; More; Ushodaya; Vijetha; Blinkit; Zomato; Amazon Fresh; Flipkart Minutes.
- Garbage Bags on Rolls: Medplus; Swiggy Instamart; Zepto; D mart; Ratnadeep; Big Basket; Spencers; More; Ushodaya; Vijetha; Blinkit; Amazon Fresh; Flipkart Minutes.
- Perforated Rolls: D mart; Ratnadeep; Spencers; More; Ushodaya; Vijetha; Blinkit.
- Courier Bags: Medplus; Myntra; Amazon; Flipkart.
- Shrink Films: Swiggy Instamart; Big Basket; Zomato; Amazon Fresh; Flipkart Minutes.
- Stretch Films: [no companies in supplied sheet].
- Industrial Packaging: Sneha Chicken.
- Garment Bags: [no companies in supplied sheet].
- D Cut Bags: [no companies in supplied sheet].

Preserve the display name and normalized name separately. Treat Amazon and Amazon Fresh as different business units and link parent-child only if evidence supports it. Do not merge similarly named organizations merely because they are owned by a common parent. Deduplicate within each company by verified normalized domain + business unit and human review of ambiguous names.

## 5. Product flow, user experience and screen specifications

### Main flow

`Search plan -> internet search -> sourced candidate -> dedupe -> evidence review -> research-qualified account -> approved contact and calling permission -> demo/live authorized call -> structured insight and follow-up -> CRM stage -> report`

Parallel flow: `Manual form / CSV -> validation -> dedupe -> CRM / research queue`, respecting permissions.

### Required screens/routes

- `/login` — secure staff login.
- `/overview` — KPI tiles for research candidates, approved accounts, contacted/permissioned leads, qualified opportunities, meetings and revenue-stage counts; all from real DB, not hard-coded metrics.
- `/research` — AI Research Studio: choose sectors, products, regions, company size/chain type, keywords, freshness, exclusion lists, search depth, budget and result limit. Start run, monitor steps and cost, inspect results.
- `/research/runs/[id]` — run detail, searches, evidence, extraction statuses, errors, retry/cancel and approvals.
- `/accounts` — searchable companies table/cards with industry, product hypotheses, evidence confidence, last verified, source, contact status, assigned owner, stage and score.
- `/accounts/[id]` — company workspace: overview, source/evidence timeline, products and status, public business contacts, research notes, historical interactions, calls, assignments, activity audit, follow-up tasks; edit with permissions.
- `/imports` — manual create, CSV mapping and validation preview, duplicate conflict review, import results and export.
- `/contacts` — contact ownership, role, business source, channel, verified status, permission ledger, DNC toggle, deletion requests; do not require personal contact data for a company to exist.
- `/calling` — queue of approved contactable contacts only, DEMO mode first; AI script editor with controlled variables and call settings; never auto-dial by default.
- `/calls/[id]` — status, transcript (only if lawful/consented), structured insights, human review and revised summary, CRM update history.
- `/crm` — kanban and table with customizable stages, manual stage override with reason, notes, task reminders, quotations/meeting outcomes.
- `/tasks` — due dates, owner, reminders, follow-ups, status and activity log.
- `/reports` — conversion funnel, research-source performance, cost per validated account, quality, call outcomes, opt-outs, stage ageing, team performance.
- `/settings` — taxonomy, roles, integrations, company N Green product catalog, AI prompts and model settings, search budgets, audit and retention controls.

Use **Bizongo (https://www.bizongo.com/)** as high-level aesthetic inspiration only: restrained B2B design, strong hierarchy, spacious white/light-cream surfaces, forest green/teal accents, clean compact data tables, subtle cards and readable typography. Original N Green branding; do not copy layout, trademarks, images, code or exact text. Responsive tablet/mobile views, clear loading/empty/error states, keyboard accessibility, color contrast. UI should look client-demo-ready, not a default AI-generated CRUD page. No made-up metrics. Sample account labels must visibly say "Reference target – not verified".

## 6. Preferred technology architecture (keep consistent)

**Recommended stack**

- Frontend: **Next.js App Router, React, TypeScript**, Tailwind CSS + shadcn/ui, Lucide icons, TanStack Query for client-side server state, React Hook Form + Zod validation, and Recharts only for actual reports.
- Backend/API: **Python 3.12+ with FastAPI**, Pydantic v2, SQLAlchemy 2.x and Alembic migration tooling. Separate `api/routers`, `services`, `adapters`, `repositories`, `jobs` and `schemas`. Generate OpenAPI; client typed using OpenAPI generation rather than duplicate manually incompatible types.
- Primary database: **PostgreSQL** (Supabase hosted Postgres is a pragmatic small-team choice). Use pgvector only later if semantic retrieval proves necessary; conventional indexed SQL and text search first. Development Postgres via Docker Compose. Use UTC timestamps plus local timezone display.
- Auth: **Supabase Auth** with server-side JWT validation in FastAPI, organization membership and server-side RBAC. Supabase RLS can add defense in depth for direct DB access, but no authorization should depend solely on hidden UI buttons. Never place service-role secret in frontend.
- Object storage: Supabase Storage / compatible managed private object storage for approved attachments; signed URLs and organization scoping.
- Jobs: start with synchronous endpoints for tiny operations; introduce **Redis + Dramatiq worker** when external research jobs, provider retries and call-event processing begin. Jobs idempotent, cancelable and rate limited.
- Research search adapter: **Serper.dev** initially because existing prototype already uses it. Keep a replaceable interface for Tavily and licensed data services; always return `source_url`, snippet, queried_at and provider. No direct Google HTML scraping or CAPTCHA bypass.
- AI extraction adapter: hosted LLM with structured JSON outputs via Pydantic schema. Abstract vendor behind `AIProvider`; local `MockAIProvider` for offline tests. AI may generate search queries and extract supported candidate facts; must not invent claims or contacts. Keep prompts versioned and record model, latency and cost.
- Voice adapter: **Vapi** first behind `VoiceProvider` interface, plus `MockVoiceProvider`. Verify caller-ID/India route support, telecom/legal approval, DNC preferences, provider terms and recording requirements before enabling real outbound calling.
- Notifications: in-app first, SMTP/transactional email later behind adapter. WhatsApp integration only with approved templates and consent after MVP.
- Deployment: frontend to Vercel (or comparable) and API + worker to a managed container host; DB and storage to Supabase, Redis to a managed Redis service. Never assume the API can run long jobs inside a short-lived serverless request.
- Local development: Node.js supported LTS, Python 3.12 or 3.13 supported by pinned dependencies, pnpm, uv/pip, Docker Compose, `.env.example`, Makefile or cross-platform scripts for Windows PowerShell.
- Tests: pytest + httpx for API, Vitest/React Testing Library for UI units, Playwright for end-to-end, Ruff/mypy/ESLint/TypeScript, GitHub Actions CI.

**No separate microservices or Kubernetes needed for MVP.** One frontend app, one modular Python API, one background worker once needed, one Postgres database. Avoid reimplementing a CRM framework before basic use cases work.

### Proposed repo layout

```
ngreen-leados/
  apps/web/                    # Next.js TypeScript frontend
  services/api/                # FastAPI, Pydantic, SQLAlchemy, Alembic
  services/worker/             # Dramatiq tasks when introduced
  packages/contracts/          # generated OpenAPI client / shared schemas
  data/reference_accounts.json
  docs/PRD.md
  docs/ARCHITECTURE.md
  docs/ERD.md
  docs/DECISIONS.md
  docs/SECURITY_AND_COMPLIANCE.md
  docs/RUNBOOK.md
  infra/docker-compose.yml
  .github/workflows/ci.yml
  .env.example
  README.md
```

## 7. Core data model (normalized and auditable)

Design tables with UUID primary keys and scoped `organization_id` where relevant:

- `organizations`, `users`, `memberships` and role assignments.
- `industries`, `products` (with N Green supply availability, certification metadata, size/spec/MOQ as optional reviewed values), `industry_aliases`.
- `companies` (display_name, normalized_name, parent_company_id nullable, business_unit, canonical_domain nullable, industry_id, city/state/country, team_owner, source_origin, review_status, reviewed_at, notes, created/updated).
- `company_product_needs` linking company+product, `need_status` = hypothesis | publicly_evidenced | buyer_confirmed | rejected, source and confidence, use case, last_reviewed_at. Need not be material-specific when unknown.
- `research_runs` (filters, query plan, budgets, status, progress, cost, start/end, error summary, initiator).
- `research_queries`, `research_candidates`, `sources` (provider, canonical_url, page_title, retrieval timestamp, domain, snippet/evidence text, rights/retention tag, source hash, error status), `evidence_claims` (exact claim, cited source, extraction method, claim_status and verifier).
- `contacts` (company_id, optional contact_name, buyer_role, public business email/phone nullable, contact_source_url, date_verified, status, assigned_owner). Do not store private information from restricted sites.
- `contact_permissions` (contact/channel, basis, scope, recorded_at, expires_at, recorded_by, supporting proof reference, DNC status, revoke_at); unknown permission -> DO NOT CALL.
- `outreach_campaigns` and `call_attempts` (provider id, who authorized, consent snapshot, requested/scheduled/completed times, state, retry count, provider cost metadata, recording access as applicable).
- `call_events`, `call_insights` (structured schema and human validation, transcript metadata, summary, classification confidence, requested_callback, objections, relevant products, reported volume, timeline, buying authority).
- `crm_opportunities` (company, optional contact, stage, value nullable, target_products, stage entered_at, close reason), `opportunity_stage_events`.
- `activities`, `notes`, `tasks` (owner, due_at, completed_at), `audit_events` (actor, entity, action, before/after redacted metadata, timestamp), `imports` and `import_rows`.
- `integrations` (provider config references, never raw secrets), `usage_events` (search count, AI tokens, call minutes, cost estimates) and `suppression_list` (hashed normalized phone/email and reason, minimally necessary storage).

Constraints: normalized domain and name matching plus business-unit rules, one product-association record per company+product+evidence origin, provider event unique IDs, idempotency keys, soft-delete/retention policies, important foreign keys/indexes. Separate account research state from outreach permission and CRM opportunity stage. Never automatically infer consent or "won" from an LLM.

## 8. Research agent design — actionable specifications

Implement an orchestrated research workflow, **not one opaque prompt that makes everything up**:

1. `Planner`: given sector, product, geography and N Green catalog, produce bounded search queries such as `large pharmacy chain India disposable carry bags procurement` or `warehouse facility management waste bag vendor tender India`. Search focuses on evidence of operations and procurement needs, not on asserting current plastic use.
2. `SearchAdapter`: call provider API with per-run caps, retries/backoff and source URLs. Preserve provider raw response only as permitted; do not circumvent source terms, robots or login.
3. `CompanyResolver`: extract companies/brands, normalize websites/domains; separate holding companies from operating brands; dedupe into existing company records with review for ambiguity.
4. `EvidenceExtractor`: classify each candidate statement with a quote/snippet, exact URL, retrieval time, and `supported / inferred / unknown / contradicted`. Untrusted webpages must not execute instructions or modify system prompts (prompt-injection defense).
5. `PackagingNeedClassifier`: map evidence to allowed product taxonomy; if evidence is only category-related, label `hypothesis`. Never assert verified biodegradable replacement availability or plastic use without actual support.
6. `ContactResearcher`: first seek official public contact pages and **general business channels** such as company procurement/support email, contact form or corporate phone. Record URL + verification date; do not scrape private profiles, login-gated listings or personal mobile directories.
7. `FitScorer`: deterministic 0–100 **sales research priority**, NOT probability of conversion. Explain scoring: industry alignment (0–25), product fit (0–25), operational scale signal with source (0–15), geography/supply fit (0–10), verified buyer-relevant evidence (0–20), source freshness (0–5). Missing evidence gets no points; do not disguise hypothesis as fact. Distinguish research confidence from fit score.
8. `ReviewQueue`: show why the company was found, what is verified and what is hypothesized, related packaging products, clickable citations, duplicates, and explicit Approve/Reject/Merge actions.
9. `PromoteToCRM`: only reviewed accounts become active CRM records; contactable status additionally needs a valid documented permission basis.

Research controls: max companies/run, max pages/company, max search queries, max spend, concurrency, caching, pagination, deduping, provider error handling, pause/cancel, usage logs. Research errors must show honestly instead of silently returning demo results as live. Seed/demo companies must have source = `Reference sheet`, distinct from web research.

## 9. AI calling — safe technical specification

Do not integrate live calls until **human acceptance of contact-permission policy** and legal/telecom approval. The first working end-to-end flow uses `MockVoiceProvider` only. Real provider adapter should be feature-flagged OFF by default and must recheck permission at execution time (not only when queue is created).

### Eligibility to initiate a real call
- Signed-in authorized sales user approves call.
- Verified destination phone (E.164) and correct contact/organization.
- Recorded appropriate consent/legal authorization for automated promotional voice contact, validated against applicable local telecom requirements and provider rules; public listing alone is not enough.
- Not on internal or relevant DNC/suppression list; valid hours and timezone; no revoked consent or expired permission.
- Outbound routing and caller identity are configured and compliant; cost/concurrency budget remains.
- Provider account, authorization, assistant version and webhook signature authentication all configured.

### AI calling assistant behavior
Introduce N Green and disclose it is an AI assistant. Be respectful and brief. Do not claim the company uses conventional plastic unless confirmed; say "We help businesses explore sustainable alternatives for suitable packaging applications." Ask whether it is a good time and whether they are comfortable continuing. Collect, only when voluntarily offered: actual packaging product(s), use volume and unit, material/spec/size, procurement responsibility, target cost, trial interest, transition time horizon, existing challenges, contact preferences, callback/meeting. Answer questions within an approved knowledge base; if uncertain, say a human representative will confirm. Never promise regulatory certifications or price that are not verified. Offer handoff to N Green staff; respect "stop calling" immediately; do not continue persuasion. Support English first, design for Hindi and Telugu after script/voice tests. Record/transcribe only under applicable consent, retention and policy.

### End-of-call structured JSON schema

```
{
  "outcome": "interested|meeting_requested|follow_up|not_interested|no_answer|wrong_number|do_not_call|needs_review",
  "spoken_language": "en|hi|te|other|unknown",
  "spoke_to_decision_maker": "yes|no|unknown",
  "requirements": [{"product": "Carry Bags", "quantity": null, "unit": null, "material_spec": null, "evidence_span": "..."}],
  "interest_level": "high|medium|low|unknown",
  "timeline": null,
  "objections": [],
  "meeting_requested": false,
  "callback_requested_at": null,
  "summary": "Factual concise summary",
  "next_action": "Human-reviewable recommended task",
  "needs_human_review": true,
  "do_not_call": false,
  "confidence": 0.0
}
```

Validate with Pydantic; map new product phrases to taxonomy but retain raw phrase. Use provider call ID + event ID idempotency. A duplicate webhook must not create duplicate tasks or CRM stages. A call marked `do_not_call` immediately suppresses future outreach. `interested` or `meeting_requested` creates a suggested CRM transition **with human review**, or an explicitly configured approved rule. Never auto-mark deal as Won or invent an order.

## 10. CRM sales process

Maintain separate account and opportunity states. Suggested sales stages (admin configurable): `Research` → `Validated Account` → `Outreach Eligible` → `Contacted` → `Interested` → `Meeting Scheduled` → `Sample / Trial Requested` → `Quotation Sent` → `Negotiation` → `Won` / `Lost` / `Nurture`.

A company may be in CRM without outreach consent. The stage `Outreach Eligible` is guarded by permission; stage changes are recorded. Add configurable stage requirements, probability only with clearly labelled heuristic, and manual ownership. Auto task creation for callbacks and sample requests. Show source, call summary, stage change and timestamp in an activity feed.

## 11. Mandatory quality, privacy and security requirements

- Production authentication and RBAC server-side on every endpoint; strict organization scoping on database reads/writes.
- No open unauthenticated CRM endpoint, no service keys in browser, no hardcoded passwords or webhook query-token secrets.
- Provider webhook HMAC/OAuth or supported signed mechanism and replay protection; never blindly trust a posted `outcome`.
- Validation, rate limiting, CSRF where cookie auth applies, secure CORS, input length checks, CSV formula-injection safe exports, safe file uploads, SQL injection resistance, server-side pagination.
- SSRF defense for URLs discovered by AI/crawlers; block local/private/link-local addresses and redirects to them. Respect robots, licensing, TOS, crawl rates and permissions.
- Secrets in environment / secret manager; scrub PII from logs; encrypted provider keys and sensitive fields; retention and export/delete workflows for personal data, staff audit trails, backup and restore test.
- No fabricated prospects, no fabricated numbers, no fabricated evidence, no fabricated scores represented as validation, no unsupported sustainability/biodegradability/compliance claims.
- Live automation is opt-in and includes kill switches, spending caps, fail-closed permission checks and clear human approval gates.
- For Indian outreach, require qualified review of TRAI TCCCPR/A2P/UCC requirements, sender/telecom registration, DNC, recording and applicable privacy rules before production launch; do not circumvent regulations or send unsolicited promotional robo-calls.

## 12. Example API contract (design in Phase 0; implement only by phase)

- `GET /health` and `GET /api/v1/me`
- `GET/POST /api/v1/accounts`, `GET/PATCH /api/v1/accounts/{id}`
- `GET/POST /api/v1/accounts/{id}/product-needs`
- `POST /api/v1/imports/preview`, `POST /api/v1/imports/commit`
- `POST /api/v1/research/runs`, `GET /api/v1/research/runs/{id}`, `POST /api/v1/research/runs/{id}/cancel`
- `GET /api/v1/research/candidates`, `POST /api/v1/research/candidates/{id}/review`
- `GET/POST /api/v1/contacts`, `POST /api/v1/contacts/{id}/permissions`
- `POST /api/v1/calls/simulate`, `POST /api/v1/calls/start` (guarded, disabled by default)
- `POST /api/v1/integrations/voice/webhook` (authenticated)
- `GET/POST/PATCH /api/v1/opportunities`, `PATCH /api/v1/opportunities/{id}/stage`
- `GET/POST/PATCH /api/v1/tasks`, `GET /api/v1/reports/funnel`

Use API versioning, validation schemas, pagination and error structures. Routes should evolve from actual delivered code rather than become stub endpoints.

## 13. Phase-gated implementation plan and exit criteria

### Phase 0 — Audit, PRD, architecture, reference data
Review source screenshot, N Green PDF, MVP zip and source, and UI reference. Document actual requirements and exclusions, architecture decision record, schema ERD, API plan, realistic risk register, sourcing/legal uncertainties and timeline. Create repo skeleton, no premature product features. **Exit:** precise written scope, mapping, clickable wireframes or UI plan and developer run instructions.

### Phase 1 — Foundation: modern UI, authentication, PostgreSQL
Monorepo, auth, RBAC, schema/migrations, local Docker Postgres, shared UI components, responsive shell, dark-green original branding, empty dashboard based on real API. **Exit:** staff login, authorized pages and secure account CRUD skeleton; CI and lint/test pass.

### Phase 2 — Manual CRM + reference data + CSV
Implement exact taxonomy, 20 deduped sample target accounts from screenshot, company-product many-to-many, manual form, notes/assignment, import preview, conflict resolution, CSV safe export, account detail and CRM board. **Exit:** import 50 test accounts, no duplicates, good editing/filters, persisted DB.

### Phase 3 — Live internet discovery with source-backed evidence
Serper search adapter, filters/query templates, background jobs, progress, source storage, budget/rate caps, company dedupe and review queue. Do **not** claim AI extraction works yet. **Exit:** with provider key, demonstrate real source-backed research; without key, deterministic fixture data with clearly labeled DEMO.

### Phase 4 — AI research agents and fit analysis
Add planner, structured evidence extractor, need classifier, company resolver, fit scorer with reasons, contradiction/uncertainty handling, source citation and human review. **Exit:** seeded evaluation set; unsupported source claims flagged instead of invented, AI results editable and explainable.

### Phase 5 — Contacts + outreach permission centre
Official-domain generic corporate contact research, manual verified contacts, source provenance, verification dates, contact roles, permission evidence, DNC/suppression list, approval UI and audit. **Exit:** nobody without permission can enter a live calling queue; opt-outs honored in tests.

### Phase 6 — AI calling simulator and CRM automation
Mock provider, approved call scripts and voice persona, simulated transcripts/structured outcomes, CRM transitions, callback tasks and idempotent webhook tests. **Exit:** click simulate → review insights → accepted CRM update with full audit, all offline.

### Phase 7 — Real outbound calling provider integration (permission-gated)
Only after legal review and provider access. Vapi adapter with verified signed webhooks, inbound events, E.164, timezone checks, budget caps, fail-closed consent gate and tested language scripts. Pilot with explicitly authorized test contacts; no bulk calls by default. **Exit:** one legal and authorized phone test correctly updates CRM and opt-out stops future calls.

### Phase 8 — Sales analytics, follow-ups and reliability
Research source yield, conversion funnel, task scheduling, team assignments, export, stage ageing, monitoring, retries, cancellation and cost dashboard. **Exit:** metrics reflect DB and reports can be explained; no fake charts.

### Phase 9 — Production hardening + launch
RLS/roles security audit, e2e tests, backup/restore, PII retention, alerts, deployment, operations runbook, load test, CI/CD and clean handover. **Exit:** staging demo and reviewed production pilot ready for approved accounts.

**Phase 10 later (not in scope):** integrations to quotes, sample workflows, stock, manufacturing, procurement or environmental compliance systems. Design events/APIs to make later integration possible.

## 14. Testing and demo acceptance scenarios

1. Start clean local environment; account requires sign-in, staff sees role-appropriate data.
2. Exact reference sheet imports as **20 distinct target companies** without inventing verified usage or contact details.
3. Add a company manually with multiple product needs, then change evidence status from hypothesis to verified with a source.
4. CSV with duplicates and malformed rows shows preview, row-level errors and a safe rollback/partial-failure report.
5. Search 10 Q-Commerce businesses for carry bags in Hyderabad; app shows provider links and hypotheses, not invented plastic use.
6. Provider outage shows explicit error and safe retry; no fake success.
7. Candidate with same official domain is flagged as possible duplicate; separate business units remain separately reviewable.
8. A contact with unknown consent has calling disabled; turning on real integration without permission still cannot call.
9. Mock call: "interested in courier bags, wants a sample next week" creates reviewable structured insight and a due task.
10. Mock call: "never contact me again" immediately adds suppression, notifies staff and blocks further attempts.
11. Replaying identical call webhook produces one activity and one CRM update only.
12. Admin can review audit events, basic usage charges, source citations and provider errors.
13. No external API keys: entire local/demo experience still works.

## 15. Coding-agent rules for EVERY phase

- Start by listing phase deliverables and locating existing relevant files. Reuse good code when feasible; do not erase files without explaining why.
- Before selecting package or API syntax, verify its current official docs. Pin supported versions in lockfiles and document compatibility; no invented endpoints.
- Implement real vertical slices: DB + API + UI + tests; avoid dozens of placeholder screens or unimplemented buttons.
- Add code in small coherent commits/changes. Use environment examples; never commit real secrets or real personal contact info to fixtures.
- Run lint, typecheck, unit/integration and relevant end-to-end tests. Provide actual commands and observed outputs, not just claims.
- Do not skip failed tests; fix or disclose blockers, including missing web/voice API access.
- Update `docs/PROGRESS.md`, changelog/decision log and README each phase.
- End every phase with exactly: (a) delivered modules, (b) how to run locally on Windows PowerShell, (c) test summary, (d) screenshots or honest inability, (e) outstanding limitations, (f) recommended next phase, (g) **STOP: Await APPROVE PHASE N**.
- Never auto-advance into another phase, make real calls, spend API credits, send outreach or deploy to production without explicit user approval.

## 16. Important references and sources

**Client files:** the N Green company PDF (strategic longer-term vision, not proof of an existing tech platform); the product-by-company screenshot (lead research hypotheses); supplied HTML pages (earlier UI concepts only); the prior local LeadOS MVP (small FastAPI/SQLite demo with no authentication; source reusable only after review). The client's latest clarification takes precedence: sales research-to-CRM is the **current MVP**.

**Design:** https://www.bizongo.com/

**Official implementation references:**
- Next.js App Router: https://nextjs.org/docs/app
- FastAPI: https://fastapi.tiangolo.com/
- Supabase Auth: https://supabase.com/docs/guides/auth
- Supabase verified Python JWT claims: https://supabase.com/docs/reference/python/auth-getclaims
- Serper API: https://serper.dev/
- Tavily alternative: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Vapi outbound calls: https://docs.vapi.ai/calls/outbound-calling
- Vapi server event schemas: https://docs.vapi.ai/server-url/events
- Vapi server authentication: https://docs.vapi.ai/server-url/server-authentication
- Official India telecom guidance (2026): https://www.pib.gov.in/PressReleasePage.aspx?PRID=2311989&lang=2&reg=48
- TRAI regulation: https://www.trai.gov.in/sites/default/files/2025-02/Regulation_12022025.pdf

**Final instruction:** Implement only the phase explicitly approved. Before taking any live external action that changes provider state, costs money, or contacts a person, request a specific approval. Prioritize a reliable, verifiable research-and-sales workflow over flashy but ungrounded AI.
