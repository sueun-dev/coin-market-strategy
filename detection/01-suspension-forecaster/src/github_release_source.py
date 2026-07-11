"""GitHub release source for early suspension forecasting."""

from __future__ import annotations

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 10.0
MODULE_DIR = Path(__file__).parent.parent
REPO_ROOT = MODULE_DIR.parent.parent
ENV_FILES = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

UPGRADE_KEYWORDS = [
    "upgrade",
    "hardfork",
    "hard fork",
    "hard-fork",
    "network upgrade",
    "mainnet upgrade",
    "mandatory update",
    "breaking change",
    "consensus",
    "migration",
    "chain upgrade",
    "validator",
]
STRONG_UPGRADE_KEYWORDS = [
    "hardfork",
    "hard fork",
    "hard-fork",
    "network upgrade",
    "mainnet upgrade",
    "mandatory update",
    "chain upgrade",
    "consensus",
]
FALSE_POSITIVE_CONTEXTS = [
    "dependency upgrade",
    "dependency update",
    "dependencies",
    "package upgrade",
    "package update",
    "database migration",
    "schema migration",
    "documentation update",
    "docs update",
    "ci update",
    "test suite",
]
EXCLUDE_KEYWORDS = [
    "testnet",
    "devnet",
    "aeneid",
    "preview network",
    "internal release",
]
PRE_RELEASE_PATTERNS = ["rc", "alpha", "beta", "preview", "dev"]
SEMVER_RE = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]?(rc|alpha|beta|preview|dev)[\d.]*)?(?:[-+][0-9A-Za-z.]+)?$",
    re.IGNORECASE,
)


class GitHubReleaseSourceError(RuntimeError):
    """Raised when GitHub releases cannot be trusted as a source for this poll."""


def _load_token_from_env_files() -> Optional[str]:
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "GITHUB_TOKEN":
                return value.strip().strip('"').strip("'")
    return None


def _load_token_from_gh() -> Optional[str]:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    token = result.stdout.strip()
    return token or None


def _parse_semver(tag: str) -> Optional[tuple[int, int, int, Optional[str]]]:
    match = SEMVER_RE.fullmatch((tag or "").strip())
    if not match:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        match.group(4).lower() if match.group(4) else None,
    )


def _is_recent_release(release: dict[str, Any], max_age_hours: int) -> bool:
    published_at = release.get("published_at")
    if not published_at:
        return False
    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    age_seconds = (datetime.now(timezone.utc) - published).total_seconds()
    return age_seconds <= max_age_hours * 3600


def _detect_version_jump(tag: str, previous_tags: list[str]) -> Optional[str]:
    current = _parse_semver(tag)
    if not current:
        return None
    cur_major, cur_minor, cur_patch, _ = current
    for previous_tag in previous_tags:
        prev = _parse_semver(previous_tag)
        if not prev:
            continue
        prev_major, prev_minor, prev_patch, _ = prev
        if (cur_major, cur_minor, cur_patch) == (prev_major, prev_minor, prev_patch):
            continue
        if cur_major > prev_major:
            return "major"
        if cur_major == prev_major and cur_minor > prev_minor:
            return "minor"
        break
    return None


