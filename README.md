# ReSIMulate

**ReSIMulate** is a terminal application for analyzing eSIM and SIM card interactions. It allows you to record APDU commands, save them, and replay them for differential testing and debugging.

## Features

- Record APDU commands from a device or interface.
- Replay saved APDU commands to a target device.
- Supports configurable timeouts, devices, and verbose output.
- Enables differential testing for SIM interactions.

## Development setup

### Poetry

This project uses [Poetry](https://python-poetry.org/) for dependency management. To install Poetry, run the following command:

```bash
pipx install poetry
pipx inject poetry poetry-plugin-shell
```

Activate the Poetry shell:

```bash
poetry shell
```

### Pre-commit hooks

This project uses [pre-commit](https://pre-commit.com/) for code formatting and linting. To install pre-commit, run the following command:

```bash
pre-commit install
```
