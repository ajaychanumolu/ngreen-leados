# Progress

## Phase 9 — complete, stopped

Date: 17 November 2026.

The review covered authentication, organization scope, SSRF, snippet quotes, do-not-call, webhooks, and the live-call refusal. An owner or a manager can export one contact and erase the address, phone, and rehearsal transcript. The suppression hash remains, and a new row with the same address cannot be rehearsed. SQLite backup and restore round-trip in a test. The call-table migration downgrades to the contact revision and upgrades again on a temporary file. Playwright signs in as the DEMO reader and opens Overview. Staging was not deployed. No number was dialed, and no search credit was spent.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests
All checks passed!

.\.venv\Scripts\python -m pytest -q
64 passed, 1 warning in 120.41s
```

The warning is Starlette noting `httpx` versus `httpx2`.

```text
corepack pnpm typecheck
corepack pnpm lint
corepack pnpm e2e
```

Typecheck and lint finished with exit code 0 in `apps/web`. Playwright reported `2 passed`.

### Not verified

- GitHub Actions was not executed from this machine. The workflow includes the Playwright job.
- Postgres `pg_dump` was not run. Docker is not installed.
- A production load test was not run. The API test repeats health 20 times on the local process.
- Staging was not authorized, so nothing was deployed.
- Live calling stays disabled.

The handover list is `docs/HANDOVER.md`. The operating steps are `docs/RUNBOOK.md`.

STOP: This is the last planned phase. Staging, production, and a real call each need a separate instruction.

## Phase 8 — complete, stopped

Date: 17 November 2026.

Reports read pipeline stage, stage age, research yield, fit scores, rehearsals, overdue tasks, team ownership, provider usage, and the research retry queue from stored rows. A ratio is omitted when the denominator is zero. Opportunity amounts are not summed, and the screen does not estimate revenue. A task due date is the follow-up. Overdue is calculated in India time when the list is read. Sales and researcher accounts cannot open the report. No number was dialed, and this phase did not spend a search credit.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests
All checks passed!

.\.venv\Scripts\python -m pytest -q
58 passed, 1 warning in 80.98s
```

The warning is Starlette noting `httpx` versus `httpx2`.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

### Not verified

- The retry control on a failed run was not clicked. Opening it from Reports only links to the existing run page.
- Live calling stays disabled. No named test contact was approved.

STOP: Await APPROVE PHASE 9.

## Phase 7 — complete, stopped

Date: 17 November 2026.

The Vapi adapter can send one call to `https://api.vapi.ai/call` with one customer number. That path is not used. Legal and telecom approval is missing, the live flag is off, and no named test contact is approved, so every start returns 403 and the sandbox provider sends nothing. Calling hours are weekdays 09:00–18:00 India time. The daily cap and the in-flight cap are both 1. A webhook needs the shared secret, a timestamp older than five minutes is rejected, and the same provider event is stored once. An opted-out contact cannot be dialed even if the live flags are turned on. No number was dialed.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests
All checks passed!

.\.venv\Scripts\python -m pytest -q
56 passed, 1 warning in 79.33s
```

The warning is Starlette noting `httpx` versus `httpx2`.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

### Not verified

- Vapi was not called. No named test contact was approved, and legal approval is still missing.
- Caller-ID registration with the phone carrier was not done. The caller-number id is empty, which is one of the reasons a start is refused.

STOP: Await APPROVE PHASE 8.

## Phase 6 — complete, stopped

Date: 17 November 2026.

Research queries now look for businesses that may buy sustainable packaging. Packaging suppliers, manufacturers, and seller directories are left out of the candidate list. DEMO call rehearsal stores a transcript, parses an outcome, and waits for a person to accept the note before a task or CRM stage changes. An opt-out is applied immediately and blocks the next rehearsal. Replaying the same signed webhook does not create a second call. `POST /api/v1/calls/start` stays unavailable. No number is dialed.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests
All checks passed!

.\.venv\Scripts\python -m pytest -q
51 passed, 1 warning in 76.80s
```

The warning is Starlette noting `httpx` versus `httpx2`.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

### Not verified

- A Bengaluru query returned tender-listing sites, and a Hyderabad query still returned two bag catalogs that mention restaurants. Both sets were rejected. Catalog pages are now left out even when they name a restaurant or hotel. The next search from the Research screen uses that filter.
- Vapi was not called. `VOICE_LIVE_ENABLED` stays false.

STOP: Await APPROVE PHASE 7.

## Phase 5 — complete, stopped

Date: 17 November 2026.

Serper and Groq are wired from `.env`. Contact research stores an email only when the snippet is on that mailbox's own public site. Personal mail, directories, and phones from search are dropped. Permission stays unknown. Opt-out is hashed and cannot be overridden. `evaluate_live_call` blocks every live call while `VOICE_LIVE_ENABLED` is false. There is no call route.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests services\worker
All checks passed!

