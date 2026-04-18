import asyncio

import httpx
import pytest

from src.domain_models.config import DispatcherConfig
from src.domain_models.manifest import CycleManifest
from src.services.async_dispatcher import AsyncDispatcher, retry_on_429


def test_resolve_dag_independent() -> None:
    dispatcher = AsyncDispatcher()
    manifests = [
        CycleManifest(id="01"),
        CycleManifest(id="02"),
        CycleManifest(id="03"),
    ]
    batches = dispatcher.resolve_dag(manifests, parallel=True)

    assert len(batches) == 1
    assert len(batches[0]) == 3


def test_resolve_dag_with_dependencies() -> None:
    dispatcher = AsyncDispatcher()
    manifests = [
        CycleManifest(id="01"),
        CycleManifest(id="02", depends_on=["01"]),
        CycleManifest(id="03", depends_on=["01"]),
        CycleManifest(id="04", depends_on=["02", "03"]),
    ]
    batches = dispatcher.resolve_dag(manifests, parallel=True)

    assert len(batches) == 3
    # First batch: 01
    assert len(batches[0]) == 1
    assert batches[0][0].id == "01"
    # Second batch: 02, 03
    assert len(batches[1]) == 2
    ids = [m.id for m in batches[1]]
    assert "02" in ids
    assert "03" in ids
    # Third batch: 04
    assert len(batches[2]) == 1
    assert batches[2][0].id == "04"


def test_resolve_dag_with_completed_cycle() -> None:
    dispatcher = AsyncDispatcher()
    manifests = [
        CycleManifest(id="01", status="completed"),
        CycleManifest(id="02", depends_on=["01"]),
        CycleManifest(id="03", depends_on=["01"]),
    ]
    batches = dispatcher.resolve_dag(manifests, parallel=True)

    assert len(batches) == 1
    # 01 is completed, so 02 and 03 are ready immediately
    assert len(batches[0]) == 2
    ids = [m.id for m in batches[0]]
    assert "02" in ids
    assert "03" in ids


@pytest.mark.asyncio
async def test_retry_on_429_success_after_retry() -> None:
    config = DispatcherConfig(max_retries=3, retry_backoff_factor=0.01)

    calls = 0

    @retry_on_429(config)
    async def mock_api_call() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            # Simulate 429 error
            request = httpx.Request("GET", "https://example.com")
            response = httpx.Response(429, request=request)
            msg = "Too Many Requests"
            raise httpx.HTTPStatusError(msg, request=request, response=response)
        return "success"

    result = await mock_api_call()

    assert result == "success"
    assert calls == 3


@pytest.mark.asyncio
async def test_retry_on_429_max_retries_exceeded() -> None:
    config = DispatcherConfig(max_retries=2, retry_backoff_factor=0.01)

    calls = 0

    @retry_on_429(config)
    async def mock_api_call() -> str:
        nonlocal calls
        calls += 1
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(429, request=request)
        msg = "Too Many Requests"
        raise httpx.HTTPStatusError(msg, request=request, response=response)

    from src.services.async_dispatcher import MaxRetriesExceededError

    with pytest.raises(MaxRetriesExceededError):
        await mock_api_call()

    assert calls == 3  # Initial call + 2 retries


@pytest.mark.asyncio
async def test_run_with_semaphore() -> None:
    config = DispatcherConfig(max_concurrent_tasks=2)
    dispatcher = AsyncDispatcher(config)

    active_tasks = 0
    max_active_tasks = 0

    async def worker() -> int:
        nonlocal active_tasks, max_active_tasks
        active_tasks += 1
        max_active_tasks = max(max_active_tasks, active_tasks)
        await asyncio.sleep(0.01)
        active_tasks -= 1
        return 1

    tasks = [dispatcher.run_with_semaphore(worker()) for _ in range(5)]
    results = await asyncio.gather(*tasks)

    assert sum(results) == 5
    assert max_active_tasks <= 2
