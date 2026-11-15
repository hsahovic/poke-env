import asyncio
from unittest.mock import Mock, patch

import pytest

from poke_env import AccountConfiguration, ServerConfiguration
from poke_env.concurrency import handle_threaded_coroutines
from poke_env.environment import SinglesEnv
from poke_env.environment.env import _AsyncQueue
from poke_env.player import RandomPlayer
from poke_env.ps_client import PSClient


class Socket:
    def __init__(self):
        self.messages = asyncio.Queue()
        self.entered = asyncio.Event()
        self.closed = False

    async def __aenter__(self):
        self.entered.set()
        return self

    async def __aexit__(self, *args):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        message = await self.messages.get()
        if message is None:
            raise StopAsyncIteration
        if isinstance(message, Exception):
            raise message
        return message


def client():
    return PSClient(
        AccountConfiguration("lifecycle", None),
        server_configuration=ServerConfiguration("ws://unused", ""),
        start_listening=False,
        loop=asyncio.get_running_loop(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation", ["send_challenges", "accept_challenges", "ladder", "battle_against"]
)
async def test_public_operations_receive_original_error(operation):
    player = RandomPlayer(start_listening=False)
    opponent = RandomPlayer(start_listening=False)
    started = asyncio.Event()
    cleaned = asyncio.Event()
    error = ValueError("broken battle initialization")

    async def fail():
        await asyncio.sleep(0.02)
        raise error

    async def exercise():
        socket = Socket()

        async def handle(_message):
            await fail()

        player.ps_client._on_battle_message = handle
        with patch("poke_env.ps_client.ps_client.ws.connect", return_value=socket):
            listener = asyncio.create_task(player.ps_client.listen())
            await socket.entered.wait()
            started.set()
            await socket.messages.put(">battle-gen9randombattle-1\n|init|battle")
            try:
                await listener
            except asyncio.CancelledError:
                pass
            cleaned.set()

    args = (1,) if operation == "ladder" else (opponent,)
    if operation in ("send_challenges", "accept_challenges"):
        args = ("opponent", 1)
    listener = asyncio.create_task(
        handle_threaded_coroutines(exercise(), player.ps_client.loop)
    )
    try:
        with pytest.raises(ValueError) as caught:
            await asyncio.wait_for(getattr(player, operation)(*args), 2)
        assert caught.value is error
        await listener
        assert started.is_set() and cleaned.is_set()
        with pytest.raises(ConnectionError, match="closed"):
            await player.ladder(1)
        assert not player.ps_client._operation_errors
        assert not opponent.ps_client._operation_errors
    finally:
        await player.ps_client.stop_listening()
        await opponent.ps_client.stop_listening()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "ending", [None, RuntimeError("receive failed"), OSError("socket failed")]
)
async def test_disconnect_releases_concurrent_waiters(ending):
    ps_client = client()
    socket = Socket()
    with patch("poke_env.ps_client.ps_client.ws.connect", return_value=socket):
        listener = asyncio.create_task(ps_client.listen())
        waiters = [
            asyncio.create_task(ps_client._wait_for_operation(asyncio.Event().wait()))
            for _ in range(3)
        ]
        await socket.entered.wait()
        await socket.messages.put(ending)
        results = await asyncio.wait_for(
            asyncio.gather(*waiters, return_exceptions=True), 1
        )
        await listener
    assert all(
        isinstance(result, ConnectionError if ending is None else type(ending))
        for result in results
    )
    assert not ps_client._operation_errors
    assert socket.closed


@pytest.mark.asyncio
async def test_stop_during_connect_waits_for_cleanup():
    ps_client = client()
    entered = asyncio.Event()
    cleaned = asyncio.Event()

    class Connecting(Socket):
        async def __aenter__(self):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0.01)
                cleaned.set()

    with patch("poke_env.ps_client.ps_client.ws.connect", return_value=Connecting()):
        listener = asyncio.create_task(ps_client.listen())
        await entered.wait()
        await asyncio.wait_for(ps_client.stop_listening(), 1)
    assert cleaned.is_set()
    assert listener.done()
    await ps_client.stop_listening()


@pytest.mark.asyncio
async def test_cross_loop_cancellation_waits_for_cleanup():
    player = RandomPlayer(start_listening=False)
    cleaned = []

    async def operation(*args):
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0.03)
            cleaned.append(True)

    player._ladder = operation
    task = asyncio.create_task(player.ladder(1))
    await asyncio.sleep(0.03)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 1)
    assert cleaned == [True]
    assert not player.ps_client._operation_errors


