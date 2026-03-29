"""Format signal/event dicts into readable Telegram messages.

Message templates follow the formats defined in STRATEGY.md.
"""

from datetime import datetime
from typing import Any

# Priority emoji prefixes
PRIORITY_PREFIX = {
    "P0": "\U0001f534",       # red circle
    "P0_CRITICAL": "\U0001f534\U0001f534\U0001f534",  # triple red for hack/critical
    "P1": "\U0001f7e0",       # orange circle
    "P2": "\U0001f7e1",       # yellow circle
    "P3": "\U0001f7e2",       # green circle
}


def format_message(signal: dict[str, Any]) -> str:
    """Route to the appropriate formatter based on event type.

    Args:
        signal: Event dict with keys: source, priority, type, data.

    Returns:
        Formatted message string.
    """
    event_type = signal.get("type", "")
    priority = signal.get("priority", "P3")

    formatters = {
        "signal_detected": _format_signal_detected,
        "position_open": _format_position_open,
        "premium_update": _format_premium_update,
        "hack_detected": _format_critical,
        "critical": _format_critical,
        "short_liquidation_risk": _format_short_liquidation_risk,
        "exit_complete": _format_exit_complete,
        "daily_report": _format_daily_report,
    }

    formatter_fn = formatters.get(event_type, _format_generic)
    text = formatter_fn(signal)

    # P0 repeat alert note
    if priority == "P0":
        text += "\n\n\u26a0\ufe0f This is a P0 alert. Repeat alerts will follow at 5 and 15 minutes until acknowledged."

    return text


