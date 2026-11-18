# N Green LeadOS

Sales-research, CRM, and permission-gated calling for one sustainable-packaging team. Research looks for businesses that may buy packaging, and leaves packaging suppliers out. Calls can be rehearsed offline. The live Vapi adapter is installed and marked disabled.

The build rules are in `MASTER_PROMPT.md`. Staging, production, and a real call each need a separate instruction. Do not start a later integration phase from this handover.

## What runs today

- DEMO staff sign-in, with the role stored on the organization membership
- Overview counts read from the database
- 11 products, 17 industries, and 20 unverified reference targets
- Manual account create, view, edit, tags, notes, product needs, and contacts the team types in
- CRM board with recorded stage reasons. Outreach Eligible requires a known permission basis
- CSV preview, commit, duplicate review, and formula-safe export
- Research runs with a review queue. Empty `SERPER_API_KEY` uses DEMO fixtures on example.com
- Official-page business emails, a permission record, and opt-out. Unknown permission blocks a live call
- DEMO call rehearsal. Accepting a note can add a task. An opt-out blocks the next rehearsal
- Live call start. It returns 403 until legal approval and one named test contact are set
- Follow-ups with a due date and an owner. Overdue is calculated in India time
- Reports for the owner, a manager, or a reader. Counts come from the database. Ratios are omitted when there is nothing to divide. The report does not estimate revenue
- Contact export and erasure for an owner or a manager. The suppression hash remains
- SQLite backup and restore commands in `docs/RUNBOOK.md`

A public email is not permission to call. A search result is not a verified buyer. Live dialing is disabled.

## Windows PowerShell

Tested with Python 3.14.7 and Node v24.21.0. pnpm is run through Corepack (`corepack pnpm`). Docker is not installed, so the running database is SQLite. Postgres remains the Compose target.

```powershell
cd C:\Users\PC\Desktop\ajay-freelance\N_Green_Agent_Build_Kit
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests
.\.venv\Scripts\python -m pytest -q

Copy-Item .env.example .env
New-Item -ItemType Directory -Force data | Out-Null
.\.venv\Scripts\python -m uvicorn ngreen_api.main:app --app-dir services/api --reload --port 8000

# second terminal
cd apps\web
Copy-Item .env.example .env.local
corepack pnpm install
corepack pnpm dev
```

Open `http://localhost:3000/login`. Use localhost rather than 127.0.0.1 so the dev page hydrates. DEMO staff use password `demo-pass`. The owner address is `owner@ngreen.demo`. A read-only sign-in is `reader@ngreen.demo`. A sales sign-in is `sales@ngreen.demo`. Researcher import is `researcher@ngreen.demo`.

Leave provider keys empty. Do not commit `.env`.

## Machine limits

- Node.js is v24.21.0, behind the 11 November 2026 security release (26.13.1 or 24.22.3).
- Docker is not installed, so `infra/docker-compose.yml` was not started.
- Supabase is not configured. Sign-in is the DEMO issuer.

## Docs

| File | Contents |
| --- | --- |
| `docs/PRD.md` | Scope, personas, the 20 targets, non-goals |
| `docs/ARCHITECTURE.md` | Processes, auth, library pins |
| `docs/ERD.md` | Logical tables |
| `docs/SECURITY_AND_COMPLIANCE.md` | Auth, calling, privacy |
| `docs/DECISIONS.md` | Phase 0 decisions |
| `docs/PHASE_PLAN.md` | Later phases and risks |
| `docs/SCREEN_MAP.md` | Routes |
| `docs/API_CONTRACT.md` | Planned routes, not implemented |
| `docs/PROGRESS.md` | What this phase actually ran |
| `docs/RUNBOOK.md` | Local start, backup, erasure, and rollback |
| `docs/HANDOVER.md` | What is ready and what is still blocked |
| `docs/SECURITY_REVIEW.md` | Phase 9 review and unresolved risks |

## Layout

```
apps/web/                  Next.js staff UI
services/api/              FastAPI auth, overview, accounts
services/worker/           Dramatiq entrypoint; local runs use an in-process thread
packages/contracts/        Pydantic contracts
data/reference_accounts.json
docs/
infra/docker-compose.yml
```
