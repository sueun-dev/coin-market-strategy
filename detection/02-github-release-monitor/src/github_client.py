"""
GitHub REST API client for fetching repository releases.
Uses httpx for HTTP requests with timeout and rate limit handling.
Supports authenticated requests via GITHUB_TOKEN env var (5000 req/hr)
and unauthenticated requests (60 req/hr).
"""

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 10.0  # seconds


class GitHubClient:
    """Client for GitHub REST API release endpoints."""

    def __init__(self, token: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            logger.info("GitHub client initialized with auth token (5000 req/hr)")
        else:
            logger.info("GitHub client initialized without token (60 req/hr)")

        self._client = httpx.Client(
            base_url=GITHUB_API_BASE,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset: float | None = None

    def _update_rate_limit(self, response: httpx.Response):
        """Track rate limit info from response headers."""
        remaining = response.headers.get("x-ratelimit-remaining")
        reset_at = response.headers.get("x-ratelimit-reset")
        if remaining is not None:
            self._rate_limit_remaining = int(remaining)
        if reset_at is not None:
            self._rate_limit_reset = float(reset_at)

        if self._rate_limit_remaining is not None and self._rate_limit_remaining < 50:
            reset_in = ""
            if self._rate_limit_reset:
                secs = max(0, self._rate_limit_reset - time.time())
                reset_in = f" (resets in {secs:.0f}s)"
            logger.warning(
                "GitHub API rate limit low: %d remaining%s",
                self._rate_limit_remaining,
                reset_in,
            )

    def get_releases(self, repo: str, per_page: int = 10) -> list[dict]:
        """Fetch latest releases for a repository.

        Args:
            repo: Repository in 'owner/repo' format (e.g. 'cosmos/gaia')
            per_page: Number of releases to fetch (max 100)

        Returns:
            List of release dicts from GitHub API

        Raises:
            GitHubAPIError on non-recoverable errors
        """
        url = f"/repos/{repo}/releases"
        try:
            response = self._client.get(url, params={"per_page": per_page})
            self._update_rate_limit(response)

            if response.status_code == 200:
                return response.json()

            if response.status_code == 403:
                # Rate limit exceeded
                reset_at = self._rate_limit_reset
                if reset_at:
                    wait = max(0, reset_at - time.time())
                    logger.warning(
                        "Rate limit exceeded for %s. Resets in %.0fs. Skipping.",
                        repo, wait,
                    )
                else:
                    logger.warning("Rate limit exceeded for %s. Skipping.", repo)
                return []

            if response.status_code == 404:
                logger.error("Repository not found: %s", repo)
                return []

            if response.status_code == 301:
                logger.warning("Repository %s has been renamed/redirected", repo)
                return []

            logger.error(
                "GitHub API error for %s: %d %s",
                repo, response.status_code, response.text[:200],
            )
            return []

        except httpx.TimeoutException:
            logger.error("Timeout fetching releases for %s (%.1fs)", repo, self.timeout)
            return []
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching releases for %s: %s", repo, e)
            return []

    def check_repo_exists(self, repo: str) -> bool:
        """Check if a repository exists and is accessible."""
        url = f"/repos/{repo}"
        try:
            response = self._client.get(url)
            self._update_rate_limit(response)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    @property
    def rate_limit_remaining(self) -> int | None:
        return self._rate_limit_remaining

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
