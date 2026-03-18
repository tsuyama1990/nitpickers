import asyncio
import random
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar

import httpx

from src.domain_models.config import DispatcherConfig
from src.domain_models.manifest import CycleManifest
from src.utils import logger

T = TypeVar("T")


def retry_on_429(config: DispatcherConfig) -> Callable[..., Any]:
    """Decorator to retry API requests on HTTP 429 Too Many Requests errors."""

    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and retries < config.max_retries:
                        retries += 1
                        # Exponential backoff with jitter
                        sleep_time = (config.retry_backoff_factor ** retries) + random.uniform(1, 3)  # noqa: S311
                        logger.warning(
                            f"HTTP 429 encountered in {func.__name__}. Retrying in {sleep_time:.2f} seconds (Attempt {retries}/{config.max_retries})."
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        raise

        return wrapper

    return decorator


class AsyncDispatcher:
    def __init__(self, config: DispatcherConfig | None = None) -> None:
        self.config = config or DispatcherConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

    def resolve_dag(self, manifests: list[CycleManifest]) -> list[list[CycleManifest]]:
        """
        Groups cycles into independent batches based on dependencies.
        Returns a list of batches, where each batch can be executed concurrently.
        Assumes valid DAG with no cycles.
        """
        # Track completed cycles (or those that we are simulating as completed in our batching)
        # We start with any cycle that is already completed.
        completed_ids = {c.id for c in manifests if c.status == "completed"}

        # Track remaining cycles to schedule
        remaining = [c for c in manifests if c.status != "completed"]

        batches = []
        while remaining:
            current_batch = []
            for cycle in remaining:
                # A cycle is ready if ALL its dependencies are in `completed_ids`
                # (which means they were completed before this run, OR they were processed in a previous batch)
                if all(dep in completed_ids for dep in cycle.depends_on):
                    current_batch.append(cycle)

            if not current_batch:
                # If we have remaining items but can't schedule anything, there's a circular dependency
                # or a missing dependency in the manifests list.
                logger.error(f"Cannot resolve dependencies for remaining cycles: {[c.id for c in remaining]}")
                # We add them all as a fallback batch so they at least get attempted
                batches.append(remaining)
                break

            batches.append(current_batch)

            # Update completed_ids for the next iteration
            completed_ids.update(c.id for c in current_batch)

            # Remove scheduled cycles from remaining list
            remaining = [c for c in remaining if c.id not in (x.id for x in current_batch)]

        return batches

    async def run_with_semaphore(self, coro: Coroutine[Any, Any, T]) -> T:
        """Executes a coroutine wrapped with a semaphore to limit concurrency."""
        async with self.semaphore:
            return await coro
