"""Upload handler: decodes a Dash dcc.Upload content string and ingests it.

Separated from the Dash callback so the logic can be unit-tested without
a running Dash server.
"""

import base64
import os
import sqlite3
import tempfile

from pokerhero.ingestion.pipeline import ingest_file


def handle_upload(
    content_string: str,
    filename: str,
    hero_username: str,
    conn: sqlite3.Connection,
) -> str:
    """Decode a dcc.Upload data-URI, ingest the hand history, return a status line.

    Args:
        content_string: Data URI from dcc.Upload contents
                        (e.g. 'data:text/plain;base64,<b64>').
        filename: Original filename, used in the status message.
        hero_username: The hero's PokerStars username.
        conn: Open SQLite connection.

    Returns:
        Human-readable status string, e.g.
        '✅ file.txt — 24 imported, 0 skipped, 0 failed'
    """
    _header, b64_data = content_string.split(",", 1)
    decoded = base64.b64decode(b64_data)

    # Write to a temp file so ingest_file can read it normally.
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(decoded)
        result = ingest_file(tmp_path, hero_username, conn)
        conn.commit()
    finally:
        os.unlink(tmp_path)

    if result.failed == 0 and result.skipped == 0:
        return f"✅ {filename} — {result.ingested} imported"
    return (
        f"{'✅' if result.ingested > 0 else '⚠️'} {filename} — "
        f"{result.ingested} imported, {result.skipped} skipped, "
        f"{result.failed} failed"
        + (f"\n{chr(10).join(result.errors)}" if result.errors else "")
    )
