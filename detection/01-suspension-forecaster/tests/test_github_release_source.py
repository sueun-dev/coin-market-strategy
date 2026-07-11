"""GitHub release source tests."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.github_release_source as github_release_source
from src.github_release_source import GitHubReleaseSource, GitHubReleaseSourceError


class FakeResponse:
    def __init__(self, status_code, text="", payload=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload if payload is not None else []
        self.headers = {"x-ratelimit-remaining": "59"}

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {"Authorization": "Bearer bad"}

    def get(self, *args, **kwargs):
        return self.responses.pop(0)

    def close(self):
        return None


def test_release_to_event_detects_upgrade_release():
    source = GitHubReleaseSource(token="test")
    target = {
        "chain_id": "injective",
        "chain_name": "Injective",
        "primary_ticker": "INJ",
    }
    release = {
        "tag_name": "v1.18.3-1774990852",
        "name": "v1.18.3",
        "body": "Injective v1.18.3 Mainnet Upgrade. Mandatory validator upgrade.",
        "draft": False,
        "prerelease": False,
        "html_url": "https://github.com/InjectiveFoundation/injective-core/releases/tag/v1.18.3-1774990852",
        "published_at": "2026-04-03T00:00:00Z",
    }
    event = source._release_to_event(
        target, "InjectiveFoundation/injective-core", release, ["v1.18.2"]
    )
    source.close()
    assert event is not None
    assert event["source_type"] == "github_release"
    assert event["metadata"]["repo"] == "InjectiveFoundation/injective-core"
    assert event["metadata"]["tag"] == "v1.18.3-1774990852"


def test_release_to_event_skips_testnet_release():
    source = GitHubReleaseSource(token="test")
    target = {"chain_id": "story", "chain_name": "Story", "primary_ticker": "IP"}
    release = {
        "tag_name": "v1.6.2",
        "name": "Story v1.6.2 (Aeneid Testnet ONLY)",
        "body": "Testnet validator release",
        "draft": False,
        "prerelease": False,
        "html_url": "https://example.com",
        "published_at": "2026-04-03T00:00:00Z",
    }
    event = source._release_to_event(target, "piplabs/story", release, ["v1.6.1"])
    source.close()
    assert event is None


@pytest.mark.parametrize(
    ("tag", "previous_tag"),
    [("v1.4.1", "v1.4.0"), ("v1.5.0", "v1.4.9")],
)
def test_release_to_event_skips_version_only_patch_and_minor_releases(
    tag, previous_tag
):
    source = GitHubReleaseSource(token="test")
    target = {"chain_id": "chain", "chain_name": "Chain", "primary_ticker": "CHN"}
    release = {
        "tag_name": tag,
        "name": tag,
        "body": "Routine maintenance release.",
        "draft": False,
        "prerelease": False,
        "html_url": "https://example.com",
        "published_at": "2026-04-03T00:00:00Z",
    }

    event = source._release_to_event(target, "example/chain", release, [previous_tag])
    source.close()

    assert event is None


def test_release_to_event_skips_dependency_upgrade_noise():
    source = GitHubReleaseSource(token="test")
    target = {"chain_id": "chain", "chain_name": "Chain", "primary_ticker": "CHN"}
    release = {
        "tag_name": "v1.4.1",
        "name": "Dependency upgrade",
        "body": "Package update and CI maintenance only.",
        "draft": False,
        "prerelease": False,
        "html_url": "https://example.com",
        "published_at": "2026-04-03T00:00:00Z",
    }

    event = source._release_to_event(target, "example/chain", release, ["v1.4.0"])
    source.close()

    assert event is None


def test_release_to_event_keeps_major_version_only_as_low_confidence_prewarning():
    source = GitHubReleaseSource(token="test")
    target = {"chain_id": "chain", "chain_name": "Chain", "primary_ticker": "CHN"}
    release = {
        "tag_name": "v2.0.0",
        "name": "v2.0.0",
        "body": "Release notes forthcoming.",
        "draft": False,
        "prerelease": False,
        "html_url": "https://example.com",
        "published_at": "2026-04-03T00:00:00Z",
    }

    event = source._release_to_event(target, "example/chain", release, ["v1.9.9"])
    source.close()

    assert event is not None
    assert event["stage"] == "prewarning"
    assert event["confidence_hint"] == "low"


def test_get_releases_retries_without_bad_token_for_public_repo():
    source = GitHubReleaseSource(token="bad", gh_token_loader=lambda: None)
    source._client = FakeClient(
        [
            FakeResponse(401, '{"message":"Bad credentials"}'),
            FakeResponse(200, payload=[]),
        ]
    )

    assert source._get_releases("cosmos/gaia") == []
    assert source.token is None
    assert "Authorization" not in source._client.headers

    source.close()


def test_init_uses_gh_token_when_no_env_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(github_release_source, "ENV_FILES", [])

    source = GitHubReleaseSource(gh_token_loader=lambda: "gh-good")

    try:
        assert source.token == "gh-good"
        assert source._client.headers["Authorization"] == "Bearer gh-good"
    finally:
        source.close()


def test_get_releases_uses_gh_token_before_unauthenticated_retry():
    source = GitHubReleaseSource(token="bad", gh_token_loader=lambda: "gh-good")
    source._client = FakeClient(
        [
            FakeResponse(401, '{"message":"Bad credentials"}'),
            FakeResponse(200, payload=[]),
        ]
    )

    assert source._get_releases("cosmos/gaia") == []
    assert source.token == "gh-good"
    assert source._client.headers["Authorization"] == "Bearer gh-good"

    source.close()


def test_get_releases_raises_when_unauthenticated_retry_fails():
    source = GitHubReleaseSource(token="bad", gh_token_loader=lambda: None)
    source._client = FakeClient(
        [
            FakeResponse(401, '{"message":"Bad credentials"}'),
            FakeResponse(403, '{"message":"API rate limit exceeded"}'),
        ]
    )

    with pytest.raises(GitHubReleaseSourceError, match="HTTP 403"):
        source._get_releases("cosmos/gaia")

    source.close()