.\.venv\Scripts\python -m pytest -q
48 passed, 1 warning in 25.63s
```

The warning is Starlette noting `httpx` versus `httpx2`.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

`GET /health` reported `research_mode` live, `ai_mode` live, and `worker` inline. One Carry Bags search for Pune completed on Serper (1 credit, 2 new candidates, both labeled not a verified buyer). Groq model `openai/gpt-oss-20b` scored those snippets. The first call was rejected by Cloudflare as error 1010 because the Python client sent no user agent; the request now sends `ngreen-leados/0.1`, and the stored error is empty. A quote that was not in the snippet was dropped, and product fit stayed 0 where the snippet did not cite the product. Discovering contacts for Zepto stored one mailbox from `www.zepto.com` with permission unknown, no phone, and `call_allowed` false. `POST /api/v1/calls/start` returned 404.

### Not verified

- A second Groq model was not tried. The configured model is the one that scored the snippets.
- Redis, Dramatiq, Docker, and Supabase are still absent. No call was placed.

STOP: Await APPROVE PHASE 6.

## Phase 4 — complete, stopped

Date: 17 November 2026.

The header uses a sharp badge and the words N Green / Sustainable Packaging. The soft wordmark image is no longer in the shell. Research skips companies already saved or already returned. Each new candidate gets a fit score whose points come only from quotes found in stored snippets. Unsupported and injected quotes are dropped. DEMO fixtures score 0. A model key is optional; without it the classifier is mock and does not call the network.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests services\worker
All checks passed!

.\.venv\Scripts\python -m pytest -q
45 passed, 1 warning in 20.34s
```

The warning is Starlette noting `httpx` versus `httpx2`.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

### Not verified

- Serper was not called. Add `SERPER_API_KEY` to `.env` and restart the API for live search.
- OpenAI was not called. Live quotes need `AI_PROVIDER=openai` and `AI_API_KEY` in `.env`. Quotes that are not in a stored snippet are still discarded.
- Redis, Dramatiq, Docker, and Supabase are still absent. Calling is still off.

STOP: Await APPROVE PHASE 5.

## Phase 3 — complete, stopped

Date: 17 November 2026.

Company discovery is a review queue. With `SERPER_API_KEY` empty, runs are DEMO fixtures on example.com. A provider error fails the run and stores no companies. Approving a candidate creates an account with no industry and no contacts. The client's wordmark is in the sidebar and on the login page. The geometric N is the favicon.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests services\worker
All checks passed!

.\.venv\Scripts\python -m pytest -q
42 passed, 1 warning in 17.42s
```

The warning is Starlette noting `httpx` versus `httpx2`. Tests still pass. The three new tests cover a labeled DEMO run, a budget refusal, a provider outage, a rate limit, cancel, a private URL dropped from a faked live response, and a second cancel of the same run.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

Browser check on `http://localhost:3000` as the DEMO owner:

- The header shows the green N Green Sustainable Packaging wordmark. The badge reads DEMO sign-in · local database · DEMO search.
- Overview counts stayed 21 accounts, 20 reference targets, 21 opportunities, and 0 manual contacts before a candidate was accepted. The research queue is a real pending count.
- A Carry Bags search for Hyderabad, limited to 2 companies, completed on the inline worker. The first query was ok. The other two were skipped because the company limit was reached. Both candidates were labeled "Research candidate – not a verified buyer" and linked to example.com.
- Accepting DEMO North Depot opened an account: web research, review approved, industry unassigned, Carry Bags at hypothesis, and no manual contacts.

### Not verified

- GitHub Actions was not executed from this machine.
- Docker Compose and Redis were not started. The live worker is the in-process thread.
- Serper was not called. Put a key in `.env` as `SERPER_API_KEY` only if you want the badge to switch to live search. Leave it empty to stay on DEMO.
- Dramatiq 2.2.1 is not installed. `RESEARCH_WORKER=redis` falls back to the same thread if that handoff fails.
- Supabase Auth was not exercised. Calling is still off.

STOP: Await APPROVE PHASE 4.

## Phase 2 — complete, stopped

Date: 17 November 2026.

Manual CRM is running: 11 products, 17 industries, 20 unverified reference targets, opportunity board, manual contacts, tasks, and CSV preview/commit/export. Research and calling are not started.

### Commands and observed output

```text
.\.venv\Scripts\python -m ruff check packages\contracts\src services\api tests
All checks passed!

.\.venv\Scripts\python -m pytest -q
39 passed, 1 warning in 13.80s
```

The warning is Starlette noting `httpx` versus `httpx2`. Tests still pass.

```text
corepack pnpm typecheck
corepack pnpm lint
```

Both finished with exit code 0 in `apps/web`.

Browser check on `http://localhost:3000` as the DEMO owner:

- Overview read 21 accounts, 20 reference targets, 21 opportunities, and 0 manual contacts from the database.
- Accounts listed Amazon and Amazon Fresh as separate rows. Reference rows show `Reference target – not verified`.
- Zepto is unassigned to an industry, has four product hypotheses, and has no contacts.
- CRM shows Research · 21. Other stages are empty.
- Import preview of an empty name plus Medplus reported Ready 0, Errors 1, Duplicates 1, and did not write.

### Not verified

- GitHub Actions was not executed from this machine.
- Docker Compose was not started. The live process uses SQLite and the screen says "local database".
- Supabase Auth was not exercised. `SUPABASE_URL` is empty, so sign-in is DEMO.
- No provider key is required for this phase, so none was added.

STOP: Await APPROVE PHASE 3.

## Phase 1 — complete

Staff sign-in, organization role, overview count, and account create/read/update. The first browser check created the manual account Harbour Paper, which is still in the local database.
