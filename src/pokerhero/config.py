"""Application-wide configuration.

The DB path defaults to data/pokerhero.db relative to the project root.
Override by setting the POKERHERO_DB_PATH environment variable.
"""

import os
from pathlib import Path

DB_PATH: Path = Path(os.environ.get("POKERHERO_DB_PATH", "data/pokerhero.db"))
