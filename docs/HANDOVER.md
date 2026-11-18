# Handover

Date: 17 November 2026. Production and staging were not deployed. Contacting a real prospect still needs a separate approval.

## Ready for a local pilot

- [x] Staff sign-in, roles, and organization scope
- [x] Manual CRM, reference targets labeled unverified, and CSV preview
- [x] Research queue with source links, buyer filter, and fit scores that cite snippets
- [x] Public business email only from the company's own page, permission unknown until a person records it
- [x] DEMO call rehearsal, human accept before a CRM write, opt-out blocks the next rehearsal
- [x] Live call route installed and refusing every start
- [x] Reports from stored rows, with empty ratios when a count is zero
- [x] Contact export and erasure for an owner or a manager
- [x] SQLite backup and restore functions, with a test
- [x] Migration down to the contact revision and back up, on a temporary file
- [x] Playwright sign-in of the DEMO reader
- [x] CI workflow for API tests, web lint, and Playwright

## Still blocked

- [ ] Legal and telecom review before any real call
- [ ] One named test contact and the exact number, approved in writing
- [ ] Caller-number id, assistant id, and webhook secret filled in outside git
- [ ] Staging host. Deploy only after a separate instruction
- [ ] Postgres started from Docker. This machine does not have Docker
- [ ] Node upgraded to the 11 November 2026 security release
- [ ] A production load test against a staging host
- [ ] Supabase row policies, if the browser ever reads Supabase directly

## Do not do these without a new approval

- Set `VOICE_LIVE_ENABLED` or `VOICE_LEGAL_APPROVED`
- Dial a number, including a test number
- Run another paid search
- Deploy this folder to a public host
- Commit `.env`
