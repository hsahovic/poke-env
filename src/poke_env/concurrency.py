import asyncio
import atexit
import sys
from logging import CRITICAL, disable
from threading import Thread
from typing import Any, List


def __run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def __stop_loop(loop: asyncio.AbstractEventLoop, thread: Thread):
    disable(CRITICAL)
    tasks: List[asyncio.Task[Any]] = []
    for task in asyncio.all_tasks(loop):
        task.cancel()
        tasks.append(task)

    cancelled = False
    shutdown = asyncio.run_coroutine_threadsafe(loop.shutdown_asyncgens(), loop)
    shutdown.result()

    while not cancelled:
        cancelled = True
        for task in tasks:
            if not task.done():
                cancelled = False

    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.call_soon_threadsafe(loop.close)


def __clear_loop():
    __stop_loop(POKE_LOOP, _t)


async def _create_in_poke_loop_async(cls_: Any, *args: Any, **kwargs: Any) -> Any:
    return cls_(*args, **kwargs)


def create_in_poke_loop(
    cls_: Any, loop: asyncio.AbstractEventLoop, *args: Any, **kwargs: Any
) -> Any:
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None
    if current_loop == loop:
        return cls_(*args, **kwargs)
    else:
        return asyncio.run_coroutine_threadsafe(
            _create_in_poke_loop_async(cls_, *args, **kwargs), loop
        ).result()


async def handle_threaded_coroutines(coro: Any, loop: asyncio.AbstractEventLoop):
    if asyncio.get_running_loop() is loop:
        return await coro
    completed = asyncio.get_running_loop().create_future()
    caller_loop = asyncio.get_running_loop()
    remote_task = None
    cancel_requested = False

    def finish(task):
        if task.cancelled():
            completed.cancel()
        elif task.exception() is not None:
            completed.set_exception(task.exception())
        else:
            completed.set_result(task.result())

    def start():
        nonlocal remote_task
        remote_task = loop.create_task(coro)
        remote_task.add_done_callback(
            lambda task: caller_loop.call_soon_threadsafe(finish, task)
        )
        if cancel_requested:
            remote_task.cancel()

    def cancel():
        if remote_task is not None:
            remote_task.cancel()

    loop.call_soon_threadsafe(start)
    try:
        return await asyncio.shield(completed)
    except asyncio.CancelledError:
        cancel_requested = True
        loop.call_soon_threadsafe(cancel)
        while not completed.done():
            try:
                await asyncio.shield(completed)
            except (asyncio.CancelledError, Exception):
                pass
        if not completed.cancelled():
            completed.exception()
        raise


POKE_LOOP = asyncio.new_event_loop()
py_ver = sys.version_info
_t = Thread(target=__run_loop, args=(POKE_LOOP,), daemon=True)
_t.start()
atexit.register(__clear_loop)
