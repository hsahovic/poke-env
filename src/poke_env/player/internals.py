import asyncio
import atexit
import sys

from logging import disable, CRITICAL
from threading import Thread


def __run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def __stop_loop(loop: asyncio.AbstractEventLoop, thread: Thread):  # pragma: no cover
    disable(CRITICAL)
    tasks = []
    if py_ver.major == 3 and py_ver.minor >= 7:
        caller = asyncio
    else:
        caller = asyncio.Task
    for task in caller.all_tasks(loop):
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


def __clear_loop():  # pragma: no cover
    __stop_loop(POKE_LOOP, _t)


POKE_LOOP = asyncio.new_event_loop()
py_ver = sys.version_info
_t = Thread(target=__run_loop, args=(POKE_LOOP,), daemon=True)
_t.start()
atexit.register(__clear_loop)
