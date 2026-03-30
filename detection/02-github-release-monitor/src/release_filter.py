"""
Release filter for detecting blockchain upgrade/hardfork releases.
Filters GitHub releases by keywords, semantic version changes, and pre-release markers.
"""

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

    # Determine if this is a breaking/mandatory change
    is_breaking = any(
        kw in keywords_matched
        for kw in [
            "hardfork", "hard fork", "hard-fork",
            "breaking change", "consensus", "chain halt",
        ]
    )
    is_mandatory = (
        is_breaking
        or "mandatory update" in keywords_matched
        or "mandatory" in search_text
        or (version_jump is not None and version_jump["type"] == "major")
    )

    # Only emit if there's something interesting
    has_keywords = len(keywords_matched) > 0
    has_version_jump = version_jump is not None

    if not has_keywords and not has_version_jump:
        return None

    # Determine confidence
    if is_breaking and not is_pre:
        confidence = "high"
    elif has_keywords and has_version_jump:
        confidence = "high"
    elif has_keywords:
        confidence = "medium"
    elif has_version_jump:
        confidence = "medium"
    else:
        confidence = "low"

    # Lower confidence for pre-releases
    if is_pre and confidence == "high":
        confidence = "medium"

    signal_level = "pre-warning" if is_pre else "alert"

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
