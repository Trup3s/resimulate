import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

from resimulate.util.apdu_highlighter import ApduHighlighter


class RichLogger:
    _instance = None

    def __new__(cls, console: Console = None):
        if cls._instance is None:
            cls._instance = super(RichLogger, cls).__new__(cls)
            cls._instance._initialize(console)
        return cls._instance

    def _initialize(self, console: Console = None):
        logging.basicConfig(
            level="NOTSET",
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, console=console, markup=True)],
        )
        self.logger = logging.getLogger("rich")

    def get_logger(self, console: Console = None) -> logging.Logger:
        if not console:
            console = Console(highlighter=ApduHighlighter())

        self._initialize(console)
        return self.logger


class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message, *args, **kwargs):
        if message != "\n":
            self.level(message)

    def flush(self):
        self.level(sys.stderr)


def init_logger(verbose: bool | None = None, console: Console | None = None):
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console, markup=True)],
    )
