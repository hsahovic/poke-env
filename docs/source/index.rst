.. _index

#############################################################################
Poke-env: A python interface for training Reinforcement Learning pokemon bots
#############################################################################

This project aims at providing a Python environment for interacting in `pokemon showdown <https://pokemonshowdown.com/>`__ battles, with reinforcement learning in mind. Welcome to its documentation!

Poke-env offers a simple and clear API to manipulate Pokemons, Battles, Moves and many other pokemon showdown battle-related objects in Python. It also exposes an `open ai gym <https://gym.openai.com/>`__ interface to train reinforcement learning agents.

.. warning:: This module currently supports most gen 8 and 7 single battle formats. Support for doubles formats and gen 4-5-6 formats is preliminary. If you want a specific format to be supported, please `open an issue <https://github.com/hsahovic/poke-env/issues>`__.

Table of contents
*****************

.. toctree::
   :maxdepth: 2

   getting_started
   examples
   module_documentation

Other
*****

Acknowledgements
================

This project is a follow-up of a group project from an artifical intelligence class at `Ecole Polytechnique <https://www.polytechnique.edu/>`__.

You can find the original repository `here <https://github.com/hsahovic/inf581-project>`__. It is partially inspired by the `showdown-battle-bot project <https://github.com/Synedh/showdown-battle-bot>`__. Of course, none of these would have been possible without `Pokemon Showdown <https://github.com/Zarel/Pokemon-Showdown>`__.

Data
====

Data files are adapted version of the :samp:`js` data files of `Pokemon Showdown <https://github.com/Zarel/Pokemon-Showdown>`__.

Team data comes from `Smogon forums' RMT section <https://www.smogon.com/>`__.

License
=======

This project and its documentation are released under the `MIT License <https://opensource.org/licenses/MIT>`__.
