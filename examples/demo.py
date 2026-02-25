from logkit.core import (
    get_logger,
    add_handlers,
    catch_all_exceptions,
    log_run,
    log_df,
)
from logkit.handlers import (
    DefaultConsoleHandler,
    DefaultFileHandler,
)

from logkit.web_handlers import TelegramHandler

logger = get_logger("my_app", __name__)


import pandas as pd
from fire import Fire

from subfolder import log_smth


@catch_all_exceptions(logger, reraise=False)
def main(
    param1: str,
    param2: str,
):
    log_run(logger, __file__, locals())
    log_run(logger, __file__, locals())

    logger.info("Test default")
    df = pd.DataFrame({
        "nums": list(range(5)),
        "str": ["ttt"] * 5,
    })
    log_df(logger, df, v2s=lambda v: str(v))
    log_smth()
    val = 1/0


if __name__ == "__main__":
    add_handlers(
        logger,
        __file__,
        [
            DefaultConsoleHandler(),
            DefaultFileHandler("logs/demo.log"),
            # TelegramHandler(
            #     "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            #     ["iovcharenko"],
            # )
        ],
    )
    Fire(main)
    logger.info("after zero div")
