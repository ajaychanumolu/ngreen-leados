# API plan

Status: Phase 9 adds contact export and erasure, an audit list, and keeps live calling disabled. `POST /api/v1/calls/start` still returns 403 until legal approval, the live flag, caller identity, and one named test contact are all set. A report is not a revenue forecast.

Base path: `/api/v1`. Errors use `ApiErrorBody`: `code`, `message`, optional `request_id`. Lists use `Page`: `items`, `page` >= 1, `page_size` 1–100, `total` >= 0.

| Method and path | Phase | Behavior when it exists |
| --- | --- | --- |
| `GET /health` | 1 | Process up. No secrets. |
| `GET /api/v1/me` | 1 | Verified user, organization, application role. 401 if the JWT fails. |
| `GET/POST /api/v1/accounts` | 2 | Organization-scoped page. Create requires researcher, sales, manager, or admin. |
| `GET/PATCH /api/v1/accounts/{id}` | 2 | Patch records an audit row. |
| `GET/POST /api/v1/accounts/{id}/product-needs` | 2 | Need status defaults to `hypothesis`. |
| `POST /api/v1/imports/preview` | 2 | No write. Returns row errors and duplicate candidates. |
| `POST /api/v1/imports/commit` | 2 | Writes only rows the preview accepted, or reports a partial failure. |
| `POST /api/v1/research/runs` | 3 | Caps for queries, pages, and spend. DEMO when the search key is empty. |
| `GET /api/v1/research/runs/{id}` | 3 | Progress, cost, errors. |
| `POST /api/v1/research/runs/{id}/cancel` | 3 | Cancel while queued or running. A second cancel of the same run returns that cancelled run. |
| `POST /api/v1/research/runs/{id}/retry` | 3 | Re-queue a failed, cancelled, or capped run. Queries that already succeeded are not repeated. |
| `GET /api/v1/research/candidates` | 3 | Review queue. |
| `POST /api/v1/research/candidates/{id}/review` | 3 | Approve, reject, or merge. Merge requires a target id. |
| `GET/POST /api/v1/contacts` | 2 | Staff-typed name and channel, plus emails found on an official page. No invented numbers. |
| `POST /api/v1/contacts/discover` | 5 | Official-domain emails from search snippets. Empty search key stores nothing. |
| `POST /api/v1/contacts/{id}/permissions` | 5 | Records basis, scope, expiry, actor. Unknown basis is rejected. Opt-out cannot be overridden. |
| `POST /api/v1/contacts/{id}/opt-out` | 5 | Marks do-not-call and stores a channel hash. |
| `POST /api/v1/calls/simulate` | 6 | DEMO transcript only. Requires recorded permission. Does not dial. |
| `POST /api/v1/calls/{id}/review` | 6 | Accept writes one task and a stage reason. Reject writes neither. |
| `POST /api/v1/integrations/voice/webhook` | 6 | Requires `X-Demo-Voice-Signature`. The same call id and event id are stored once. |
| `POST /api/v1/calls/start` | 7 | One contact. Returns 403 while live calling is disabled. No batch. |
| `POST /api/v1/integrations/voice/webhook` | 6 shape, 7 signatures | Idempotency key is provider call id + event id. Unsigned events are rejected. |
| `GET/POST/PATCH /api/v1/opportunities` | 2 | Value may be null. |
| `PATCH /api/v1/opportunities/{id}/stage` | 2 | Requires a reason. `outreach_eligible` checks permission. `won` is not set by a model. |
| `GET/POST/PATCH /api/v1/tasks` | 2, follow-ups in 8 | Due date, owner on this team, and `overdue=true` for open tasks before today in Asia/Kolkata. |
| `GET /api/v1/team` | 8 | Names and roles in the caller's organization. |
| `GET /api/v1/reports/funnel` | 8 | Stage counts, age, yield, credits, fit, alerts, and retry queue. Owner, manager, or read-only. Ratios are null when the count underneath is zero. |
| `GET /api/v1/reports/spend` | 8 | Provider usage rows. Same roles as the funnel. |
| `GET /api/v1/reports/export` | 8 | CSV of the same counts. Formula characters are prefixed. |
| `GET /api/v1/privacy/contacts/{id}` | 9 | Personal fields and rehearsal transcripts. Owner or manager. |
| `POST /api/v1/privacy/contacts/{id}/erase` | 9 | Removes those fields and the transcript. Keeps the suppression hash. |
| `GET /api/v1/audit` | 9 | Staff actions for the organization. The summary does not include the address. |

Shared models already in code: `CallInsight`, `FitScore`, `ReferenceCatalog`, `LiveCallDecision`, `Page`, `ApiErrorBody`.

OpenAPI generation starts when Phase 1 has `/health` and `/api/v1/me`. The TypeScript client lands in `packages/api-client`.
