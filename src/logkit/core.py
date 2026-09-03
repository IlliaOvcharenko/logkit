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
    """Create a LoggerAdapter with a hierarchical logger name.

    Args:
        base_name: Base logger namespace (application name).
        module_name: Module identifier, typically ``__name__``.
        level: Logging level name (for example, ``"DEBUG"``).
        propagate: Whether messages should propagate to parent loggers.
            If not, handler attached to a main logger (like one in
            enter-point script) will not see any massages from an src
            folder loggers.

    Returns:
        logging.LoggerAdapter: Configured logger adapter.

    Examples:
        >>> logger = get_logger("my_app", __name__)
    """
    if module_name == "__main__":
        name = base_name
    else:
        name = f"{base_name}.{module_name}"

    logger = logging.getLogger(name)
    logger.setLevel(get_level_mapping()[level])
    logger.propagate = propagate
    logger_adapter = logging.LoggerAdapter(logger)
    return logger_adapter


def absolute_to_rel(fn: Path | str) -> Path | str:
    if Path(fn).is_relative_to(Path.cwd()):
        return Path(fn).relative_to(Path.cwd())
    else:
        return fn


def add_handlers(
    logger: logging.LoggerAdapter,
    application: str,
    handlers: list,
) -> logging.LoggerAdapter:
    """Attach handlers and add application name to logger extra fields.

    The function stores ``app_name`` (derived from the ``application`` path)
    into ``logger.extra`` so handlers such as ``TelegramHandler`` can enrich
    outgoing messages.

    Args:
        logger: Target logger adapter.
        application: Application file path, usually ``__file__``.
        handlers: List of initialized logging handlers to attach.

    Returns:
        logging.LoggerAdapter: Same adapter with handlers attached.

    Examples:
        >>> add_handlers(logger, __file__, [DefaultConsoleHandler()])
    """

    app_path = absolute_to_rel(application)
    logger.extra = {
        "app_name": app_path.stem if isinstance(app_path, Path) else app_path
    }

    for h in handlers:
        logger.logger.addHandler(h)

    return logger


def catch_all_exceptions(
    logger: logging.LoggerAdapter,
    *,
    reraise: bool = False,
) -> Callable:
    """Create a decorator that logs and optionally re-raises exceptions.

    Args:
        logger: Logger used to report caught exceptions.
        reraise: If ``True``, re-raise the original exception after logging.

    Returns:
        Callable: Decorator wrapping a function with exception handling.

    Examples:
        >>> @catch_all_exceptions(logger, reraise=False)
        ... def main():
        ...     ...
    """
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

    if not log_filename_done and Path(fn).is_relative_to(Path.cwd()):
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
    """Log current enter-point information. Done only ones, even if repeated.

    Logs filename, git metadata (if available), and parameter values exactly
    once per Python process.

    Args:
        logger: Logger used for output.
        fn: Current file path (usually ``__file__``).
        params: Mapping of run parameters (for example, ``locals()``).

    Examples:
        >>> log_run(logger, __file__, locals())
    """
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
    """Log a pandas DataFrame in okay format.

    If pandas is not installed, the function logs a debug message and returns
    without raising.

    Args:
        logger: Logger used for output.
        df: pandas DataFrame object to print.
        title: Optional title line shown above the table.
        v2s: Optional value-to-string converter for cell values.
        level: Logging level name used for DataFrame rows.
        col_size: Optional minimum width for each column.

    Raises:
        TypeError: If ``df`` is not a pandas DataFrame.

    Examples:
        >>> log_df(logger, df, v2s=lambda v: str(v))
    """
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
