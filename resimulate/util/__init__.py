import re
from importlib.metadata import PackageNotFoundError, version


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
