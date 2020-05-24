# The pokemon showdown Python environment

[![PyPI version fury.io](https://badge.fury.io/py/poke-env.svg)](https://pypi.python.org/pypi/poke-env/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/poke-env.svg)](https://pypi.python.org/pypi/poke-env/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/poke-env/badge/?version=stable)](https://poke-env.readthedocs.io/en/stable/?badge=stable)

A Python interface to create battling pokemon agents. `poke-env` offers an easy-to-use interface for creating rule-based or training Reinforcement Learning bots to battle on [pokemon showdown](https://pokemonshowdown.com/).

![A simple agent in action](rl-gif.gif)

# Getting started

Agents are instance of python classes inheriting from `Player`. Here is what your first agent could look like:

```python
class YourFirstAgent(Player):
    def choose_move(self, battle):
        for move in battle.available_moves:
            if move.base_power > 90:
                # A powerful move! Let's use it
                return self.create_order(move)

        # No available move? Let's switch then!
        for switch in battle.available_switches:
            if switch.current_hp_fraction > battle.active_pokemon.current_hp_fraction:
                # This other pokemon has more HP left... Let's switch it in?
                return self.create_order(switch)

        # Not sure what to do?
        return self.choose_random_move(battle)
```

To get started, take a look at [our documentation](https://poke-env.readthedocs.io/en/stable/)!


## Documentation and examples

Documentation, detailed examples and starting code can be found [on readthedocs](https://poke-env.readthedocs.io/en/stable/).


## Installation

This project requires python >= 3.6 and a [Pokemon Showdown](https://github.com/Zarel/Pokemon-Showdown) server.

```
pip install poke-env
```

You can use [smogon's server](https://play.pokemonshowdown.com/) to try out your agents against humans, but having a development server is strongly recommended. In particular, [this showdown fork](https://github.com/hsahovic/Pokemon-Showdown) is optimized for performance and can be used locally **without authentication**:

```
git clone https://github.com/hsahovic/Pokemon-Showdown.git
```

### Development version

You can also install the latest master version with:

```
git clone https://github.com/hsahovic/poke-env.git
```

Dependencies and development dependencies can then be installed with:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Acknowledgements

This project is a follow-up of a group project from an artifical intelligence class at [Ecole Polytechnique](https://www.polytechnique.edu/).

You can find the original repository [here](https://github.com/hsahovic/inf581-project). It is partially inspired by the [showdown-battle-bot project](https://github.com/Synedh/showdown-battle-bot). Of course, none of these would have been possible without [Pokemon Showdown](https://github.com/Zarel/Pokemon-Showdown).

Team data comes from [Smogon forums' RMT section](https://www.smogon.com/).

## Data

Data files are adapted version of the `js` data files of [Pokemon Showdown](https://github.com/Zarel/Pokemon-Showdown).

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Other

[![CircleCI](https://circleci.com/gh/hsahovic/poke-env.svg?style=svg)](https://circleci.com/gh/hsahovic/poke-env)
[![codecov](https://codecov.io/gh/hsahovic/poke-env/branch/master/graph/badge.svg)](https://codecov.io/gh/hsahovic/poke-env)
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
