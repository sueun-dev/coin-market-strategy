"""
Integration tests that hit the LIVE GitHub API.
Tests real repos: cosmos/gaia, anza-xyz/agave (Solana), MystenLabs/sui.

These tests require network access and consume GitHub API rate limit.
Run with: pytest tests/test_integration.py -v
Skip with: pytest -m "not integration"
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.github_client import GitHubClient
from src.release_filter import filter_releases


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    """Shared GitHub client for all integration tests."""
    c = GitHubClient()
    yield c
    c.close()


def _skip_if_rate_limited(client: GitHubClient):
    """Skip test if rate limit is too low."""
    if client.rate_limit_remaining is not None and client.rate_limit_remaining < 3:
        pytest.skip("GitHub API rate limit too low")


class TestCosmosGaia:
    """Test against cosmos/gaia (ATOM) - a well-known Cosmos SDK chain."""

    def test_fetch_releases(self, client):
        releases = client.get_releases("cosmos/gaia", per_page=5)
        _skip_if_rate_limited(client)
        assert isinstance(releases, list)
        assert len(releases) > 0, "cosmos/gaia should have releases"

    def test_release_structure(self, client):
        releases = client.get_releases("cosmos/gaia", per_page=1)
        _skip_if_rate_limited(client)
        if not releases:
            pytest.skip("No releases returned")
        release = releases[0]
        # Verify expected GitHub API fields exist
        assert "tag_name" in release
        assert "name" in release
        assert "body" in release
        assert "html_url" in release
        assert "published_at" in release
        assert "draft" in release
        assert "prerelease" in release

    def test_filter_finds_upgrades(self, client):
        releases = client.get_releases("cosmos/gaia", per_page=10)
        _skip_if_rate_limited(client)
        if not releases:
            pytest.skip("No releases returned")
        # cosmos/gaia frequently has upgrade-related releases
        filtered = filter_releases(releases)
        # We just verify filtering runs without error
        assert isinstance(filtered, list)
        # Each filtered result should have required keys
        for f in filtered:
            assert "tag" in f
            assert "keywords_matched" in f
            assert "is_breaking" in f
            assert "is_mandatory" in f
            assert "is_pre_release" in f
            assert "signal_level" in f
            assert "confidence" in f


class TestSolana:
    """Test against anza-xyz/agave (Solana validator client)."""

    def test_fetch_releases(self, client):
        releases = client.get_releases("anza-xyz/agave", per_page=5)
        _skip_if_rate_limited(client)
        assert isinstance(releases, list)
        assert len(releases) > 0, "anza-xyz/agave should have releases"

    def test_has_version_tags(self, client):
        releases = client.get_releases("anza-xyz/agave", per_page=5)
        _skip_if_rate_limited(client)
        if not releases:
            pytest.skip("No releases returned")
        # Solana releases should have version tags
        tags = [r.get("tag_name", "") for r in releases]
        assert any("v" in t or t[0].isdigit() for t in tags), f"Expected version tags, got: {tags}"


class TestSui:
    """Test against MystenLabs/sui (SUI)."""

    def test_fetch_releases(self, client):
        releases = client.get_releases("MystenLabs/sui", per_page=5)
        _skip_if_rate_limited(client)
        assert isinstance(releases, list)
        assert len(releases) > 0, "MystenLabs/sui should have releases"

    def test_filter_runs(self, client):
        releases = client.get_releases("MystenLabs/sui", per_page=10)
        _skip_if_rate_limited(client)
        if not releases:
            pytest.skip("No releases returned")
        filtered = filter_releases(releases)
        assert isinstance(filtered, list)


class TestNonExistentRepo:
    """Verify graceful handling of non-existent repos."""

    def test_nonexistent_repo_returns_empty(self, client):
        releases = client.get_releases("definitely-not-a-real-org/fake-repo-12345")
        assert releases == []

    def test_check_repo_exists_false(self, client):
        _skip_if_rate_limited(client)
        exists = client.check_repo_exists("definitely-not-a-real-org/fake-repo-12345")
        assert exists is False

    def test_check_repo_exists_true(self, client):
        _skip_if_rate_limited(client)
        exists = client.check_repo_exists("cosmos/gaia")
        assert exists is True


class TestRateLimitHandling:
    """Test that rate limit info is tracked properly."""

    def test_rate_limit_tracked(self, client):
        # After at least one request, rate limit should be tracked
        client.get_releases("cosmos/gaia", per_page=1)
        # rate_limit_remaining should be set (could be None if all requests failed)
        # Just verify it doesn't crash
        remaining = client.rate_limit_remaining
        if remaining is not None:
            assert isinstance(remaining, int)
            assert remaining >= 0
