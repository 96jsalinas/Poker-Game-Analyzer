"""Application-wide configuration.

The DB path defaults to data/pokerhero.db relative to the project root.
Override by setting the POKERHERO_DB_PATH environment variable.
"""

import logging
import os
from pathlib import Path

DB_PATH: Path = Path(os.environ.get("POKERHERO_DB_PATH", "data/pokerhero.db"))


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the pokerhero logger hierarchy with a console handler.

    Idempotent — safe to call multiple times; handlers are only added once.

    Args:
        level: Logging level for the pokerhero root logger (default INFO).
    """
    logger = logging.getLogger("pokerhero")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
