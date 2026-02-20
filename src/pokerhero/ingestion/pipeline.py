"""Ingestion pipeline: read .txt session files, parse, and persist to SQLite."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from pokerhero.database.db import insert_session, save_parsed_hand
from pokerhero.ingestion.splitter import split_hands
from pokerhero.parser.hand_parser import HandParser

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Summary of a single file ingestion run."""

    file_path: str
    ingested: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def ingest_file(
    path: Path | str,
    hero_username: str,
    conn: sqlite3.Connection,
) -> IngestResult:
    """Parse a .txt session file and persist all hands to the database.

    One session row is created per file using the first hand's metadata and
    timestamp. Hands whose source_hand_id already exists in the database are
    silently skipped (duplicate import protection). Any hand that fails to
    parse or insert for any other reason is counted as failed.

    Args:
        path: Path to the .txt session file.
        hero_username: The hero's PokerStars username.
        conn: An open SQLite connection (created via init_db).

    Returns:
        IngestResult with counts of ingested, skipped, and failed hands.
    """
    path = Path(path)
    result = IngestResult(file_path=str(path))

    logger.info("Starting ingestion: %s", path)

    blocks = split_hands(path.read_text(encoding="utf-8"))
    if not blocks:
        logger.info("Ingestion complete — %s: no hand blocks found", path.name)
        return result

    parser = HandParser(hero_username=hero_username)

    # Parse the first block to get session metadata for the session row.
    try:
        first_parsed = parser.parse(blocks[0])
    except Exception as exc:
        result.failed = len(blocks)
        result.errors.append(f"Could not parse first hand for session metadata: {exc}")
        logger.error("Failed to parse session metadata from %s: %s", path.name, exc)
        return result

    session_id = insert_session(
        conn,
        first_parsed.session,
        start_time=first_parsed.hand.timestamp.isoformat(),
    )
    conn.commit()
    logger.info("Session %d created for %s", session_id, path.name)

    for block in blocks:
        try:
            parsed = parser.parse(block)
            save_parsed_hand(conn, parsed, session_id)
            conn.commit()
            result.ingested += 1
            logger.debug("Ingested hand %s", parsed.hand.hand_id)
        except sqlite3.IntegrityError:
            conn.rollback()
            result.skipped += 1
            logger.warning("Skipped duplicate hand in %s", path.name)
        except Exception as exc:
            conn.rollback()
            result.failed += 1
            result.errors.append(str(exc))
            logger.error("Failed to ingest hand from %s: %s", path.name, exc)

    logger.info(
        "Ingestion complete — %s: %d ingested, %d skipped, %d failed",
        path.name,
        result.ingested,
        result.skipped,
        result.failed,
    )
    return result


def ingest_directory(
    dir_path: Path | str,
    hero_username: str,
    conn: sqlite3.Connection,
) -> list[IngestResult]:
    """Ingest all .txt files in a directory.

    Files are processed in sorted order. Non-.txt files are ignored.

    Args:
        dir_path: Path to the directory containing .txt session files.
        hero_username: The hero's PokerStars username.
        conn: An open SQLite connection (created via init_db).

    Returns:
        List of IngestResult, one per .txt file found.
    """
    return [
        ingest_file(txt_file, hero_username, conn)
        for txt_file in sorted(Path(dir_path).glob("*.txt"))
    ]
