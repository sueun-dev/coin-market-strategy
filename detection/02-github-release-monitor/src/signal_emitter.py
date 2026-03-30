"""
Signal emitter for GitHub release monitor.
Emits detected upgrade/hardfork signals as JSON files and console output.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SIGNALS_DIR = Path(__file__).parent.parent / "data" / "signals"


class SignalEmitter:
    """Emit structured signals as JSON files and console output."""

    def __init__(self, signals_dir: Path | str = SIGNALS_DIR):
        self.signals_dir = Path(signals_dir)
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self._emitted: list[dict] = []

    def emit(
        self,
        repo: str,
        ticker: str,
        chain: str,
        release_signal: dict,
    ) -> dict:
        """Emit a signal for a detected release.

        Args:
            repo: GitHub repo (e.g. 'cosmos/gaia')
            ticker: Coin ticker (e.g. 'ATOM')
            chain: Chain name (e.g. 'cosmos')
            release_signal: Filtered release data from release_filter

        Returns:
            Emitted signal dict
        """
        now = datetime.now(timezone.utc)

        signal = {
            "signal_id": uuid.uuid4().hex[:12],
            "signal_type": "github_release",
            "chain": chain,
            "ticker": ticker,
            "repo": repo,
            "release_tag": release_signal["tag"],
            "release_title": release_signal["title"],
            "release_url": release_signal["url"],
            "keywords_matched": release_signal["keywords_matched"],
            "is_breaking": release_signal["is_breaking"],
            "is_mandatory": release_signal["is_mandatory"],
            "is_pre_release": release_signal["is_pre_release"],
            "signal_level": release_signal["signal_level"],
            "version_jump": release_signal.get("version_jump"),
            "confidence": release_signal["confidence"],
            "published_at": release_signal["published_at"],
            "detected_at": now.isoformat(),
        }

        # Save to file (atomic write)
        tag_safe = release_signal["tag"].replace("/", "_")
        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{chain}_{tag_safe}.json"
        filepath = self.signals_dir / filename
        tmp = filepath.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(signal, f, indent=2, ensure_ascii=False)
        os.replace(tmp, filepath)

        self._emitted.append(signal)
        self._print_signal(signal)

        logger.info(
            "Signal emitted: %s %s [%s] -> %s",
            ticker, release_signal["tag"], release_signal["signal_level"], filepath.name,
        )

        return signal

    def _print_signal(self, signal: dict):
        """Print signal in a readable console format."""
        level_marker = "PRE-WARNING" if signal["signal_level"] == "pre-warning" else "ALERT"
        breaking = "YES" if signal["is_breaking"] else "no"
        mandatory = "YES" if signal["is_mandatory"] else "no"

        print("\n" + "=" * 60)
        print(f"[{level_marker}] GitHub Release Detected")
        print("=" * 60)
        print(f"  Chain:       {signal['chain']} ({signal['ticker']})")
        print(f"  Repo:        {signal['repo']}")
        print(f"  Tag:         {signal['release_tag']}")
        print(f"  Title:       {signal['release_title']}")
        print(f"  Keywords:    {', '.join(signal['keywords_matched']) if signal['keywords_matched'] else 'N/A'}")
        print(f"  Breaking:    {breaking}")
        print(f"  Mandatory:   {mandatory}")
        if signal.get("version_jump"):
            print(f"  Version:     {signal['version_jump']['description']}")
        print(f"  Pre-release: {'yes' if signal['is_pre_release'] else 'no'}")
        print(f"  Confidence:  {signal['confidence']}")
        print(f"  Published:   {signal['published_at']}")
        print(f"  URL:         {signal['release_url']}")
        print(f"  Detected:    {signal['detected_at']}")
        print("=" * 60)

    def get_emitted(self) -> list[dict]:
        return self._emitted.copy()
