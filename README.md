# The Pokemon Showdown Python Environment

[![PyPI version fury.io](https://badge.fury.io/py/poke-env.svg)](https://pypi.python.org/pypi/poke-env/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/poke-env.svg)](https://pypi.python.org/pypi/poke-env/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/poke-env/badge/?version=stable)](https://poke-env.readthedocs.io/en/stable/?badge=stable)
[![codecov](https://codecov.io/gh/hsahovic/poke-env/branch/master/graph/badge.svg)](https://codecov.io/gh/hsahovic/poke-env)

A Python interface for creating battling Pokemon agents. `poke-env` offers an
easy-to-use interface for building rule-based bots or training reinforcement
learning agents to battle on [Pokemon Showdown](https://pokemonshowdown.com/).

![A simple agent in action](rl-gif.gif)

## Getting started

Agents are instances of Python classes inheriting from `Player`. Here is what
your first agent could look like:

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

This project requires Python >= 3.10 and a
[Pokemon Showdown](https://github.com/smogon/pokemon-showdown) server.

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
