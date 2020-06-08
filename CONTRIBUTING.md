# Contributing

Hi, and thanks for considering contributing to `poke-env`! This projects tries to bring two awesome things together: Pokemon and AI, and we would love to welcome new contributors.

Before contributing, please start by opening an issue to discuss the changes you wish to make before starting working on them: we'd be sad to refuse PRs because of a misunderstanding. Once we are convinced that your ideas would fit into the project, we'd love to help you build it. If you need a hand, have a question or wish to discuss your ideas in detail, feel free to reach out! A good method to do so would be to tag contributors, either in a draft PR or in the issue you opened.

Also, please note that we have a code of conduct. Follow it in all your interactions with the project. You can read it at [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Pull Request Process

To be accepted, your PR must:

- Implement changes that were discussed.
- Pass tests. We use the following tests:
    - Your code must be linted using `black`
    - Type hints must be consistent, as judged py `pyre`
    - Unit tests, found in `/unit_tests`
    - Integration tests, found in `/integration_tests`
- Be documented. If you introduce new functionalities, your code must be documented, and preferably include examples in the documentation. If applicable, update other files, such as the README.
- Be tested. Unit tests are a must, integration tests recommended if applicable.
- Be reviewed and approved.

## Setting up a local environment

These steps are not required, but are useful if you are unsure where to start.

First, you should use a python virtual environment. Which flavor of virtual environment you want to use depends on a couple things, including personal habits and your OS of choice. On Windows, [we recommend using `anaconda`](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html). On Mac OS and Linux, [`pyenv` works very well](https://github.com/pyenv/pyenv).

This project supports multiple versions of python 3, starting from version 3.6. You can use any supported version for development, but bear in mind that your work will be tested on all supported versions.

Once you have created your virtual environment, install dependencies with `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`. You can now setup pre-commits by running `pre-commit install` - the pre-commit configuration on the repo supposes Python 3.6.10, but you can modify it locally to your liking.

## Locally testing your commits

First, make sure your code is black-formatted by running `black .`.

To run tests locally, you can run:

- `PYTHONPATH=src/ pytest unit_tests/`
- `PYTHONPATH=src/ pytest integration_tests/`
- `pyre check`

If you do not have `pre-commit`s installed, be sure to also run `flake8`.

If all tests pass, you are ready to commit your changes!
