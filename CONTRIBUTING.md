# Contributing

Hi, and thanks for considering contributing to `poke-env`! This projects tries to bring two awesome things together: Pokemon and AI, and we would love to welcome new contributors.

Before contributing, please start by opening an issue to discuss the changes you wish to make before starting working on them: we'd be sad to refuse PRs because of a misunderstanding. Once we are convinced that your ideas would fit into the project, we'd love to help you build it. If you need a hand, have a question or wish to discuss your changes, feel free to reach out! A good method to do so would be to tag contributors, either in a draft PR or in the issue you opened.

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
- Be reviews and approved.
