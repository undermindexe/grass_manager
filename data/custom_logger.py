import os
import logging
from rich.logging import RichHandler

log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("custom_logger")
logger.setLevel(logging.DEBUG)


rich_handler = RichHandler(
    markup=True,
    show_time=True,
    omit_repeated_times=False,
    show_level=True,
    show_path=False,
    rich_tracebacks=True,
)

file_handler = logging.FileHandler(r"log\\log.txt", mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

logger.handlers = []
logger.addHandler(rich_handler)
logger.addHandler(file_handler)