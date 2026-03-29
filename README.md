# Poke-env: Python Interface for Pokemon Showdown Bots

[![PyPI version fury.io](https://badge.fury.io/py/poke-env.svg)](https://pypi.python.org/pypi/poke-env/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/poke-env.svg)](https://pypi.python.org/pypi/poke-env/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/poke-env/badge/?version=stable)](https://poke-env.readthedocs.io/en/stable/?badge=stable)
[![codecov](https://codecov.io/gh/hsahovic/poke-env/branch/master/graph/badge.svg)](https://codecov.io/gh/hsahovic/poke-env)

`poke-env` is a Python library for building scripted agents, self-play
experiments, and reinforcement learning workflows on
[Pokemon Showdown](https://pokemonshowdown.com/).

![A simple agent in action](rl-gif.gif)

## Installation

This project requires Python >= 3.10 and access to a
[Pokemon Showdown](https://github.com/smogon/pokemon-showdown) server. For
training and local development, running your own server is strongly
recommended.

```
pip install poke-env
```

You can use [smogon's server](https://play.pokemonshowdown.com/) to try out your agents against humans, but having a development server is strongly recommended. In particular, it is recommended to use the `--no-security` flag to run a local server with most rate limiting and throttling turned off. Please refer to [the docs](https://poke-env.readthedocs.io/en/stable/getting_started.html#configuring-a-showdown-server) for detailed setup instructions.


```
git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown
npm install
cp config/config-example.js config/config.js
node pokemon-showdown start --no-security
```

## First local battle

Once your local server is running, the quickest way to verify your setup is to
run two built-in players against each other. `RandomPlayer` uses the default
localhost server configuration, so this script should work as-is:

```python
import asyncio

from poke_env.player import RandomPlayer


async def main():
    player_1 = RandomPlayer(max_concurrent_battles=1)
    player_2 = RandomPlayer(max_concurrent_battles=1)

    await player_1.battle_against(player_2, n_battles=1)

    print(f"Finished battles: {player_1.n_finished_battles}")
    print(f"Player 1 wins: {player_1.n_won_battles}")


if __name__ == "__main__":
    asyncio.run(main())
```

To build your own bot, subclass `Player` and override `choose_move`. The
quickstart guide walks through that step by step.

## Documentation and examples

Documentation, detailed examples, and starting code are available
[on Read the Docs](https://poke-env.readthedocs.io/en/stable/).

Useful entry points:

- [Getting started](https://poke-env.readthedocs.io/en/stable/getting_started.html)
- [Example guides](https://poke-env.readthedocs.io/en/stable/examples/index.html)

## Development version

You can also clone the latest master version with:

```
git clone https://github.com/hsahovic/poke-env.git
```

Dependencies and development dependencies can then be installed with:

```
pip install .[dev]
```

## Acknowledgements

This project is a follow-up of a group project from an artificial intelligence class at [Ecole Polytechnique](https://www.polytechnique.edu/).

You can find the original repository [here](https://github.com/hsahovic/inf581-project). It is partially inspired by the [showdown-battle-bot project](https://github.com/Synedh/showdown-battle-bot). Of course, none of these would have been possible without [Pokemon Showdown](https://github.com/smogon/pokemon-showdown).

Team data comes from [Smogon forums' RMT section](https://www.smogon.com/).

## Data

Data files are adapted versions of the `js` data files from
[Pokemon Showdown](https://github.com/smogon/pokemon-showdown).

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Citing `poke-env`

```bibtex
@misc{poke_env,
    author       = {Haris Sahovic},
    title        = {Poke-env: pokemon AI in python},
    url          = {https://github.com/hsahovic/poke-env}
}
```
