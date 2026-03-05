# ✍️  LogKit
This project is my personal lib with some logging helpers.

I use it in my other project to make logging configuration simpler.

## Public API

Check demo script ([examples/demo.py](./examples/demo.py)) and corresponding log output ([examples/demo.log](./examples/demo.log))

<details>
<summary><code>get_logger(...)</code></summary>

```python
get_logger(
    base_name: str,
    module_name: str,
    *,
    level: str = "DEBUG",
    propagate: bool = True,
) -> logging.LoggerAdapter
```

Create logger with a name representing current project.
Calls from project subfolder will create a correct hierarchy of loggers.

  ```python
  from logkit.core import get_logger
  logger = get_logger("my_app", __name__)
  ```

Parameters:
- `base_name`: `str`, prefix for logger name.
- `module_name`: `str` (usually `__name__`, including `"__main__"`), defines module part of logger name.
- `level`: `str` (for example `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`), sets logger level threshold.
- `propagate`: `bool`, enables/disables propagation to parent loggers.
</details>

<details>
<summary><code>add_handlers(...)</code></summary>

```python
add_handlers(
    logger: logging.LoggerAdapter,
    application: str,
    handlers: list,
) -> logging.LoggerAdapter
```

Attach configured handlers to logger and keep application context for records.

  ```python
  from logkit.core import add_handlers
  from logkit.handlers import DefaultConsoleHandler
  add_handlers(logger, __file__, [DefaultConsoleHandler()])
  ```

Parameters:
- `logger`: `logging.LoggerAdapter`, logger instance created by `get_logger` call.
- `application`: `str` (often `__file__`), used to set `app_name` in logger extra context.
- `handlers`: `list`, every handler in list is attached to the logger.
</details>

<details>
<summary><code>catch_all_exceptions(...)</code></summary>

```python
catch_all_exceptions(
    logger: logging.LoggerAdapter,
    *,
    reraise: bool = False,
) -> Callable
```

Wrap function execution with exception logging.
Can optionally raise the original exception after logging.

  ```python
  from logkit.core import catch_all_exceptions

  @catch_all_exceptions(logger, reraise=False)
  def main() -> None:
      ...
  ```

Parameters:
- `logger`: `logging.LoggerAdapter`, logger instance created by `get_logger` call.
- `reraise`: `bool`, if `True`, exception is raised again after logging.
</details>

<details>
<summary><code>log_run(...)</code></summary>

```python
log_run(
    logger: logging.LoggerAdapter,
    fn: str,
    params: Mapping[str, Any],
) -> None
```

Log run context for current execution.
That includes filename, git commit (if available), specified paramters.
Usually called at the beginning of `main`, that allow to track when did the script started and input parameters.

  ```python
  from logkit.core import log_run

  def main(param1: str, param2: str):
      log_run(logger, __file__, locals())
  ```

Outputs:
  ```
  2026-03-05 02:13:21 :: my_app :: INFO :: Run: examples/demo.py
  2026-03-05 02:13:21 :: my_app :: INFO :: Current branch is: main
  commit: 660c911bcecf7aa58bfeb7cc9abc463bde5e2768
  2026-03-05 02:13:21 :: my_app :: INFO :: Params:
  2026-03-05 02:13:21 :: my_app :: INFO ::   param1: test1
  2026-03-05 02:13:21 :: my_app :: INFO ::   param2: test2
  ```

Parameters:
- `logger`: `logging.LoggerAdapter`, logger instance created by `get_logger` call.
- `fn`: `str` (often `__file__`), script filename.
- `params`: `Mapping[str, Any]`, values are logged as run parameters.
</details>

<details>
<summary><code>log_df(...)</code></summary>

```python
log_df(
    logger: logging.LoggerAdapter,
    df: Any,
    title: str | None = None,
    v2s: Callable[[Any], str] | None = None,
    level: str = "INFO",
    col_size: int | None = None,
) -> None
```

Log DataFrame data in a readable table-like text form.

  ```python
  from logkit.core import log_df
  log_df(logger, df, v2s=lambda v: str(v))
  ```

Outputs:
  ```
  2026-03-05 02:13:21 :: my_app :: INFO ::    nums str
  2026-03-05 02:13:21 :: my_app :: INFO :: 0: 0    ttt
  2026-03-05 02:13:21 :: my_app :: INFO :: 1: 1    ttt
  2026-03-05 02:13:21 :: my_app :: INFO :: 2: 2    ttt
  2026-03-05 02:13:21 :: my_app :: INFO :: 3: 3    ttt
  2026-03-05 02:13:21 :: my_app :: INFO :: 4: 4    ttt
  ```

Parameters:
- `logger`: `logging.LoggerAdapter`, logger instance created by `get_logger` call.
- `df`: `Any` (expected `pandas.DataFrame`), source data to print.
- `title`: `str | None`, optional header line before table.
- `v2s`: `Callable[[Any], str] | None`, converts each cell value to string before alignment.
- `level`: `str` (for example `"INFO"`, `"DEBUG"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`), selects logging level for DataFrame output.
- `col_size`: `int | None`, minimum width per output column.
</details>

<details>
<summary><code>DefaultConsoleHandler(...)</code></summary>

```python
DefaultConsoleHandler()
```

Create console handler with project default formatting.

  ```python
  from logkit.handlers import DefaultConsoleHandler
  handler = DefaultConsoleHandler()
  ```

Parameters:
- None
</details>

<details>
<summary><code>DefaultFileHandler(...)</code></summary>

```python
DefaultFileHandler(
    fn: str,
)
```

Create file handler with project default formatting.

  ```python
  from logkit.handlers import DefaultFileHandler
  handler = DefaultFileHandler("logs/demo.log")
  ```

Parameters:
- `fn`: `str`, target log file path (parent directories are created if needed).
</details>

<details>
<summary><code>TelegramHandler(...)</code></summary>

```python
TelegramHandler(
    token: str,
    username: str | list[str],
    prefix: str = "",
    notify_levels: list[str] = ["INFO", "ERROR", "CRITICAL", "WARNING"],
    only_level: str | None = None,
)
```

Create handler for sending log messages to Telegram.

  ```python
  from logkit.web_handlers import TelegramHandler
  handler = TelegramHandler("BOT_TOKEN", ["username"])
  ```

Parameters:
- `token`: `str`, authenticates bot API requests.
- `username`: `str | list[str]`, selects Telegram users/chats for delivery.
- `prefix`: `str`, prepends text to every sent message.
- `notify_levels`: `list[str]`, levels in this list are sent with active notifications.
- `only_level`: `str | None`, `None` sends all levels; otherwise sends only matching level.
</details>
