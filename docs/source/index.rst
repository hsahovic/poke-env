.. _index:

#############################################################################
Poke-env: A Python Interface for Training Reinforcement Learning Pokémon Bots
#############################################################################

Poke-env provides an environment for engaging in `Pokémon Showdown <https://pokemonshowdown.com/>`__ battles with a focus on reinforcement learning. 

It boasts a straightforward API for handling Pokémon, Battles, Moves, and other battle-centric objects, alongside a `Farama Gymnasium <https://gymnasium.farama.org/>`__ interface for training agents.

.. attention:: While poke-env aims to support all Pokémon generations, it was primarily developed with the latest generations in mind. If you discover any missing or incorrect functionalities for earlier generations, please `open an issue <https://github.com/hsahovic/poke-env/issues>`__ to help improve the library.

.. toctree::
   :maxdepth: 2
   :caption: User guide

   getting_started.rst
   examples/index.rst

.. toctree::
   :maxdepth: 2
   :caption: Main modules documentation

   modules/battle.rst
   modules/player.rst
   modules/pokemon.rst
   modules/move.rst
   modules/env.rst
   modules/other_environment.rst

On top of the main modules dedicated to building Pokémon Showdown bots, Poke-env encompasses standalone submodules to cater to various facets of Pokémon Showdown interactions:

.. toctree::
   :maxdepth: 1
   :caption: Standalone submodules documentation

   Data - Access and manipulate pokémon data <modules/data.rst>
   PS Client - Interact with Pokémon Showdown servers <modules/ps_client.rst>
   Teambuilder - Parse and generate showdown teams <modules/teambuilder.rst>
   Concurrency utilities <modules/concurrency.rst>
   Damage calculator <modules/calc.rst>
   Stats utilities <modules/stats.rst>
   Exceptions <modules/exceptions.rst>

Acknowledgements
================

Originated from a group project at `École Polytechnique <https://www.polytechnique.edu/>`_. Inspired partially by `showdown-battle-bot <https://github.com/Synedh/showdown-battle-bot>`__ and built upon `Pokemon Showdown <https://github.com/Zarel/Pokemon-Showdown>`__.

Data
====

Data adapted from `Pokemon Showdown <https://github.com/Zarel/Pokemon-Showdown>`__ and team data sourced from `Smogon forums' RMT section <https://www.smogon.com/>`__.

License
=======

Released under the `MIT License <https://opensource.org/licenses/MIT>`__.
