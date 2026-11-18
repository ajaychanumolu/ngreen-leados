# N GREEN LEADOS — ONE-PHASE-AT-A-TIME PROMPTS

Read and keep `MASTER_PROMPT.md` as the permanent specification. Send **only one** phase prompt after checking the previous phase's output and tests. Never paste all phases to tell the agent to execute them together.

## 0 — Architecture and audit (SEND FIRST)

```
Read MASTER_PROMPT.md and all attached N Green source files. Begin PHASE 0 ONLY. Audit the existing LeadOS FastAPI/SQLite demo if supplied: identify reusable logic, security issues and missing features. Reconcile the new client-confirmed scope (Internet B2B lead discovery + manual leads + permission-gated AI calls + CRM) with the older, broader N Green packaging-operations vision. Inspect the exact reference product/company mapping and preserve all 11 categories and 20 distinct company targets as hypotheses. Produce docs/PRD.md, docs/ARCHITECTURE.md, docs/ERD.md, docs/SECURITY_AND_COMPLIANCE.md, docs/DECISIONS.md, docs/PHASE_PLAN.md and an accurate repository setup README. Recommend version-pinned libraries after checking official docs. Draft the screen map and data-contract schemas. Do not build full product features, contact the web for leads, call people, or spend provider credits. Run available baseline tests and report their true output. STOP and wait for APPROVE PHASE 1.
```

## 1 — App foundation, login and database

```
APPROVE PHASE 1. Implement only the foundation from MASTER_PROMPT.md: Next.js + TypeScript + Tailwind + shadcn/ui frontend, FastAPI API, PostgreSQL migrations, Supabase Auth integration with correctly verified server JWT and server RBAC, organization membership, original polished N Green UI app shell and responsive sidebar, protected routes, typed API client, loading/error states, basic health/me and secure account shell endpoints, Docker Compose local DB, .env.example, CI lint/typecheck/test. Run locally on Windows and write exact commands. No mocked metrics displayed as live; placeholders must be labeled demo. Write tests for login/unauthorized access. STOP after tested foundation; do not begin lead discovery.
```

## 2 — Manual CRM, reference account seed and CSV

```
APPROVE PHASE 2. Implement the complete offline/manual research-and-CRM vertical slice: 11 packaging products, CRM industries and aliases, 20 deduplicated source-reference accounts with many-to-many product needs labeled unverified, companies/accounts listing, details, CRUD, opportunity board and stages, assigned owner, notes, manual contacts, safe CSV import preview/commit, duplicate conflict review, editable tags/filters and CSV safe export. Use PostgreSQL and migrations. Implement RBAC, org isolation, audit log, validation and tests. Demonstrate import/edit/review of 50 fixture companies. Show real persisted data; no fabricated public contacts. STOP before live web research.
```

## 3 — Research discovery integration (NO AI extraction yet)

```
APPROVE PHASE 3. Implement provider-backed company discovery, NOT AI assertions yet. Use a Serper adapter with mock fixtures if key missing, configurable research filters (industry, packaging product, geography, limit), query templates, background job worker with Redis, run progress/cancel/retry, API rate limit and budget caps, provenance URLs/excerpts and retrieved timestamps, duplicate suggestions, candidate review queue, source filters and approve/reject/merge actions. Every result is RESEARCH CANDIDATE, not verified plastic buyer. UI should show exact source links and whether DEMO or LIVE. Add tests for throttling, provider outage and fail-safe budget. STOP before LLM classification.
```

## 4 — AI Research Agent and evidence classifier

```
APPROVE PHASE 4. Implement a modular research agent using deterministic tools and a structured-output AI provider adapter with mock mode: planner -> source search -> company resolver -> extraction with citations -> product-need classification -> explainable research fit score -> human review. Validate Pydantic outputs, reject unsupported claims, protect against web prompt injection, detect contradictory sources, label unverified hypotheses explicitly and display scores with reason breakdown. Persist prompt/model/version and token usage. Add a golden-set evaluation on reference companies and adversarial tests. Only reviewed candidates enter CRM. STOP before contact research or calls.
```

## 5 — Public business contacts and permission center

```
APPROVE PHASE 5. Build business contact research limited to permitted official public contact pages and corporate channels, plus manual verified contacts. Track source URL, checked date, buyer role, owner, validity and permission evidence. Add DNC/opt-out, channel restrictions, permission expiry, approval workflow, call eligibility server function, privacy/retention controls and tests that unknown permissions always block automated promotional calling. Do not scrape personal mobile directories or login-gated profiles; do not make a call. STOP after security and UI tests.
```

## 6 — AI calling workflow in DEMO mode

```
APPROVE PHASE 6. Implement MockVoiceProvider, reviewed AI call script and knowledge base, simulated calls and transcripts, structured call-outcome parser (Pydantic), deduped call events, human approval of AI-extracted notes, and CRM stage/task updates. Cover interested, meeting_requested, callback, not_interested, no_answer, wrong_number, needs_review and do_not_call. Test two full flows: interest generates task; opt-out blocks future calls. Make DEMO mode unmistakable. NO provider call, NO real phone requests. STOP before Vapi live integration.
```

## 7 — Controlled live voice integration

```
APPROVE PHASE 7 only if I have separately provided live-provider credentials and approved legal/telecom configuration. Integrate Vapi behind a provider interface with E.164 validation, documented permission and DNC checks at execution, caller identity and routing verification, allowed local hours, concurrency and spending caps, secure server-authenticated signed webhooks, replay protection, retries and idempotency. Implement structured callback mapping and CRM review. Do not send any real call unless I explicitly approve a named test contact and exact call. If prerequisites are missing, finish the integration with a fake sandbox adapter and mark LIVE DISABLED. No mass dialing. STOP.
```

## 8 — Follow-ups and dashboards

```
APPROVE PHASE 8. Add reliable tasks and follow-up scheduler, team ownership, research/call pipeline analytics, conversion funnel, stage ageing, lead quality, cost per researched and validated account, spend logs, team views and export. Every chart must derive from real stored data and display empty/limited-data states correctly. Add delivery monitoring, retry queues and incident alerts. Avoid speculative revenue claims. STOP after test evidence.
```

## 9 — Production pilot readiness

```
APPROVE PHASE 9. Conduct a comprehensive production security and privacy review: authenticated endpoints, tenant isolation, SSRF, prompt injection, DNC failsafes, provider credential handling, webhook signatures/replay, file permissions, backup and restore, retention/deletion workflows, migration rollback, rate limiting, observability, CI/CD and Playwright E2E. Deploy to STAGING only if explicitly authorized, run genuine smoke tests, create operating runbook, disclose unresolved risks. Production deployment and contacting real prospects require separate explicit approval. STOP with final handover checklist.
```

## Reusable checkpoint command after any phase

```
Before moving on, show me exactly what you implemented in the approved phase; the files changed; local setup commands for Windows PowerShell; database migrations; all tests run and actual pass/fail output; screenshots or browser test evidence; missing prerequisites; costs; security or data risks; known limitations; and what the next phase would add. Do not move forward until I say APPROVE PHASE N.
```
