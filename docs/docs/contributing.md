---
slug: /contributing
sidebar_position: 9
---

# Contributing

OpenRPC is open source and open to feedback and contributions from the
community!

## Requirements

- [Poetry](https://python-poetry.org/docs/)
- [Black](https://github.com/psf/black/)
- [pre-commit](https://pre-commit.com/)

## Getting Started

Fork or clone this repository, then run the following.

```shell
cd openrpc
poetry shell
poetry install
pre-commit install
pre-commit run
```

Start hacking!

## Pull Requests

- Pull requests should target the `develop` branch.
- An [issue](https://gitlab.com/mburkard/openrpc/-/issues) should be
  made for any substantial changes.
- Commit messages should follow the
  [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  specification.
- Use type annotations.
- Code style [Black](https://github.com/psf/black/).