@pytest.mark.asyncio
@pytest.mark.parametrize("race", [False, True])
async def test_environment_queue_wait_observes_client_failure(race):
    ps_client = client()
    queue = _AsyncQueue(ps_client.loop, client=ps_client)
    error = ValueError("environment handler failed")
    wait = asyncio.create_task(asyncio.to_thread(queue.race_get if race else queue.get))
    await asyncio.sleep(0.03)
    ps_client._close_operations(error)
    with pytest.raises(ValueError) as caught:
        await asyncio.wait_for(wait, 1)
    assert caught.value is error
    assert not ps_client._operation_errors


@pytest.mark.asyncio
async def test_cancelled_operation_does_not_close_healthy_client():
    ps_client = client()
    task = asyncio.create_task(ps_client._wait_for_operation(asyncio.Event().wait()))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert await ps_client._wait_for_operation(asyncio.sleep(0, result=7)) == 7
    assert not ps_client._operation_errors


@pytest.mark.asyncio
async def test_connection_setup_failure_and_automatic_listener_cleanup():
    error = OSError("connection refused")
    player = RandomPlayer(start_listening=False)
    with patch("poke_env.ps_client.ps_client.ws.connect", side_effect=error):
        listener = asyncio.create_task(
            handle_threaded_coroutines(player.ps_client.listen(), player.ps_client.loop)
        )
        await listener
    await player.ps_client.stop_listening()
    with pytest.raises(ConnectionError):
        await player.ladder(1)


class Environment(SinglesEnv):
    def embed_battle(self, battle):
        return [0]

    def calc_reward(self, battle):
        return 0


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["reset", "step"])
@pytest.mark.parametrize("failing_agent", ["agent1", "agent2"])
async def test_public_environment_waits_receive_failure(operation, failing_agent):
    env = Environment(start_listening=False)
    error = ValueError("battle parser failed")
    if operation == "step":
        env.battle1 = Mock(finished=False)
        env.battle2 = Mock(finished=False)
    call = env.reset if operation == "reset" else lambda: env.step({})
    waiting = asyncio.create_task(asyncio.to_thread(call))

    async def fail_when_waiting():
        ps_client = getattr(env, failing_agent).ps_client
        while len(ps_client._operation_errors) < (2 if operation == "reset" else 1):
            await asyncio.sleep(0.001)
        ps_client._close_operations(error)

    try:
        await asyncio.wait_for(
            handle_threaded_coroutines(fail_when_waiting(), env._loop), 1
        )
        with pytest.raises(ValueError) as caught:
            await asyncio.wait_for(waiting, 1)
        assert caught.value is error
    finally:
        await env.agent1.ps_client.stop_listening()
        await env.agent2.ps_client.stop_listening()
        if env._challenge_task is not None:
            await asyncio.gather(
                asyncio.wrap_future(env._challenge_task), return_exceptions=True
            )
        env._loop.call_soon_threadsafe(env._loop.stop)


@pytest.mark.asyncio
async def test_connection_setup_failure_reaches_pending_public_call():
    player = RandomPlayer(start_listening=False)
    error = OSError("connection refused")
    pending = asyncio.create_task(player.ladder(1))

    async def connect():
        while not player.ps_client._operation_errors:
            await asyncio.sleep(0.001)
        with patch("poke_env.ps_client.ps_client.ws.connect", side_effect=error):
            await player.ps_client.listen()

    await asyncio.wait_for(
        handle_threaded_coroutines(connect(), player.ps_client.loop), 1
    )
    with pytest.raises(OSError) as caught:
        await asyncio.wait_for(pending, 1)
    assert caught.value is error
    await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_environment_queue_race_preserves_consumed_item():
    ps_client = client()
    queue = _AsyncQueue(ps_client.loop, client=ps_client)
    queue._clients = (ps_client, client())
    event = asyncio.Event()

    class Queue(asyncio.Queue):
        async def get(self):
            item = await super().get()
            event.set()
            return item

    queue.queue = Queue()
    waiting = asyncio.create_task(asyncio.to_thread(queue.race_get, event))
    await asyncio.sleep(0.03)
    queue.queue.put_nowait(7)
    result = await asyncio.wait_for(waiting, 1)
    assert result == 7
    assert not ps_client._operation_errors
