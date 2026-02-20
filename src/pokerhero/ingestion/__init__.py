"""Ingestion pipeline: parse .txt session files and persist to the database."""

from pokerhero.ingestion.pipeline import IngestResult, ingest_directory, ingest_file
from pokerhero.ingestion.splitter import split_hands

__all__ = ["split_hands", "IngestResult", "ingest_file", "ingest_directory"]
