import sys
import traceback
import logging

from functools import wraps
from pathlib import Path

from logging import (
    getLevelNamesMapping as get_level_mapping
)
from typing import (
    Callable,
    Any,
    Mapping,
)


def get_logger(
    base_name: str,
    module_name: str,
    *,
    level: str = "DEBUG",
    propagate: bool = True,
) -> logging.LoggerAdapter:
    if module_name == "__main__":
        name = base_name
    else:
        name = f"{base_name}.{module_name}"

    logger = logging.getLogger(name)
    logger.setLevel(get_level_mapping()[level])
    logger.propagate = propagate
    logger_adapter = logging.LoggerAdapter(logger)
    return logger_adapter


def absolute_to_rel(fn: Path | str) -> Path:
    return Path(fn).relative_to(Path.cwd())


def add_handlers(
    logger: logging.LoggerAdapter,
    application: str,
    handlers: list,
) -> logging.LoggerAdapter:

    application_path: Path = absolute_to_rel(application)
    logger.extra = {"app_name": application_path.name}

    for h in handlers:
        logger.logger.addHandler(h)

    return logger


def catch_all_exceptions(
    logger: logging.LoggerAdapter,
    *,
    reraise: bool = False,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # try to run several times if crashes
            # add n_attempts as param, then
            # for attempt in range(1, n_attempts + 1):
            try:
                retval = func(*args, **kwargs)
                return retval
            except Exception as exc:
                tbe = traceback.TracebackException(*sys.exc_info())
                last = tbe.stack[-1] if tbe.stack else None
                file_at = getattr(last, "filename", "<unknown>")
                line_at = getattr(last, "lineno", "<unknown>")
                logger.warning(
                    f"Caught {type(exc).__name__} " \
                    f"at {file_at}:{line_at} - {exc}",
                    exc_info=False,
                )
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def log_git_info(
    logger: logging.LoggerAdapter,
    cwd: str | Path | None = None
) -> None:
    try:
        from pygit2 import Repository
    except Exception:
        logger.debug("pygit2 is not installed; skipping log_git_info")
        return

    try:
        cwd = Path.cwd() if cwd is None else cwd
        cwd = str(cwd)

        repo = Repository(cwd)

        logger.info(
            f"Current branch is: {repo.head.shorthand}\n" \
            f"commit: {repo.head.target}"
        )
    except Exception as e:
        logger.warning(f"Error getting git info: {e}")


log_filename_done: bool = False
def log_filename(
    logger: logging.LoggerAdapter,
    fn: str
) -> None:
    global log_filename_done

    if not log_filename_done:
        logger.info(f"Run: {Path(fn).relative_to(Path.cwd())}")
        log_filename_done = True


def log_params(
    logger: logging.LoggerAdapter,
    params: Mapping[str, Any],
) -> None:
    if len(params) == 0:
        logger.info("Params are empty")

    else:
        logger.info("Params:")
        for k, v in params.items():
            logger.info(f"  {k}: {v}")


log_run_done: bool = False
def log_run(
    logger: logging.LoggerAdapter,
    fn: str,
    params: Mapping[str, Any],
) -> None:
    global log_run_done

    if not log_run_done:
        log_filename(logger, fn)
        log_git_info(logger)
        log_params(logger, params)

        log_run_done = True


def log_df(
    logger: logging.LoggerAdapter,
    df: Any,
    title: str | None = None,
    v2s: Callable[[Any], str] | None = None,
    level: str = "INFO",
    col_size: int | None = None,
) -> None:
    try:
        import pandas as pd
    except Exception:
        logger.debug("pandas is not installed; skipping log_df")
        return

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"log_df expect a pandas DataFrame object as df param"
        )

    level_map = get_level_mapping()
    v2s = (lambda v: v) if v2s is None else v2s

    row_names = df.index.tolist()
    row_names = [str(r) for r in row_names]
    row_names = [r + ":" for r in row_names]

    first_col_size = max([len(c) for c in row_names]) + 1
    row_names = [r.ljust(first_col_size) for  r in row_names]

    col_names = df.columns.tolist()

    # if col_size is None:
    #     col_size = max([len(c) for c in col_names]) + 1

    col_size_v = [len(c) + 1 for c in col_names]
    if col_size is not None:
        col_size_v = [max(col_size, c) for c in col_size_v]

    if title is not None:
        logger.log(level_map[level], f"DataFrame: {title}")

    col_names = [c.ljust(col_size_v[i]) for i, c in enumerate(col_names)]
    col_name_row = "".join(col_names)
    col_name_row = (" " * first_col_size) + col_name_row

    logger.log(level_map[level], col_name_row)

    for irow in range(df.shape[0]):
        current_row = [
            v2s(v).ljust(col_size_v[i])
            for (i, v) in enumerate(df.iloc[irow])
        ]
        current_row = "".join(current_row)
        current_row = row_names[irow] + current_row
        logger.log(level_map[level], current_row)
