"""Cross-engine idempotency tests for the Bybit orderLinkId.

Double-buy protection for a single listing relies on Bybit treating a repeated
``orderLinkId`` as a duplicate. The Python poller and the C++ ultra engine
(``cpp/listing_ultra_engine.cpp``) can both fire for the same (exchange,
message_id, ticker). If they build *different* orderLinkIds Bybit will NOT
dedup and the listing is bought twice.

These tests pin the Python orderLinkId to the canonical form documented in the
README and emitted by the C++ engine:

    ls-<exchange>-<message_id>-<ticker>   (truncated to 36 chars)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.poller import ExchangeListingPoller


# Bybit V5 caps orderLinkId at 36 chars; the C++ engine truncates with
# ``.substr(0, 36)``.
ORDER_LINK_ID_MAX_LEN = 36


def cpp_order_link_id(exchange: str, message_id: int, ticker: str) -> str:
    """Reproduce cpp/listing_ultra_engine.cpp:617-619 exactly.

        const std::string order_link_id =
            ("ls-" + std::string(exchange) + "-" + std::to_string(message_id)
             + "-" + ticker);
        ... order_link_id.substr(0, 36) ...
    """
    return ("ls-" + exchange + "-" + str(message_id) + "-" + ticker)[
        :ORDER_LINK_ID_MAX_LEN
    ]


def python_order_link_id(exchange: str, message_id: int, ticker: str) -> str:
    """Build the orderLinkId via the production Python code path.

    Mirrors poller.py: the per-channel prefix is ``ls-<exchange_code>-`` and the
    id is finished by ``_make_order_link_id``.
    """
    poller = ExchangeListingPoller.__new__(ExchangeListingPoller)
    prefix = f"ls-{ExchangeListingPoller._exchange_code(exchange)}-"
    return poller._make_order_link_id(
        prefix=prefix,
        message_id=message_id,
        ticker=ticker,
    )


CASES = [
    ("upbit", 12345, "ABC"),
    ("bithumb", 999999, "WLD"),
    ("upbit", 1, "X"),
    ("bithumb", 70000000, "DOGE"),
    # Long inputs that force the 36-char truncation on both paths.
    ("upbit", 88888888888888, "SUPERLONGTICKERNAME1234567890"),
    ("bithumb", 123456789012345, "ANOTHERVERYLONGTICKERSYMBOLXYZ"),
]


@pytest.mark.parametrize("exchange,message_id,ticker", CASES)
def test_python_matches_cpp_order_link_id(exchange, message_id, ticker):
    py = python_order_link_id(exchange, message_id, ticker)
    cpp = cpp_order_link_id(exchange, message_id, ticker)
    assert py == cpp, (
        f"orderLinkId diverges for ({exchange}, {message_id}, {ticker}): "
        f"python={py!r} cpp={cpp!r} -> Bybit would not dedup -> double buy"
    )
    assert len(py) <= ORDER_LINK_ID_MAX_LEN


@pytest.mark.parametrize("exchange,message_id,ticker", CASES)
def test_order_link_id_canonical_form(exchange, message_id, ticker):
    """The Python id uses the full exchange name, not a 1-letter abbreviation."""
    py = python_order_link_id(exchange, message_id, ticker)
    expected = ("ls-" + exchange + "-" + str(message_id) + "-" + ticker)[
        :ORDER_LINK_ID_MAX_LEN
    ]
    assert py == expected


def test_exchange_code_is_full_name():
    # Regression guard for the audit bug: upbit->u / bithumb->b broke dedup.
    assert ExchangeListingPoller._exchange_code("upbit") == "upbit"
    assert ExchangeListingPoller._exchange_code("bithumb") == "bithumb"


def test_order_link_id_truncated_to_36():
    py = python_order_link_id("upbit", 88888888888888, "SUPERLONGTICKERNAME1234567890")
    assert len(py) == ORDER_LINK_ID_MAX_LEN
