# ReSIMulate

**ReSIMulate** is a terminal application and library built for eSIM analysis.

## Features

- Full LPA client implementation for eSIM cards.
- Trace APDU commands between eSIM and Smartphone via the simtrace2 sniffer
- Replay traced APDU commands to the eSIM card.
- Fuzzer for eSIM cards.

## Usage

### CLI

```bash
$ resimulate --help

Usage: resimulate [-h] [--version] [-v] [-p {0}] {lpa,trace,fuzzer} ...

ReSIMulate is a terminal application and library built for eSIM and SIM-specific APDU analysis.

Options:
  -h, --help            show this help message and exit
  --version             show programs version number and exit
  -v, --verbose         Enable verbose output during replay.
  -p, --pcsc-device {0}
                        PC/SC device index (default: 0). 0: OMNIKEY 3x21 Smart Card Reader

Commands:
  {lpa,trace,fuzzer}    Available commands
    lpa                 Local Profile Assistant operations
    trace               Trace-level operations (record, replay)
    fuzzer              Fuzzer operations
```

### Library

```python
from resimulate.euicc.card import Card
from resimulate.euicc.exceptions import IccidAlreadyExists, EuiccException
from resimulate.euicc.models.activation_profile import ActivationProfile
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.euicc.mutation.deterministic_engine import DeterministicMutationEngine
from resimulate.euicc.recorder.recorder import OperationRecorder
from resimulate.euicc.transport.pcsc_link import PcscLink

mutation_engine = DeterministicMutationEngine()
recorder = OperationRecorder()

profile = ActivationProfile.from_activation_code(
    "LPA:1$rsp.truphone.com$QR-G-5C-1LS-1W1Z9P7"
)

with PcscLink(recorder=recorder, apdu_data_size=255) as link:
    card = Card(link)
    try:
        card.isd_r.get_euicc_challenge()
    except EuiccException:
        pass

    card.isd_r.get_euicc_info_2()
    card.isd_r.get_euicc_info_1()
    card.isd_r.get_eid()
    try:
        notification = card.isd_r.download_profile(profile)
        iccid = notification.data.notification.iccid
        card.isd_r.process_notifications([notification])
        card.isd_r.set_nickname(iccid, "Some Nickname")
        card.isd_r.enable_profile(iccid)
        card.isd_r.disable_profile(iccid)
    except IccidAlreadyExists:
        pass

    profiles = card.isd_r.get_profiles()
    for profile in profiles:
        card.isd_r.delete_profile(isdp_aid=profile.isdp_aid)
        notifications = card.isd_r.retrieve_notification_list()
        card.isd_r.process_notifications(notifications)

    card.isd_r.set_default_dp_address("some random address")
    card.isd_r.reset_euicc_memory(ResetOption.RESET_DEFAULT_SMDP_ADDRESS)
```

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

This is useful for extending the library or just debugging interactions between the smartcard reader and the program using it.

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
