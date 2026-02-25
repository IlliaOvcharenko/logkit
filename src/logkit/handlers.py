import logging

from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Defaults:
    level: int = logging.DEBUG
    fmt: str = "%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"

    def get_formatter(self) -> logging.Formatter:
        return logging.Formatter(self.fmt, self.datefmt)

class DefaultConsoleHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        defaults = Defaults()
        self.setLevel(defaults.level)
        self.setFormatter(defaults.get_formatter())


class DefaultFileHandler(logging.FileHandler):
    def __init__(self, fn: str):
        fn: Path = Path(fn)
        fn.parent.mkdir(exist_ok=True, parents=True)
        super().__init__(fn)
        defaults = Defaults()
        # self.setLevel(defaults.level)
        self.setFormatter(defaults.get_formatter())