def _format_signal_detected(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    prefix = PRIORITY_PREFIX.get(signal.get("priority", "P1"), PRIORITY_PREFIX["P1"])
    detection_time = d.get("detection_time", datetime.now().strftime("%Y-%m-%d %H:%M KST"))

    lines = [
        f"{prefix} [SIGNAL] {d.get('title', 'Signal Detected')}",
        "",
        f"Coin: {d.get('coin', 'N/A')}",
        f"Source: {signal.get('source', 'N/A')}",
        f"Target Grade: {d.get('grade', 'N/A')}",
        f"Lead Time: {d.get('lead_time', 'N/A')}",
        f"Recommended Exchange: {d.get('exchange', 'N/A')}",
        "",
        f"Direction: {d.get('direction', 'N/A')}",
        f"Urgency: {d.get('urgency', 'N/A')}",
        f"Estimated Size: {d.get('size', 'N/A')}",
        "",
        f"Detection Time: {detection_time}",
    ]
    return "\n".join(lines)


def _format_position_open(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    prefix = PRIORITY_PREFIX.get(signal.get("priority", "P1"), PRIORITY_PREFIX["P1"])

    lines = [
        f"{prefix} [POSITION OPEN] Delta Neutral Constructed",
        "",
        f"Coin: {d.get('coin', 'N/A')}",
        f"Domestic: {d.get('domestic', 'N/A')}",
        f"Overseas: {d.get('overseas', 'N/A')}",
        f"Quantity Match: {d.get('quantity_match', 'N/A')}",
        f"Liquidation Price Buffer: {d.get('liq_buffer', 'N/A')}",
        "",
        f"Total Deployed: {d.get('total_deployed', 'N/A')}",
    ]
    return "\n".join(lines)


def _format_premium_update(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    priority = signal.get("priority", "P2")
    prefix = PRIORITY_PREFIX.get(priority, PRIORITY_PREFIX["P2"])

    lines = [
        f"{prefix} [PREMIUM] {d.get('coin', 'N/A')} Premium Rising",
        "",
        "Current Premium:",
    ]

    premiums = d.get("premiums", {})
    for exchange, value in premiums.items():
        lines.append(f"  {exchange}: {value}")

    lines.extend([
        "",
        f"Peak: {d.get('peak', 'N/A')}",
        f"Status: {d.get('status', 'N/A')}",
        f"Recommendation: {d.get('recommendation', 'N/A')}",
    ])
    return "\n".join(lines)


def _format_critical(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    prefix = PRIORITY_PREFIX["P0_CRITICAL"]

    lines = [
        f"{prefix} [CRITICAL] {d.get('title', 'Critical Event Detected')}",
        "",
        f"Exchange: {d.get('exchange', 'N/A')}",
        f"Chain: {d.get('chain', 'N/A')}",
        f"Amount: {d.get('amount', 'N/A')}",
        f"Receiving Address: {d.get('receiving_address', 'N/A')}",
        f"Detection Time: {d.get('detection_time', 'N/A')}",
        "",
        "\u26a0\ufe0f Immediate Actions:",
    ]

    actions = d.get("actions", [
        "No new long entries",
        "Maintain existing position hold",
        "Confirm overseas short maintained",
        "Prepare for reverse premium additional buy",
    ])
    for action in actions:
        lines.append(f"- {action}")

    return "\n".join(lines)


def _format_short_liquidation_risk(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    prefix = PRIORITY_PREFIX["P0"]

    lines = [
        f"{prefix} [RISK] Approaching Short Liquidation Price",
        "",
        f"Coin: {d.get('coin', 'N/A')} / {d.get('exchange', 'N/A')}",
        f"Current Price: {d.get('current_price', 'N/A')}",
        f"Liquidation Price: {d.get('liquidation_price', 'N/A')}",
        f"Distance: {d.get('distance', 'N/A')}",
        "",
        "Required Action:",
    ]

    actions = d.get("actions", [
        f"Immediately deposit additional margin {d.get('margin_needed', 'N/A')}",
        "Or consider partial short close",
    ])
    for action in actions:
        lines.append(f"- {action}")

    lines.extend([
        "",
        f"Auto Margin Addition: {d.get('auto_margin', 'Disabled (manual confirmation required)')}",
    ])
    return "\n".join(lines)


def _format_exit_complete(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    prefix = PRIORITY_PREFIX.get(signal.get("priority", "P1"), PRIORITY_PREFIX["P1"])

    lines = [
        f"{prefix} [EXIT] Simultaneous Liquidation Complete",
        "",
        f"Coin: {d.get('coin', 'N/A')}",
        f"Exit Premium: {d.get('exit_premium', 'N/A')}",
        "",
        f"Domestic Sell: {d.get('domestic_sell', 'N/A')}",
        f"Overseas Short Close: {d.get('overseas_close', 'N/A')}",
        "",
        f"Net Profit: {d.get('net_profit', 'N/A')}",
        f"Execution Lag: {d.get('execution_lag', 'N/A')}",
        "",
        f"Funding Fee Cost: {d.get('funding_cost', 'N/A')}",
        f"Trading Fees: {d.get('trading_fees', 'N/A')}",
        f"Final Net Profit: {d.get('final_net_profit', 'N/A')}",
    ]
    return "\n".join(lines)


def _format_daily_report(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    prefix = PRIORITY_PREFIX["P3"]

    lines = [
        f"{prefix} [DAILY REPORT] {d.get('date', datetime.now().strftime('%Y-%m-%d'))}",
        "",
        f"Active Positions: {d.get('active_positions', 0)}",
        f"Premium Status: {d.get('premium_status', 'N/A')}",
        f"Accumulated Funding Fees: {d.get('funding_fees', 'N/A')}",
        f"Signals Being Monitored: {d.get('monitored_signals', 0)}",
        f"Signals Detected Today: {d.get('signals_today', 0)}",
    ]
    return "\n".join(lines)


def _format_generic(signal: dict[str, Any]) -> str:
    d = signal.get("data", {})
    priority = signal.get("priority", "P3")
    prefix = PRIORITY_PREFIX.get(priority, PRIORITY_PREFIX["P3"])
    event_type = signal.get("type", "unknown")
    source = signal.get("source", "unknown")

    lines = [
        f"{prefix} [{event_type.upper()}] Event from {source}",
        "",
    ]
    for key, value in d.items():
        lines.append(f"{key}: {value}")

    return "\n".join(lines)
