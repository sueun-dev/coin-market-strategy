"""
Release filter for detecting blockchain upgrade/hardfork releases.
Filters GitHub releases by keywords, semantic version changes, and pre-release markers.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Keywords that indicate a release will cause exchange deposit/withdrawal suspension
UPGRADE_KEYWORDS = [
    "upgrade",
    "hardfork",
    "hard fork",
    "hard-fork",
    "migration",
    "breaking change",
    "consensus",
    "network upgrade",
    "mandatory update",
    "node update",
    "chain halt",
    "chain upgrade",
    "mainnet upgrade",
    "state migration",
    "genesis restart",
]

STRONG_UPGRADE_KEYWORDS = {
    "hardfork",
    "hard fork",
    "hard-fork",
    "breaking change",
    "consensus",
    "network upgrade",
    "mandatory update",
    "chain halt",
    "chain upgrade",
    "mainnet upgrade",
    "state migration",
    "genesis restart",
}

WEAK_UPGRADE_KEYWORDS = {
    "upgrade",
    "migration",
    "node update",
}

ACTIONABLE_CONTEXT_RE = re.compile(
    r"\b("
    r"chain|mainnet|network|protocol|consensus|runtime|validator|validators|"
    r"node operator|node operators|hardfork|hard fork|governance|genesis|"
    r"state migration|software upgrade|halt height|upgrade height"
    r")\b",
    re.IGNORECASE,
)

FALSE_POSITIVE_CONTEXT_RE = re.compile(
    r"\b("
    r"dependenc(?:y|ies)|deps|package|packages|library|libraries|"
    r"ci|docs?|readme|changelog|docker|helm|chart|charts|"
    r"database migration|schema migration|sql migration|test(?:s|ing)?"
    r")\b",
    re.IGNORECASE,
)

# Pre-release tag indicators
PRE_RELEASE_PATTERNS = ["rc", "alpha", "beta", "preview", "dev"]

# Semantic version regex: captures major, minor, patch
SEMVER_RE = re.compile(
    r"v?(\d+)\.(\d+)\.(\d+)(?:[-.]?(rc|alpha|beta|preview|dev)[\d.]*)?",
    re.IGNORECASE,
)


def parse_semver(tag: str) -> tuple[int, int, int, str | None] | None:
    """Parse a semantic version tag. Returns (major, minor, patch, pre) or None."""
    m = SEMVER_RE.search(tag)
    if not m:
        return None
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre = m.group(4).lower() if m.group(4) else None
    return (major, minor, patch, pre)


def is_pre_release_tag(tag: str) -> bool:
    """Check if a tag contains pre-release markers (rc, alpha, beta, etc.)."""
    tag_lower = tag.lower()
    for pattern in PRE_RELEASE_PATTERNS:
        # Match patterns like -rc1, -rc.1, -alpha, .beta2
        if re.search(rf"[-.]?{pattern}\d*", tag_lower):
            return True
    return False


def detect_version_jump(
    current_tag: str, previous_tags: list[str]
) -> dict | None:
    """Detect major/minor version jumps compared to previous releases.

    Returns dict with jump info or None if no significant jump.
    """
    current = parse_semver(current_tag)
    if not current:
        return None

    cur_major, cur_minor, cur_patch, cur_pre = current

    for prev_tag in previous_tags:
        prev = parse_semver(prev_tag)
        if not prev:
            continue
        prev_major, prev_minor, prev_patch, prev_pre = prev

        # Skip comparing with same version or pre-releases of same version
        if (cur_major, cur_minor, cur_patch) == (prev_major, prev_minor, prev_patch):
            continue

        if cur_major > prev_major:
            return {
                "type": "major",
                "from": prev_tag,
                "to": current_tag,
                "description": f"Major version change: {prev_tag} -> {current_tag}",
            }
        if cur_major == prev_major and cur_minor > prev_minor:
            return {
                "type": "minor",
                "from": prev_tag,
                "to": current_tag,
                "description": f"Minor version change: {prev_tag} -> {current_tag}",
            }

        # Found a meaningful comparison, stop
        break

    return None


def _has_false_positive_context(search_text: str) -> bool:
    """Return True for maintenance releases that only sound like upgrades."""
    return bool(FALSE_POSITIVE_CONTEXT_RE.search(search_text))


def _has_actionable_upgrade_context(search_text: str) -> bool:
    """Return True when weak words are tied to chain/runtime upgrade context."""
    return bool(ACTIONABLE_CONTEXT_RE.search(search_text))


def filter_release(release: dict, previous_tags: list[str] | None = None) -> dict | None:
    """Filter a single release for upgrade/hardfork relevance.

    Args:
        release: GitHub release dict from API
        previous_tags: List of tag names from older releases (for version comparison)

    Returns:
        Structured signal dict if relevant, None otherwise.
    """
    tag = release.get("tag_name", "")
    title = release.get("name", "") or ""
    body = release.get("body", "") or ""
    is_draft = release.get("draft", False)
    is_github_prerelease = release.get("prerelease", False)

    # Skip drafts entirely
    if is_draft:
        return None

    # Combine text for keyword search
    search_text = f"{tag} {title} {body}".lower()

    # Find matching keywords
    keywords_matched = []
    for kw in UPGRADE_KEYWORDS:
        if kw in search_text:
            keywords_matched.append(kw)

    # Check for version jump
    version_jump = None
    if previous_tags:
        version_jump = detect_version_jump(tag, previous_tags)

    # Check pre-release status
    is_pre = is_pre_release_tag(tag) or is_github_prerelease

    strong_keywords = [kw for kw in keywords_matched if kw in STRONG_UPGRADE_KEYWORDS]
    weak_keywords = [kw for kw in keywords_matched if kw in WEAK_UPGRADE_KEYWORDS]
    has_false_positive_context = _has_false_positive_context(search_text)
    has_actionable_context = _has_actionable_upgrade_context(search_text)
    major_jump_only = (
        version_jump is not None
        and version_jump["type"] == "major"
        and not strong_keywords
        and not (weak_keywords and has_actionable_context and not has_false_positive_context)
    )
    minor_jump_only = (
        version_jump is not None
        and version_jump["type"] == "minor"
        and not strong_keywords
        and not (weak_keywords and has_actionable_context and not has_false_positive_context)
    )

    # Weak words like "upgrade" and "migration" are common in dependency,
    # database, docs, and CI releases. Emit only when tied to chain/runtime
    # context, or when a major version jump deserves a low-priority warning.
    if not strong_keywords:
        weak_contextual = weak_keywords and has_actionable_context and not has_false_positive_context
        if not weak_contextual and not major_jump_only:
            return None
    if minor_jump_only:
        return None

    # Determine if this is a breaking/mandatory change
    is_breaking = any(
        kw in strong_keywords
        for kw in [
            "hardfork", "hard fork", "hard-fork",
            "breaking change", "consensus", "chain halt",
        ]
    )
    is_mandatory = (
        is_breaking
        or "mandatory update" in keywords_matched
        or "mandatory" in search_text
        or ("network upgrade" in keywords_matched and "validator" in search_text)
    )

    # Only emit if there's something interesting
    has_keywords = bool(strong_keywords or weak_keywords)
    has_version_jump = version_jump is not None

    if not has_keywords and not has_version_jump:
        return None

    # Determine confidence
    if is_breaking and not is_pre:
        confidence = "high"
    elif strong_keywords and has_version_jump:
        confidence = "high"
    elif strong_keywords:
        confidence = "medium"
    elif weak_keywords and has_actionable_context:
        confidence = "medium"
    elif major_jump_only:
        confidence = "low"
    else:
        confidence = "low"

    # Lower confidence for pre-releases
    if is_pre and confidence == "high":
        confidence = "medium"

    signal_level = "pre-warning" if is_pre or major_jump_only else "alert"

    return {
        "tag": tag,
        "title": title,
        "url": release.get("html_url", ""),
        "published_at": release.get("published_at", ""),
        "keywords_matched": keywords_matched,
        "is_breaking": is_breaking,
        "is_mandatory": is_mandatory,
        "is_pre_release": is_pre,
        "version_jump": version_jump,
        "confidence": confidence,
        "signal_level": signal_level,
    }


def filter_releases(releases: list[dict]) -> list[dict]:
    """Filter a list of releases, returning only relevant ones.

    Args:
        releases: List of GitHub release dicts (newest first)

    Returns:
        List of structured signal dicts for relevant releases.
    """
    if not releases:
        return []

    # Extract tags for version comparison (skip first since that's what we compare against)
    all_tags = [r.get("tag_name", "") for r in releases]

    results = []
    for i, release in enumerate(releases):
        previous_tags = all_tags[i + 1:] if i + 1 < len(releases) else []
        result = filter_release(release, previous_tags)
        if result:
            results.append(result)

    return results
