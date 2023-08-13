# self-play training is a planned feature for poke-env
# This script illustrates a very rough approach that can currently be used to train using self-play
# Don't hesitate to open an issue if things seem not to be working

import asyncio
from threading import Thread

import numpy as np

from poke_env import to_id_str
from poke_env.player import Gen8EnvSinglePlayer


class RandomGen8EnvPlayer(Gen8EnvSinglePlayer):
    def embed_battle(self, battle):
        return np.array([0])


def env_algorithm(player, n_battles):
    for _ in range(n_battles):
        done = False
        player.reset()
        while not done:
            _, _, done, _ = player.step(np.random.choice(player.action_space))


async def launch_battles(player, opponent):
    battles_coroutine = asyncio.gather(
        player.send_challenges(
            opponent=to_id_str(opponent.username),
            n_challenges=1,
            to_wait=opponent.logged_in,
        ),
        opponent.accept_challenges(opponent=to_id_str(player.username), n_challenges=1),
    )
    await battles_coroutine


def env_algorithm_wrapper(player, kwargs):
    env_algorithm(player, **kwargs)

    player._start_new_battle = False
    while True:
        try:
            player.complete_current_battle()
            player.reset()
        except OSError:
            break


p1 = RandomGen8EnvPlayer(log_level=25)
p2 = RandomGen8EnvPlayer(log_level=25)

p1._start_new_battle = True
p2._start_new_battle = True

loop = asyncio.get_event_loop()

env_algorithm_kwargs = {"n_battles": 5}

t1 = Thread(target=lambda: env_algorithm_wrapper(p1, env_algorithm_kwargs))
t1.start()

t2 = Thread(target=lambda: env_algorithm_wrapper(p2, env_algorithm_kwargs))
t2.start()

while p1._start_new_battle:
    loop.run_until_complete(launch_battles(p1, p2))
t1.join()
t2.join()
