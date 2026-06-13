"""Telegram post text normalization helpers."""

from __future__ import annotations

import html
import re


def clean_telegram_html_text(raw_html: str) -> str:
    """Convert Telegram public-channel message HTML into plain text."""
    text = re.sub(r"<br\b[^>]*>", "\n", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", text, flags=re.IGNORECASE | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )


def extract_title(text: str) -> str:
    """Return the first non-empty line from Telegram message text."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def has_nonspace(text: str) -> bool:
    return any(not char.isspace() for char in text)
