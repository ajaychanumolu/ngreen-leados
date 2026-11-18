"""Optional Redis handoff. Importing Dramatiq is deferred until a Redis worker is configured."""

from __future__ import annotations


def send_run(run_id: str) -> None:
    import dramatiq
    from dramatiq.brokers.redis import RedisBroker

    from ngreen_api.research_jobs import execute_run
    from ngreen_api.settings import get_settings

    broker = RedisBroker(url=get_settings().redis_url)
    dramatiq.set_broker(broker)

    @dramatiq.actor(queue_name="research", max_retries=0)
    def research_run(queued_id: str) -> None:
        execute_run(queued_id)

    research_run.send(run_id)
