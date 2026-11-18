# Phase plan

Phase 9 is in the local app. Staging was not deployed. Estimates below are planning assumptions, not a commitment.

| Phase | What it adds | Exit | Assumption |
| --- | --- | --- | --- |
| 0 | Audit, docs, contracts, skeleton | This folder, tests green, no product UI | Done in this change |
| 1 | Next.js shell, FastAPI, Postgres, auth, RBAC, CI | Staff login, empty overview from the API, account route skeleton | About a week after Node 26, pnpm, Docker, and a Supabase project exist |
| 2 | Taxonomy, 20 targets, manual CRM, CSV | Import a 50-row fixture, duplicates caught, no invented contacts | 1–2 weeks |
| 3 | Serper or DEMO search, worker, review queue | Real links when a key exists; labeled DEMO when it does not; outages stay errors | 1–2 weeks |
| 4 | Planner, extractor, fit score, citations | Unsupported claims flagged; people approve before CRM | About 2 weeks |
| 5 | Public business contacts and permission ledger | Unknown permission cannot enter a live queue | 1–2 weeks |
| 6 | Mock voice, insights, tasks, idempotent events | Two scripted flows, no network call | 1–2 weeks |
| 7 | Real voice adapter, still default off | One approved test call only after legal review and a named contact | Blocked on credentials and counsel |
| 8 | Tasks, funnel, cost, ageing | Charts match the database, including empty states | 1–2 weeks |
| 9 | Hardening, e2e, backup, staging if approved | Handover checklist. Production and real prospect contact are separate approvals | 1–2 weeks |

## Gate

Phase 9 is the last phase in this plan. Staging, production, and a real call each need a separate instruction. A live call still needs legal approval and one named test contact.

Phase 1 prerequisites the user or the machine still needs:

- Node.js 26.13.1 (workstation is on 24.21.0).
- pnpm (absent).
- Docker Desktop with Linux containers (absent), or another Postgres the user names.
- A Supabase project, or an explicit decision to use local auth for the first milestone. The spec selects Supabase Auth. Do not invent a project URL.

## Scenario ownership

See the table in `docs/PRD.md`. Phase 0 covers scenario 8 only as a pure function, and scenario 13 only as the empty-key policy in `.env.example`.

## Risks

| Risk | Why it matters | Mitigation in force now |
| --- | --- | --- |
| Missing MVP zip | Useful code or unsafe secrets might appear later | Do not import it without a new review |
| Missing PDF and screenshot | Scope could be argued from unseen pages | Master spec wins; JSON is the only company/product source |
| Industry guessing | Would present a hypothesis as a category fact | Industry left null |
| Accidental merge of business units | Amazon and Amazon Fresh would collapse | Normalization test and separate-name rule |
| Live call before legal review | Regulatory and consent failure | Flag default false; eligibility function fail-closed |
| Prompt injection from search results | A page could try to steer the model | Planned untrusted-data boundary; not built yet |
| SSRF from discovered URLs | Research fetch could hit internal hosts | Phase 3 stores the provider URL and does not fetch it. Private and loopback hosts are dropped |
| JWT role confused with app role | Everyone would look like `authenticated` | Documented; enforced when auth is built |
| Python 3.14 vs CI 3.12 | Local green might miss a 3.12-only failure | CI workflow targets 3.12; it has not run on GitHub |
| Node 24.21.0 | Misses the 11 Nov 2026 security release | Phase 1 upgrades before `create-next-app` |
| Zod 4 vs form resolvers | Phase 1 install could break types | Decision D-009 |
| Provider keys in git | Cost and data exposure | Example file empty; test locks that |
| Scope creep into ERP | Delays the sales MVP | Non-goals written in the PRD |
