# Contributing to goth

## Getting started
Here are some ideas for issues to start with:
- pick something from [good first issues](https://github.com/golemfactory/goth/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- resolve some [`mypy`](https://github.com/python/mypy) warnings in the project
- propose a change to the readme/docstrings based on your experience when using the project

## Developer guidelines
1. Use [`black`](https://github.com/psf/black/) and [`flake8`](https://flake8.pycqa.org/en/latest/) for code formatting
    - if you used `poetry`, both these packages should already be installed in your virtual env as part of dev-dependencies
    - both checkers are run as part of the codestyle workflow in the project's GitHub Actions
2. Once you're done with your changes, mention them in the project's `CHANGELOG.md` file under the `Unreleased` section
