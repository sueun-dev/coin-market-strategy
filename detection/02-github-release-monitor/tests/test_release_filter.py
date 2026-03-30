"""
Unit tests for the release filter module.
Tests keyword matching, semantic version detection, and pre-release handling.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.release_filter import (
    filter_release,
    filter_releases,
    parse_semver,
    is_pre_release_tag,
    detect_version_jump,
)


# --- parse_semver ---

class TestParseSemver:
    def test_standard_version(self):
        assert parse_semver("v1.2.3") == (1, 2, 3, None)

    def test_no_v_prefix(self):
        assert parse_semver("1.2.3") == (1, 2, 3, None)

    def test_rc_version(self):
        result = parse_semver("v2.0.0-rc1")
        assert result == (2, 0, 0, "rc")

    def test_alpha_version(self):
        result = parse_semver("v3.1.0-alpha2")
        assert result == (3, 1, 0, "alpha")

    def test_beta_version(self):
        result = parse_semver("v1.0.0-beta")
        assert result == (1, 0, 0, "beta")

    def test_non_semver(self):
        assert parse_semver("release-2024") is None

    def test_complex_tag(self):
        # Should still extract the version
        result = parse_semver("chain-v15.2.0")
        assert result == (15, 2, 0, None)


# --- is_pre_release_tag ---

class TestPreReleaseTag:
    def test_rc_tag(self):
        assert is_pre_release_tag("v2.0.0-rc1") is True

    def test_alpha_tag(self):
        assert is_pre_release_tag("v1.0.0-alpha") is True

    def test_beta_tag(self):
        assert is_pre_release_tag("v1.0.0-beta2") is True

    def test_preview_tag(self):
        assert is_pre_release_tag("v1.0.0-preview.1") is True

    def test_stable_tag(self):
        assert is_pre_release_tag("v1.2.3") is False

    def test_dev_tag(self):
        assert is_pre_release_tag("v1.0.0-dev3") is True


# --- detect_version_jump ---

class TestDetectVersionJump:
    def test_major_jump(self):
        result = detect_version_jump("v2.0.0", ["v1.5.3", "v1.5.2"])
        assert result is not None
        assert result["type"] == "major"

    def test_minor_jump(self):
        result = detect_version_jump("v1.6.0", ["v1.5.3", "v1.5.2"])
        assert result is not None
        assert result["type"] == "minor"

    def test_patch_only(self):
        result = detect_version_jump("v1.5.4", ["v1.5.3"])
        assert result is None

    def test_no_previous(self):
        result = detect_version_jump("v1.0.0", [])
        assert result is None

    def test_non_semver_previous(self):
        result = detect_version_jump("v2.0.0", ["release-2024"])
        assert result is None

    def test_same_version(self):
        result = detect_version_jump("v1.5.3", ["v1.5.3"])
        assert result is None


# --- filter_release ---

class TestFilterRelease:
    def _make_release(self, tag="v1.0.0", name="", body="", draft=False, prerelease=False):
        return {
            "tag_name": tag,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
            "html_url": f"https://github.com/test/repo/releases/tag/{tag}",
            "published_at": "2026-03-28T12:00:00Z",
        }

    def test_hardfork_keyword(self):
        release = self._make_release(
            tag="v2.0.0",
            name="Athena Hard Fork",
            body="This release implements the Athena hard fork upgrade.",
        )
        result = filter_release(release, ["v1.5.0"])
        assert result is not None
        assert "hard fork" in result["keywords_matched"]
        assert "upgrade" in result["keywords_matched"]
        assert result["is_breaking"] is True
        assert result["is_mandatory"] is True

    def test_network_upgrade_keyword(self):
        release = self._make_release(
            tag="v15.0.0",
            name="Network Upgrade v15",
            body="Mandatory network upgrade. All validators must update.",
        )
        result = filter_release(release, ["v14.2.0"])
        assert result is not None
        assert "network upgrade" in result["keywords_matched"]
        assert "upgrade" in result["keywords_matched"]
        assert result["is_mandatory"] is True

    def test_consensus_change(self):
        release = self._make_release(
            tag="v3.0.0",
            name="Consensus Protocol Update",
            body="New consensus mechanism deployed.",
        )
        result = filter_release(release, ["v2.1.0"])
        assert result is not None
        assert "consensus" in result["keywords_matched"]
        assert result["is_breaking"] is True

    def test_no_keywords_no_version_jump(self):
        release = self._make_release(
            tag="v1.5.4",
            name="Bug fix release",
            body="Fixed minor bug in logging.",
        )
        result = filter_release(release, ["v1.5.3"])
        assert result is None

    def test_draft_ignored(self):
        release = self._make_release(
            tag="v2.0.0",
            name="Hard Fork Release",
            body="Breaking change",
            draft=True,
        )
        result = filter_release(release)
        assert result is None

    def test_rc_pre_release(self):
        release = self._make_release(
            tag="v2.0.0-rc1",
            name="v2.0.0 Release Candidate 1",
            body="Network upgrade preparation",
        )
        result = filter_release(release, ["v1.9.0"])
        assert result is not None
        assert result["is_pre_release"] is True
        assert result["signal_level"] == "pre-warning"

    def test_github_prerelease_flag(self):
        release = self._make_release(
            tag="v2.0.0",
            name="Upgrade Release",
            body="Network upgrade",
            prerelease=True,
        )
        result = filter_release(release, ["v1.9.0"])
        assert result is not None
        assert result["is_pre_release"] is True
        assert result["signal_level"] == "pre-warning"

    def test_version_jump_only(self):
        """Major version jump alone should trigger even without keywords."""
        release = self._make_release(
            tag="v3.0.0",
            name="v3.0.0",
            body="New major release.",
        )
        result = filter_release(release, ["v2.8.1"])
        assert result is not None
        assert result["version_jump"]["type"] == "major"

    def test_migration_keyword(self):
        release = self._make_release(
            tag="v1.1.0",
            name="State Migration",
            body="Includes state migration for database upgrade.",
        )
        result = filter_release(release, ["v1.0.0"])
        assert result is not None
        assert "migration" in result["keywords_matched"]

    def test_mandatory_update_keyword(self):
        release = self._make_release(
            tag="v5.0.0",
            name="Mandatory Update Required",
            body="This is a mandatory update. All node operators must update before block 1000000.",
        )
        result = filter_release(release, ["v4.2.0"])
        assert result is not None
        assert "mandatory update" in result["keywords_matched"]
        assert result["is_mandatory"] is True

    def test_node_update_keyword(self):
        release = self._make_release(
            tag="v5.0.0",
            name="Node Update v5",
            body="All node operators must apply this node update.",
        )
        result = filter_release(release, ["v4.2.0"])
        assert result is not None
        assert "node update" in result["keywords_matched"]


# --- filter_releases ---

class TestFilterReleases:
    def test_empty_list(self):
        assert filter_releases([]) == []

    def test_multiple_releases(self):
        releases = [
            {
                "tag_name": "v2.0.0",
                "name": "Hard Fork Release",
                "body": "Network upgrade with consensus changes",
                "draft": False,
                "prerelease": False,
                "html_url": "https://github.com/test/repo/releases/tag/v2.0.0",
                "published_at": "2026-03-28T12:00:00Z",
            },
            {
                "tag_name": "v1.9.1",
                "name": "Bug fix",
                "body": "Minor patch",
                "draft": False,
                "prerelease": False,
                "html_url": "https://github.com/test/repo/releases/tag/v1.9.1",
                "published_at": "2026-03-20T12:00:00Z",
            },
            {
                "tag_name": "v1.9.0",
                "name": "Feature release",
                "body": "New features added",
                "draft": False,
                "prerelease": False,
                "html_url": "https://github.com/test/repo/releases/tag/v1.9.0",
                "published_at": "2026-03-10T12:00:00Z",
            },
        ]
        results = filter_releases(releases)
        # Only v2.0.0 should match (hard fork keyword + major version jump)
        assert len(results) >= 1
        assert results[0]["tag"] == "v2.0.0"

    def test_all_irrelevant(self):
        releases = [
            {
                "tag_name": "v1.0.1",
                "name": "Patch",
                "body": "Fixed typo",
                "draft": False,
                "prerelease": False,
                "html_url": "",
                "published_at": "2026-03-28T12:00:00Z",
            },
            {
                "tag_name": "v1.0.0",
                "name": "Initial Release",
                "body": "First release",
                "draft": False,
                "prerelease": False,
                "html_url": "",
                "published_at": "2026-03-20T12:00:00Z",
            },
        ]
        results = filter_releases(releases)
        assert len(results) == 0


# --- Confidence levels ---

class TestConfidence:
    def _make_release(self, tag="v1.0.0", name="", body="", prerelease=False):
        return {
            "tag_name": tag,
            "name": name,
            "body": body,
            "draft": False,
            "prerelease": prerelease,
            "html_url": "",
            "published_at": "2026-03-28T12:00:00Z",
        }

    def test_high_confidence_breaking(self):
        release = self._make_release(
            tag="v2.0.0",
            name="Hard Fork",
            body="Consensus breaking change",
        )
        result = filter_release(release, ["v1.0.0"])
        assert result is not None
        assert result["confidence"] == "high"

    def test_medium_confidence_prerelease(self):
        release = self._make_release(
            tag="v2.0.0-rc1",
            name="Hard Fork RC",
            body="Consensus breaking change",
            prerelease=True,
        )
        result = filter_release(release, ["v1.0.0"])
        assert result is not None
        assert result["confidence"] == "medium"
