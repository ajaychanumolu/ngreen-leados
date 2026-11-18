# Operating runbook

Local only. Staging was not authorized, so nothing in this file was deployed.

## Start

```powershell
cd C:\Users\PC\Desktop\ajay-freelance\N_Green_Agent_Build_Kit
.\.venv\Scripts\python -m uvicorn ngreen_api.main:app --app-dir services/api --port 8000
```

In a second terminal:

```powershell
cd C:\Users\PC\Desktop\ajay-freelance\N_Green_Agent_Build_Kit\apps\web
corepack pnpm dev
```

Open `http://localhost:3000/login`. DEMO password is `demo-pass`. Owner is `owner@ngreen.demo`. Reader is `reader@ngreen.demo`.

`GET http://127.0.0.1:8000/health` should return `status: ok`. It must not contain a provider key. `voice_mode` stays `disabled` until legal approval and one named test contact are both set.

## Stop a live call

Leave `VOICE_LIVE_ENABLED` and `VOICE_LEGAL_APPROVED` false and restart the API. `POST /api/v1/calls/start` then returns 403. Do not set those flags to try a call.

## Backup the local database

Stop the API so the file is not being written. From the repository root:

```powershell
$env:PYTHONPATH = "services/api"
.\.venv\Scripts\python -c "from pathlib import Path; from ngreen_api.backup import backup_sqlite; backup_sqlite(Path('data/local-leados.db'), Path('data/local-leados-backup.db'))"
```

Restore only after stopping the API, and only onto a copy you can afford to replace:

```powershell
$env:PYTHONPATH = "services/api"
.\.venv\Scripts\python -c "from pathlib import Path; from ngreen_api.backup import restore_sqlite; restore_sqlite(Path('data/local-leados-backup.db'), Path('data/local-leados.db'))"
```

Postgres backup, when Docker is available, is `pg_dump` of the Compose database. That command was not run here.

## Erase one contact

An owner or a manager calls `POST /api/v1/privacy/contacts/{id}/erase`. The address, phone, and rehearsal transcript are removed. The suppression hash remains, so the same address cannot be rehearsed again. The audit row does not store the address.

`GET /api/v1/privacy/contacts/{id}` exports the stored personal fields before an erasure. Sales, researcher, and read-only accounts receive 403.

## Migration rollback

On a copy of the database, not the live file:

```powershell
$env:DATABASE_URL = "sqlite:///./data/rollback-copy.db"
.\.venv\Scripts\python -m alembic -c services/api/alembic.ini downgrade 0005_contacts
.\.venv\Scripts\python -m alembic -c services/api/alembic.ini upgrade head
```

Downgrade removes the call tables from that copy. Upgrade puts them back. It does not restore rows that were only in those tables.

## When something fails

- Search error on a run: the run stays failed and the Reports retry queue links to it. Retry spends a credit only when a search key is set. Do not retry just to see the button.
- Sign-in 429: wait a minute. The limit is 10 attempts per email per minute.
- Research 429: the organization started more than 5 runs in a minute.
- Health `research_mode: live` means a search key is present. It does not mean a search just ran.

## Logs

The API writes `method path status` on logger `ngreen.access`. The path has an email or E.164 number replaced. Do not add the request body to that line.
