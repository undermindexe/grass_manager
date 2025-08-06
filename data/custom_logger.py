import logging
from rich.logging import RichHandler

logger = logging.getLogger("custom_logger")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(message)s")

rich_handler = RichHandler(
    markup=True,
    show_time=True,
    omit_repeated_times=False,
    show_level=True,
    show_path=False,
    rich_tracebacks=True,
)

rich_handler.setFormatter(formatter)

logger.handlers = []
logger.addHandler(rich_handler)
