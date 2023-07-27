import asyncio
import atexit
import sys
from logging import CRITICAL, disable
from threading import Thread
from typing import Any


def __run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def __stop_loop(loop: asyncio.AbstractEventLoop, thread: Thread):
    disable(CRITICAL)
    tasks: list[asyncio.Task[Any]] = []
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


POKE_LOOP = asyncio.new_event_loop()
py_ver = sys.version_info
_t = Thread(target=__run_loop, args=(POKE_LOOP,), daemon=True)
_t.start()
atexit.register(__clear_loop)
