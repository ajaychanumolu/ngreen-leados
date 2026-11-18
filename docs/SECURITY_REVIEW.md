# Security review

Date: 17 November 2026. This is a review of the code in this folder. It is not a penetration test and it is not legal advice. Staging was not deployed. No prospect was contacted.

## What was checked

| Control | Result |
| --- | --- |
| Authenticated routes | `/health` and `POST /api/v1/auth/demo/login` are public. Other `/api/v1` routes use `get_actor` and return 401 without a bearer token. |
| Tenant isolation | Queries filter on the membership organization. A second organization cannot read the first organization's account. Covered by `test_patch_and_other_organization_cannot_read`. |
| SSRF | Research stores the provider URL and does not fetch it. Loopback, private, and link-local hosts are dropped before storage. |
| Prompt injection | A quote scores only when it is a substring of a stored snippet. Instruction text in a snippet does not grant permission or mark an opportunity won. |
| Do-not-call | Unknown permission, revocation, suppression, expiry, a bad number, and the live flag all fail closed. Erasing a contact keeps the channel hash, and a new row with the same address cannot be rehearsed. |
| Webhooks | The shared secret is compared in constant time. A timestamp older than five minutes is rejected. The same provider call id and event id are stored once. |
| Live calling | `POST /api/v1/calls/start` returns 403 while legal approval, the live flag, caller identity, or the named test contact is missing. |
| Secrets | Health returns modes, not key values. Access logs record method, path, and status. The path is scrubbed for an email or E.164 number, and the query string is not logged. |
| CSV | Export cells that start with `=`, `+`, `-`, or `@` are prefixed. |
| Backup | `backup_sqlite` and `restore_sqlite` round-trip a SQLite file in tests. Postgres `pg_dump` was not run. |
| Migrations | Revision `0006_calls` downgrades to `0005_contacts` and upgrades again on a temporary database. |
| Browser | Playwright signs in as the DEMO reader and opens Overview. It does not create an account. |

## Unresolved

- The DEMO session cookie is set from the browser so it can be read by script. A cross-site script on this origin could copy it. The app does not load a third-party script.
- The local database is a SQLite file. It is not encrypted. Postgres in Docker was not started.
- Row security inside Supabase is not in force. The API is the data path. A future browser query against Supabase would need its own policies.
- Login and research starts are rate limited. Other write routes are not.
- The short health loop in tests is not a production load test.
- Caller-ID registration, TRAI review, and a named test contact are still missing. Live calling stays disabled.
- This machine is on Node v24.21.0. The 11 November 2026 Node security release is not installed.
- GitHub Actions was not executed from this machine. The workflow file includes the API tests, the web typecheck, and the Playwright job.
