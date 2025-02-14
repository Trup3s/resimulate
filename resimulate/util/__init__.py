import re
from importlib.metadata import PackageNotFoundError, version

from smartcard.System import readers


def get_version() -> str | None:
    try:
        return version("resimulate")
    except PackageNotFoundError:
        pass

    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        return str(match.group(1)) if match else None
    except FileNotFoundError:
        return None


def get_pcsc_devices() -> list[str]:
    devices = []
    for i, reader in enumerate(readers()):
        name = reader.name
        match = re.search(r"\[(.*?)\]", name)

        if match:
            name = match.group(1)

        devices.append(f"{i}: {name}")

    return devices
