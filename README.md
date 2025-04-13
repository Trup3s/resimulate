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

## Misc

### Sniff APDUs between smartcard reader and program

Source: [blog.apdu.fr](https://blog.apdu.fr/posts/2022/06/pcsc-api-spy-update/)

1. Find libpcsclite library that is linked:

```bash
$ ldd /usr/bin/pcsc_scan
    linux-vdso.so.1 (0x000076ae78b9b000)
	libpcsclite.so.1 => /usr/lib/libpcsclite.so.1 (0x000076ae78b44000)
	libc.so.6 => /usr/lib/libc.so.6 (0x000076ae78952000)
	/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x000076ae78b9d000)
```

2. Run pcsc-spy in another terminal:

```bash
$ pcsc-spy -o /tmp/pcsc-spy.log
```

3. Run the program that uses libpcsclite:

```bash
LD_PRELOAD=/usr/lib/libpcscspy.so.0 program.sh
```
