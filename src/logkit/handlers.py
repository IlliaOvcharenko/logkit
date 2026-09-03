import logging

from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Defaults:
    level: int = logging.DEBUG
    fmt: str = "%(asctime)s :: %(levelname)s :: %(message)s"
    # fmt: str = "%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"

    def get_formatter(self) -> logging.Formatter:
        return logging.Formatter(self.fmt, self.datefmt)

class DefaultConsoleHandler(logging.StreamHandler):
    """Console stream handler with project default formatting.

    The handler uses ``Defaults`` for level and formatter setup.
    """

    def __init__(self):
        """Initialize console handler with default level and formatter."""
        super().__init__()
        defaults = Defaults()
        self.setLevel(defaults.level)
        self.setFormatter(defaults.get_formatter())


class DefaultFileHandler(logging.FileHandler):
    """File handler with project default formatting.

    The handler creates parent directories for the log file path if they do
    not exist.
    """

    def __init__(self, fn: str):
        """Initialize file handler.

        Args:
            fn: Path to the output log file.
        """
        fn: Path = Path(fn)
        fn.parent.mkdir(exist_ok=True, parents=True)
        super().__init__(fn)
        defaults = Defaults()
        # self.setLevel(defaults.level)
        self.setFormatter(defaults.get_formatter())
