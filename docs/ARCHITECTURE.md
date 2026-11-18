# Architecture

Status: Phase 9 is running locally on SQLite. A security review, contact erasure, SQLite backup, and a migration rollback check are in the repo. Staging was not deployed. Search is live when `SERPER_API_KEY` is set, otherwise DEMO. Classification is live when `AI_PROVIDER` is `openai` or `groq` and `AI_API_KEY` is set, otherwise mock. The local worker is an in-process thread. Live calling is disabled. `VOICE_LIVE_ENABLED` and `VOICE_LEGAL_APPROVED` stay false.

## 1. Shape

One Next.js frontend, one FastAPI process, one Postgres database, and later one Dramatiq worker. No microservices and no Kubernetes for the MVP.

```
apps/web                 Next.js App Router. Staff UI. Anon Supabase key only.
services/api             FastAPI. Authn, RBAC, business rules, OpenAPI.
services/worker          Dramatiq. Introduced in Phase 3. Not in the web request.
packages/contracts       Hand-written Pydantic contracts (this phase).
packages/api-client      Generated TypeScript client. Created in Phase 1, not now.
data/                    Reference sheet and future fixtures. No personal contact data.
infra/docker-compose.yml Local Postgres 16 and Redis 7. Not started in Phase 0.
```

The prompt kit (`MASTER_PROMPT.md`, `PHASE_BY_PHASE_PROMPTS.md`, `README_START_HERE.md`, root `reference_accounts.json`) stays at the repository root. `data/reference_accounts.json` is the copy the product loads. A test fails if the two files diverge.

## 2. Request path

1. The browser holds a Supabase Auth session.
2. The web app calls FastAPI with `Authorization: Bearer`.
3. FastAPI verifies that JWT. For new Supabase projects the supported method is `auth.get_claims(jwt=...)`, which checks the project JWKS at `/.well-known/jwks.json` when signing is asymmetric. Symmetric projects fall back to the Auth server inside that same method. Do not authorize from `get_session()`; that reads storage without verifying the signature.
4. The JWT `role` claim is the Postgres role (`authenticated`), not an application role. Application role comes from `memberships` for the organization.
5. Repositories filter by `organization_id` on every read and write.
6. Long work (search, call-event handling) goes to the worker. A short HTTP request must not run a research crawl.

Direct Supabase client reads from the browser are not the MVP data path. If they are added later, RLS is a second fence, not the only one. The service-role key stays on the server.

## 3. Modules inside the API

When Phase 1 starts, keep these packages separate:

- `routers` — HTTP, status codes, dependency injection.
- `schemas` — request and response models, reusing `ngreen_contracts` where the shape is shared.
- `services` — review, dedupe, permission, CRM transitions.
- `repositories` — SQLAlchemy queries.
- `adapters` — search, model, voice, email. Each has a DEMO implementation.
- `jobs` — Dramatiq actors, idempotent and cancellable.

Empty adapter rule: if `SERPER_API_KEY` or `AI_API_KEY` is blank, the DEMO adapter runs and every result is marked `provider = demo`. The DEMO adapter must not pretend a live call or a live search succeeded. If a live adapter is selected and the provider errors, the run stores the error.

Voice: `VOICE_LIVE_ENABLED=false` in `.env.example`. `evaluate_live_call` in `ngreen_contracts.eligibility` is the fail-closed rule. It does not dial.

## 4. Research pipeline (Phase 3–4)

Planner → SearchAdapter → CompanyResolver → EvidenceExtractor → PackagingNeedClassifier → ContactResearcher → FitScorer → ReviewQueue → PromoteToCRM.

Phase 3 stops before the model extractor. Pages returned by search are untrusted data. They are stored as text evidence. They are not concatenated into a system prompt without a fixed instruction that the page cannot change tools, permissions, or CRM state.

Search uses a provider API (Serper first, interface replaceable by Tavily or a licensed source). No Google HTML scraping and no CAPTCHA bypass. Each source stores URL, snippet, retrieval time, and provider. Fetches block link-local, loopback, and private addresses, including redirects to those addresses.

## 5. Three independent states

These are different columns and different screens:

| State | Question it answers |
| --- | --- |
| Research review | Is this a real, non-duplicate company we want in the CRM? |
| Product need status | hypothesis, publicly evidenced, buyer confirmed, or rejected |
| Calling permission | May an automated promotional call be placed to this channel? |
| Opportunity stage | Where is the sales motion? |

`Outreach Eligible` requires a recorded permission basis. Won is a manual stage. A call insight can suggest a move; it cannot close an order. `insight_can_auto_mark_won` returns false.

## 6. Library pins checked on 17 November 2026

Phase 1 installs these. Phase 0 installed only Pydantic, pytest, and Ruff, because the app is not built.

| Piece | Pin | Note |
| --- | --- | --- |
| Node.js | 26.13.1 LTS | This machine has 24.21.0, which is behind the 11 Nov 2026 security release. Use 26.13.1 before Phase 1 frontend work. 24.22.3 is the patched 24.x line if 26 is unavailable. |
| Next.js | 16.4.6 | Current stable that day. App Router. |
| React / React DOM | 19.3.1 | Pair with Next 16. |
| Tailwind CSS | 4.3.5 | Next's scaffolder was still pinning 4.3.3 in the 16.4.6 notes. Upgrade to 4.3.5 after scaffold and recheck the build. |
| FastAPI | 0.163.1 | Requires Python >= 3.11. |
| Pydantic | 2.14.3 | Installed in Phase 0. |
| SQLAlchemy | 2.1.9 | Current 2.1 series. Read the 2.0 → 2.1 migration notes before writing models. 2.0.58 is maintenance-only. |
| Alembic | 1.20.1 | Works with SQLAlchemy >= 2.0. |
| psycopg | 3.3.9 | Use psycopg 3, not psycopg2. |
| supabase (Python) | 2.34.1 | Requires Python >= 3.11. JWT verification via `get_claims`. |
| Dramatiq | 2.2.1 | Phase 3. |
| pytest | 9.2.0 | Installed in Phase 0. |
| Ruff | 0.17.5 | Installed in Phase 0. |
| httpx | 0.28.1 | Phase 1 API tests. supabase 2.34.1 allows httpx >= 0.26 and < 0.29. |

Not pinned yet, on purpose:

- Zod. npm showed 4.6.7. React Hook Form resolvers may still expect Zod 3. Phase 1 tries Zod 4, and if types fail, pins the current Zod 3 and records why.
- TanStack Query, shadcn/ui, Lucide, Vitest, Playwright, mypy, pnpm. Confirm the current stable versions at install time. A November 2026 lockfile bump referenced `@tanstack/react-query` 5.107.x and Vitest 5.1.0; recheck npm rather than floating.

Python for CI in this phase is 3.12, which matches the spec. The workstation used for the Phase 0 tests has Python 3.14.7 only. See decisions.

## 7. Local runtime

Phase 0 command path is in `README.md`. Docker Desktop and pnpm were not installed on the Phase 0 machine, so Compose was not started and the web app was not scaffolded. That is expected: both belong to Phase 1.

## 8. Deployment, later

Frontend on a Node host such as Vercel. API and worker on a container host. Postgres and object storage on Supabase. Redis managed. Secrets in the host's secret store. No long research job inside a serverless API timeout. Production deploy is Phase 9 and still needs a separate approval.
