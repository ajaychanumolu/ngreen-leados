# Security, privacy, and compliance

Status: Phase 9 review is in `docs/SECURITY_REVIEW.md`. The operating steps are in `docs/RUNBOOK.md`. Staging was not deployed.

## Authentication and authorization

- Every API route except health requires a verified staff JWT.
- Application RBAC is loaded from `memberships`. The Supabase JWT `role` claim is not an application role.
- Verify tokens with `get_claims` (JWKS for asymmetric keys). Do not trust `get_session` on the server.
- The service-role key never ships to the browser. `.env.example` names it as server-only and leaves it empty.
- Organization id on the token or membership is applied in queries. A user cannot pass another organization's id and read its rows.
- Read-only users do not get write or call routes.

## Calling and telecom

- `VOICE_LIVE_ENABLED` defaults to false.
- `evaluate_live_call` denies the attempt when the flag is off, the role cannot authorize, the number is not E.164, the basis is unknown, DNC or suppression is set, permission was revoked, or permission is expired.
- A public web page that shows a phone number is not consent.
- Do-not-call on a call insight is an immediate suppression, implemented in Phase 6.
- Before any real outbound promotional call in India, a qualified person reviews TRAI TCCCPR / commercial communication rules, sender registration, DNC, calling hours, recording consent, and the voice provider's terms. Official references named by the spec: PIB release `https://www.pib.gov.in/PressReleasePage.aspx?PRID=2311989` and the TRAI regulation PDF linked from `https://www.trai.gov.in/sites/default/files/2025-02/Regulation_12022025.pdf`. This repository does not summarize those documents as legal advice and does not implement a way around them.
- Phase 7 still requires a named test contact and a separate approval before a real dial.

## Data that must not be invented

- No fabricated phone numbers, emails, personal names, volumes, or "uses plastic" facts in seeds, fixtures, or model output.
- Reference companies carry the label `Reference target – not verified`.
- Fit score components with no evidence are zero.
- Web pages are evidence text. Instructions inside a page cannot change the system prompt, grant permission, or write CRM stage Won.

## Input and output safety

- Pydantic validation and length limits on write APIs.
- Server-side pagination (`page_size` max 100 in the contract).
- Parameterized SQL through SQLAlchemy.
- CSV export neutralizes formula injection (`=`, `+`, `-`, `@` at the start of a cell).
- Upload types and sizes restricted. Attachments in private storage, organization-scoped, served by signed URL.
- SSRF: resolve and block loopback, private, and link-local destinations before fetch and after each redirect.
- Rate limits on auth, import, research start, and call start.
- CORS limited to the staff web origin. Cookie auth, if used, gets CSRF protection. Bearer tokens are the expected API scheme.
- Provider webhooks: HMAC or the provider's signed mechanism, timestamp, and replay rejection. The posted outcome is not trusted until the signature matches and the permission snapshot is reloaded.
- Logs do not contain phone numbers, emails, tokens, or raw transcripts. Usage logs store counts and cost estimates.

## Secrets and retention

- `.env` is gitignored. `.env.example` has empty provider keys.
- Phase 0 tests refuse a non-empty `SERPER_API_KEY` or `VAPI_API_KEY` line in the example file.
- Personal data export and erasure are `GET` and `POST /api/v1/privacy/contacts/{id}`. An owner or a manager can run them. Erasure removes the address, phone, and transcript and keeps the suppression hash. Audit rows keep the action and do not store the address.
- Recordings and transcripts exist only when consent and provider settings allow, with a retention period in settings.

## Known gaps at the end of Phase 0

- No running authentication, database, RLS, or webhook endpoint.
- Docker and a Supabase project are not configured.
- The earlier LeadOS demo was not in the repo, so its SQLite file and any hardcoded secrets could not be reviewed. Do not import that zip later without a fresh pass for auth, secrets, and invented contact data.
- Legal review of outbound calling has not been done. Live calling remains disabled.
