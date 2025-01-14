# My build123d models

A monorepository for my [build123d][build123d] models.

[![PyPI](https://img.shields.io/pypi/v/monobd)][pypi]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/monobd)][pypi]
[![Build](https://img.shields.io/github/checks-status/smkent/monobd/main?label=build)][gh-actions]
[![codecov](https://codecov.io/gh/smkent/monobd/branch/main/graph/badge.svg)][codecov]
[![GitHub stars](https://img.shields.io/github/stars/smkent/monobd?style=social)][repo]

## Installation from PyPI

[monobd is available on PyPI][pypi]:

```console
pip install monobd
```

## Development

### [Poetry][poetry] installation

Via [`pipx`][pipx]:

```console
pip install pipx
pipx install poetry
pipx inject poetry poetry-pre-commit-plugin
```

Via `pip`:

```console
pip install poetry
poetry self add poetry-pre-commit-plugin
```

### Development tasks

* Setup: `poetry install`
* Run static checks: `poetry run poe lint` or
  `poetry run pre-commit run --all-files`
* Run static checks and tests: `poetry run poe test`

---

Created from [smkent/cookie-python][cookie-python] using
[cookiecutter][cookiecutter]

[build123d]: https://github.com/gumyr/build123d
[codecov]: https://codecov.io/gh/smkent/monobd
[cookie-python]: https://github.com/smkent/cookie-python
[cookiecutter]: https://github.com/cookiecutter/cookiecutter
[gh-actions]: https://github.com/smkent/monobd/actions?query=branch%3Amain
[pipx]: https://pypa.github.io/pipx/
[poetry]: https://python-poetry.org/docs/#installation
[pypi]: https://pypi.org/project/monobd/
[repo]: https://github.com/smkent/monobd
