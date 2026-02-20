"""Utility for splitting a multi-hand PokerStars session file into individual hand blocks."""

import re


def split_hands(text: str) -> list[str]:
    """Split a raw session file into individual hand blocks.

    Each block starts with 'PokerStars Hand #'. Blocks are stripped of
    leading/trailing whitespace and empty blocks are discarded.

    Args:
        text: Raw text content of a PokerStars .txt session file.

    Returns:
        List of hand block strings, one per hand. Empty list if no hands found.
    """
    blocks = re.split(r"(?=PokerStars Hand #)", text)
    return [b.strip() for b in blocks if b.strip().startswith("PokerStars Hand #")]
