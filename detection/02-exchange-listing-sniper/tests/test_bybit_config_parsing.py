"""Config-parsing tests for BybitSpotBuyer.

Covers two audit findings about .env.example values silently misbehaving:
  - BYBIT_SPOT_BUY_MODE shorthand ("quote") must normalize to a valid Bybit V5
    marketUnit ("quoteCoin") instead of being sent verbatim and rejected.
  - BYBIT_ORDER_TRANSPORT_PREFERENCE must honor the documented CSV form
    (e.g. "cpp_rest,cpp_ws,python_ws,python_rest") and the legacy single tokens.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bybit_spot_buyer import (
    BybitSpotBuyer,
    _normalize_buy_mode,
    _normalize_market_unit,
)


class TestMarketUnitNormalization:
    def test_quote_shorthand_maps_to_quoteCoin(self):
        assert _normalize_market_unit("quote") == "quoteCoin"
        assert _normalize_buy_mode("quote") == "quoteCoin"

    def test_base_shorthand_maps_to_baseCoin(self):
        assert _normalize_market_unit("base") == "baseCoin"

    def test_already_valid_values_preserved(self):
        assert _normalize_market_unit("quoteCoin") == "quoteCoin"
        assert _normalize_market_unit("baseCoin") == "baseCoin"

    def test_case_insensitive(self):
        assert _normalize_market_unit("QUOTE") == "quoteCoin"
        assert _normalize_market_unit("QuoteCoin") == "quoteCoin"

    def test_empty_falls_back_to_default(self):
        assert _normalize_market_unit("") == "quoteCoin"
        assert _normalize_market_unit(None) == "quoteCoin"
        assert _normalize_buy_mode("") == "quoteCoin"

    def test_unknown_value_passed_through_stripped(self):
        # Not a known alias: leave it to Bybit to reject, but trimmed.
        assert _normalize_market_unit("  weird  ") == "weird"


def _buyer_with_preference(pref: str) -> BybitSpotBuyer:
    """Build a buyer instance carrying only the preference string.

    Avoids the heavy constructor (which spins up C++/WS bridges) since
    _parse_transport_preference reads nothing but self.order_transport_preference.
    """
    buyer = BybitSpotBuyer.__new__(BybitSpotBuyer)
    buyer.order_transport_preference = pref
    return buyer


class TestTransportPreferenceParsing:
    def test_documented_csv_form_is_honored(self):
        buyer = _buyer_with_preference("cpp_rest,cpp_ws,python_ws,python_rest")
        # cpp_rest->cpp, cpp_ws->cpp_ws, python_ws->ws, python_rest->(fallback).
        assert buyer._parse_transport_preference() == ("cpp", "cpp_ws", "ws")

    def test_csv_reordering_changes_priority(self):
        buyer = _buyer_with_preference("python_ws,cpp_ws,cpp_rest")
        assert buyer._parse_transport_preference() == ("ws", "cpp_ws", "cpp")

    def test_partial_csv_appends_missing_transports(self):
        buyer = _buyer_with_preference("cpp_ws")
        # Legacy single token; preserves original ordering.
        assert buyer._parse_transport_preference() == ("cpp_ws", "cpp", "ws")

    def test_partial_csv_with_comma_appends_remaining(self):
        buyer = _buyer_with_preference("python_ws,")
        # ws named first, cpp/cpp_ws appended in default order.
        assert buyer._parse_transport_preference() == ("ws", "cpp", "cpp_ws")

    def test_unknown_tokens_ignored(self):
        buyer = _buyer_with_preference("bogus,cpp_ws,alsobogus")
        assert buyer._parse_transport_preference() == ("cpp_ws", "cpp", "ws")

    def test_legacy_ws_single_token_preserved(self):
        buyer = _buyer_with_preference("ws")
        assert buyer._parse_transport_preference() == ("ws", "cpp_ws", "cpp")

    def test_legacy_default_single_token_preserved(self):
        buyer = _buyer_with_preference("cpp")
        assert buyer._parse_transport_preference() == ("cpp", "cpp_ws", "ws")

    def test_unrecognized_single_token_defaults_to_cpp_first(self):
        buyer = _buyer_with_preference("garbage")
        assert buyer._parse_transport_preference() == ("cpp", "cpp_ws", "ws")
