# Research worker

The API default is `RESEARCH_WORKER=inline`. Each search runs in a daemon thread inside the API process. That is the local path because Redis is not running on this machine.

Tests set `RESEARCH_WORKER=sync` so the run finishes inside the request.

`RESEARCH_WORKER=redis` imports Dramatiq only when a run is queued. Dramatiq 2.2.1 is not installed in the local environment. If the import or the Redis handoff fails, the API runs the same thread and does not pretend the provider succeeded.

When Redis is up and Dramatiq is installed:

```powershell
cd C:\Users\PC\Desktop\ajay-freelance\N_Green_Agent_Build_Kit
$env:PYTHONPATH = "services/api;services"
.\.venv\Scripts\python -m dramatiq worker.tasks
```

The actor is `research_run` on the queue `research`. It calls `execute_run`. The worker module is not imported by the API, so a missing Dramatiq package does not stop DEMO search.
