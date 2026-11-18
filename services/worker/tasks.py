"""Dramatiq entrypoint for research runs.

Start Redis, then from the repo root:

    .\\.venv\\Scripts\\dramatiq services.worker.tasks

The API falls back to an in-process thread when Redis or Dramatiq is unavailable.
"""

from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from ngreen_api.research_jobs import execute_run
from ngreen_api.settings import get_settings

dramatiq.set_broker(RedisBroker(url=get_settings().redis_url))


@dramatiq.actor(queue_name="research", max_retries=0)
def research_run(run_id: str) -> None:
    execute_run(run_id)
