# The pokemon showdown Python environment

[![CircleCI](https://circleci.com/gh/hsahovic/poke-env.svg?style=svg)](https://circleci.com/gh/hsahovic/poke-env)
[![codecov](https://codecov.io/gh/hsahovic/poke-env/branch/master/graph/badge.svg)](https://codecov.io/gh/hsahovic/poke-env)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
[![Documentation Status](https://readthedocs.org/projects/poke-env/badge/?version=latest)](https://poke-env.readthedocs.io/en/latest/?badge=latest)

A python interface for training Reinforcement Learning bots to battle on [pokemon showdown](https://pokemonshowdown.com/).

This project aims at providing a Python environment for interacting in [pokemon showdown](https://pokemonshowdown.com/) battles, with reinforcement learning in mind.

## Documentation and examples

Documentation and detailed examples can be found [here](https://poke-env.readthedocs.io/en/latest/).

Examples and starting code can be found [here](https://github.com/hsahovic/poke-env/tree/master/examples).

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

## Data

Data files are adapted version of the `js` data files of [Pokemon Showdown](https://github.com/Zarel/Pokemon-Showdown).

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
