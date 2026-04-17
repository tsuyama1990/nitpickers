import asyncio
import random
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar

import httpx

from src.config import settings
from src.domain_models.config import DispatcherConfig
from src.domain_models.manifest import CycleManifest
from src.utils import logger


class MaxRetriesExceededError(Exception):
    pass


T = TypeVar("T")


def retry_on_429(config: DispatcherConfig) -> Callable[..., Any]:
    """Decorator to retry API requests on HTTP 429 Too Many Requests errors."""

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
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
                        sleep_time = (
                            config.retry_backoff_factor**retries
                        ) + random.SystemRandom().uniform(1, 3)
                        logger.warning(
                            f"HTTP 429 encountered in {func.__name__}. Retrying in {sleep_time:.2f} seconds (Attempt {retries}/{config.max_retries})."
                        )
                        await asyncio.sleep(sleep_time)
                    elif (
                        getattr(e.response, "status_code", None) == 503
                        and retries < config.max_retries
                    ):
                        retries += 1
                        sleep_time = (
                            config.retry_backoff_factor**retries
                        ) + random.SystemRandom().uniform(1, 3)
                        logger.warning(
                            f"HTTP 503 encountered in {func.__name__}. Retrying in {sleep_time:.2f} seconds (Attempt {retries}/{config.max_retries})."
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        if retries >= config.max_retries:
                            msg = f"Max retries exceeded for {func.__name__}"
                            raise MaxRetriesExceededError(msg) from e
                        raise

        return wrapper

    return decorator


class AsyncDispatcher:
    def __init__(self, config: DispatcherConfig | None = None) -> None:
        self.config = config or settings.dispatcher
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

    def resolve_dag(
        self, manifests: list[CycleManifest], parallel: bool = False
    ) -> list[list[CycleManifest]]:
        """
        Groups cycles into independent batches based on dependencies.
        Returns a list of batches, where each batch can be executed concurrently.
        Optimized using Kahn's algorithm principles for DAG sorting.
        """
        if not parallel:
            return [[c] for c in manifests]

        # Start with any cycle that is already completed.
        completed_ids = {c.id for c in manifests if c.status == "completed"}

        # Track remaining cycles to schedule
        remaining = [c for c in manifests if c.status != "completed"]

        # Build adjacency graph and in-degree map
        # in_degree tracks how many unmet dependencies a cycle has
        in_degree: dict[str, int] = {c.id: 0 for c in remaining}

        for c in remaining:
            for dep in c.depends_on:
                if dep not in completed_ids:
                    in_degree[c.id] += 1

        batches = []
        while remaining:
            # Collect all items with 0 unmet dependencies in the current iteration
            current_batch = [c for c in remaining if in_degree[c.id] == 0]

            if not current_batch:
                # If we have remaining items but can't schedule anything, there is a cycle
                logger.error(
                    f"Circular dependency detected. Cannot resolve: {[c.id for c in remaining]}"
                )
                # Add them all as a fallback batch to ensure progress is attempted
                batches.append(remaining)
                break

            batches.append(current_batch)

            # Mark items in current_batch as resolved
            resolved_ids = {c.id for c in current_batch}

            # Remove them from the remaining list
            remaining = [c for c in remaining if c.id not in resolved_ids]

            # Reduce in-degree for downstream components
            # This makes the approach O(V + E) instead of iterating multiple times
            for c in remaining:
                # Calculate how many dependencies were just fulfilled in this batch
                met_dependencies = sum(1 for dep in c.depends_on if dep in resolved_ids)
                in_degree[c.id] -= met_dependencies

        return batches

    async def run_with_semaphore(self, coro: Coroutine[Any, Any, T]) -> T:
        """Executes a coroutine wrapped with a semaphore to limit concurrency."""
        async with self.semaphore:
            logger.info(f"DEBUG: run_with_semaphore awaiting {coro}")
            return await coro
