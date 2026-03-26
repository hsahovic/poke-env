import asyncio
import time

import pytest

from poke_env.concurrency import POKE_LOOP
from poke_env.environment.env import _AsyncQueue


def _bench_put_get(n: int) -> float:
    """Benchmark n iterations of put + get (the reset hot path)."""
    q: _AsyncQueue[int] = _AsyncQueue(POKE_LOOP, maxsize=1)
    start = time.perf_counter()
    for i in range(n):
        q.put(i)
        q.get()
    return time.perf_counter() - start


def _bench_put_race_get(n: int) -> float:
    """Benchmark n iterations of put + race_get (the step hot path)."""
    q: _AsyncQueue[int] = _AsyncQueue(POKE_LOOP, maxsize=1)
    event = asyncio.run_coroutine_threadsafe(
        _create_event(), POKE_LOOP
    ).result()
    start = time.perf_counter()
    for i in range(n):
        q.put(i)
        result = q.race_get(event)
        assert result == i
    return time.perf_counter() - start


async def _create_event() -> asyncio.Event:
    return asyncio.Event()


N = 5000
PUT_GET_MAX_SECONDS = 5.0
PUT_RACE_GET_MAX_SECONDS = 8.0


@pytest.mark.timeout(30)
def test_bench_put_get():
    elapsed = _bench_put_get(N)
    assert elapsed < PUT_GET_MAX_SECONDS, (
        f"put+get x{N} took {elapsed:.2f}s (limit {PUT_GET_MAX_SECONDS}s)"
    )


@pytest.mark.timeout(30)
def test_bench_put_race_get():
    elapsed = _bench_put_race_get(N)
    assert elapsed < PUT_RACE_GET_MAX_SECONDS, (
        f"put+race_get x{N} took {elapsed:.2f}s (limit {PUT_RACE_GET_MAX_SECONDS}s)"
    )
