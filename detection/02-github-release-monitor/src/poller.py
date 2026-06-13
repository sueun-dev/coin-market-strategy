"""
Main polling loop for the GitHub Release Monitor.
Loads repo config, polls each repo, filters releases, and emits signals.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from .github_client import GitHubClient
from .release_filter import filter_releases
from .signal_emitter import SignalEmitter
from .state_store import StateStore

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent / "config" / "repos.json"
DEFAULT_POLL_INTERVAL = 1800  # 30 minutes


class ReleasePoller:
    """Polls GitHub repos for new upgrade/hardfork releases."""

    def __init__(
        self,
        config_file: Path | str = CONFIG_FILE,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        github_client: GitHubClient | None = None,
        state_store: StateStore | None = None,
        signal_emitter: SignalEmitter | None = None,
    ):
        self.config_file = Path(config_file)
        self.poll_interval = poll_interval
        self.client = github_client or GitHubClient()
        self.state_store = state_store or StateStore()
        self.signal_emitter = signal_emitter or SignalEmitter()
        self._repos: list[dict] = self._load_config()

    def _load_config(self) -> list[dict]:
        """Load repo list from config file."""
        if not self.config_file.exists():
            logger.error("Config file not found: %s", self.config_file)
            return []
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
            repos = data.get("repos", [])
            logger.info("Loaded %d repos from config", len(repos))
            return repos
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load config: %s", e)
            return []

    def poll_repo(self, repo_entry: dict) -> list[dict]:
        """Poll a single repo for new relevant releases.

        Args:
            repo_entry: Dict with 'repo', 'ticker', 'chain' keys

        Returns:
            List of emitted signals
        """
        repo = repo_entry["repo"]
        ticker = repo_entry["ticker"]
        chain = repo_entry["chain"]

        logger.debug("Polling %s (%s)...", repo, ticker)

        releases = self.client.get_releases(repo, per_page=10)
        if not releases:
            logger.debug("No releases found for %s", repo)
            return []

        # Filter for upgrade-related releases
        relevant = filter_releases(releases)
        if not relevant:
            logger.debug("No upgrade-related releases for %s", repo)
            return []

        signals = []
        for release_signal in relevant:
            tag = release_signal["tag"]

            # Check if already detected
            if not self.state_store.is_new(repo, tag):
                logger.debug("Already detected: %s @ %s", repo, tag)
                continue

            # Emit signal
            signal = self.signal_emitter.emit(
                repo=repo,
                ticker=ticker,
                chain=chain,
                release_signal=release_signal,
            )

            # Mark as detected
            self.state_store.mark_detected(repo, tag, signal)
            signals.append(signal)

        return signals

    def poll_all(self) -> list[dict]:
        """Poll all configured repos once."""
        all_signals = []
        for repo_entry in self._repos:
            try:
                signals = self.poll_repo(repo_entry)
                all_signals.extend(signals)
            except Exception as e:
                logger.error(
                    "Error polling %s: %s", repo_entry.get("repo", "?"), e,
                    exc_info=True,
                )
        return all_signals

    def poll_single(self, repo_slug: str) -> list[dict]:
        """Poll a specific repo by its slug (owner/repo).

        Args:
            repo_slug: Repository in 'owner/repo' format

        Returns:
            List of emitted signals
        """
        # Find matching entry in config
        entry = None
        for r in self._repos:
            if r["repo"] == repo_slug:
                entry = r
                break

        if entry is None:
            logger.warning(
                "Repo %s not found in config. Using defaults.", repo_slug
            )
            entry = {"repo": repo_slug, "ticker": "UNKNOWN", "chain": repo_slug.split("/")[0]}

        return self.poll_repo(entry)

    def run(self):
        """Run the polling loop indefinitely."""
        logger.info(
            "Starting release monitor loop (interval=%ds, repos=%d)",
            self.poll_interval,
            len(self._repos),
        )
        try:
            while True:
                logger.info("--- Poll cycle start ---")
                signals = self.poll_all()
                if signals:
                    logger.info("Poll cycle complete: %d new signals", len(signals))
                else:
                    logger.info("Poll cycle complete: no new signals")

                rate = self.client.rate_limit_remaining
                if rate is not None:
                    logger.info("GitHub API rate limit remaining: %d", rate)

                logger.info("Sleeping %ds until next cycle...", self.poll_interval)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Polling stopped by user")
        finally:
            self.close()

    def close(self):
        self.client.close()