def _extract_event_time_from_text(text: str) -> Optional[str]:
    iso_match = re.search(
        r"(20\d\d-\d\d-\d\d[ T]\d\d:\d\d(?::\d\d)?(?: ?UTC|Z)?)",
        text,
        re.IGNORECASE,
    )
    if iso_match:
        raw = iso_match.group(1).replace(" UTC", "+00:00").replace("Z", "+00:00")
        raw = raw.replace(" ", "T")
        try:
            return datetime.fromisoformat(raw).astimezone(timezone.utc).isoformat()
        except ValueError:
            return None

    month_match = re.search(
        r"(\d{1,2}:\d{2})\s*UTC.*?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?[,]?\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if month_match:
        time_part, month_name, day, year = month_match.groups()
        raw = f"{month_name} {day} {year} {time_part} UTC"
        try:
            dt = datetime.strptime(raw, "%B %d %Y %H:%M UTC")
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return None
    return None


class GitHubReleaseSource:
    def __init__(
        self,
        token: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        gh_token_loader: Optional[Callable[[], Optional[str]]] = None,
    ):
        self._gh_token_loader = gh_token_loader or _load_token_from_gh
        self._gh_token_attempted = False
        self.token = token or os.getenv("GITHUB_TOKEN") or _load_token_from_env_files()
        if not self.token:
            self._gh_token_attempted = True
            self.token = self._gh_token_loader()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            logger.info("GitHub release source initialized with auth token")
        else:
            logger.warning("GitHub release source initialized without auth token")
        self._client = httpx.Client(
            base_url=GITHUB_API_BASE,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        self._rate_limit_remaining: Optional[int] = None

    def _try_replace_rejected_token_with_gh_token(self) -> bool:
        if self._gh_token_attempted:
            return False
        self._gh_token_attempted = True
        token = self._gh_token_loader()
        if not token or token == self.token:
            return False
        self.token = token
        self._client.headers["Authorization"] = f"Bearer {token}"
        logger.warning(
            "GitHub env token rejected; retrying releases with `gh auth token`"
        )
        return True

    def close(self):
        self._client.close()

    def collect(
        self, target: dict[str, Any], default_recent_release_hours: int
    ) -> list[dict[str, Any]]:
        source_cfg = target.get("sources", {}).get("github_release")
        if not source_cfg:
            return []

        repo = source_cfg["repo"]
        recent_hours = int(
            source_cfg.get("recent_release_hours", default_recent_release_hours)
        )
        releases = self._get_releases(repo)
        if not releases:
            return []

        results = []
        tags = [release.get("tag_name", "") for release in releases]
        for index, release in enumerate(releases):
            if not _is_recent_release(release, recent_hours):
                continue
            event = self._release_to_event(target, repo, release, tags[index + 1 :])
            if event:
                results.append(event)
        return results

    def _get_releases(self, repo: str) -> list[dict[str, Any]]:
        try:
            response = self._client.get(
                f"/repos/{repo}/releases", params={"per_page": 10}
            )
        except httpx.HTTPError as exc:
            raise GitHubReleaseSourceError(
                f"GitHub releases request failed for {repo}: {exc}"
            ) from exc

        if response.status_code == 401 and self.token:
            if self._try_replace_rejected_token_with_gh_token():
                try:
                    response = self._client.get(
                        f"/repos/{repo}/releases", params={"per_page": 10}
                    )
                except httpx.HTTPError as exc:
                    raise GitHubReleaseSourceError(
                        f"GitHub releases gh-auth retry failed for {repo}: {exc}"
                    ) from exc
                if response.status_code == 200:
                    self._rate_limit_remaining = int(
                        response.headers.get("x-ratelimit-remaining", "0") or "0"
                    )
                    return response.json()

            if response.status_code == 401:
                # The original token and any gh fallback were rejected. Public
                # release endpoints can still be useful, so try one last request
                # without Authorization before surfacing the source error.
                self.token = None
                self._client.headers.pop("Authorization", None)
                try:
                    response = self._client.get(
                        f"/repos/{repo}/releases", params={"per_page": 10}
                    )
                except httpx.HTTPError as exc:
                    raise GitHubReleaseSourceError(
                        f"GitHub releases unauthenticated retry failed for {repo}: {exc}"
                    ) from exc

        self._rate_limit_remaining = int(
            response.headers.get("x-ratelimit-remaining", "0") or "0"
        )
        if response.status_code == 200:
            return response.json()
        body = response.text[:300].replace("\n", " ").strip()
        raise GitHubReleaseSourceError(
            f"GitHub releases unavailable for {repo}: HTTP {response.status_code}"
            + (f" ({body})" if body else "")
        )

    def _release_to_event(
        self,
        target: dict[str, Any],
        repo: str,
        release: dict[str, Any],
        previous_tags: list[str],
    ) -> Optional[dict[str, Any]]:
        if release.get("draft"):
            return None

        tag = release.get("tag_name", "")
        title = release.get("name", "") or tag
        body = release.get("body", "") or ""
        search_text = f"{tag} {title} {body}".lower()
        if any(keyword in search_text for keyword in EXCLUDE_KEYWORDS):
            return None

        keywords_matched = [kw for kw in UPGRADE_KEYWORDS if kw in search_text]
        strong_keywords_matched = [
            kw for kw in STRONG_UPGRADE_KEYWORDS if kw in search_text
        ]
        if (
            any(context in search_text for context in FALSE_POSITIVE_CONTEXTS)
            and not strong_keywords_matched
        ):
            return None
        version_jump = _detect_version_jump(tag, previous_tags)
        is_pre_release = bool(
            release.get("prerelease")
            or any(
                re.search(rf"[-.]?{pattern}\d*", tag.lower())
                for pattern in PRE_RELEASE_PATTERNS
            )
        )

        if not keywords_matched and version_jump != "major":
            return None

        signal_level = (
            "prewarning"
            if is_pre_release or (version_jump == "major" and not keywords_matched)
            else "early"
        )
        is_mandatory = bool(
            strong_keywords_matched
            or (
                "migration" in keywords_matched
                and not any(
                    context in search_text
                    for context in ["database migration", "schema migration"]
                )
            )
        )
        confidence = "high" if is_mandatory else "medium"
        if is_pre_release and confidence == "high":
            confidence = "medium"
        if not keywords_matched:
            confidence = "low"

        event_time = _extract_event_time_from_text(body)
        return {
            "event_key": f"{target['chain_id']}:{repo}:{tag}",
            "event_reference": tag,
            "source_type": "github_release",
            "stage": signal_level,
            "cause_type": "network_upgrade",
            "title": title,
            "summary": (body or "")[:1200],
            "confidence_hint": confidence,
            "network_event_time": event_time,
            "network_event_height": None,
            "evidence_links": [release.get("html_url", "")],
            "metadata": {
                "repo": repo,
                "tag": tag,
                "published_at": release.get("published_at", ""),
                "keywords_matched": keywords_matched,
                "strong_keywords_matched": strong_keywords_matched,
                "version_jump": version_jump,
                "is_pre_release": is_pre_release,
                "is_mandatory": is_mandatory,
                "rate_limit_remaining": self._rate_limit_remaining,
            },
        }
