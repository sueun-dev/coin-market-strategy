"""Replay fixture tests."""

from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from peaq_watch.monitor import load_config
from peaq_watch.replay import build_snapshot_provider, load_snapshots
from peaq_watch.runtime_head_source import RuntimeHeadSource
from peaq_watch.state_store import StateStore


def test_replay_fixture_emits_warning_critical_recovery():
    fixture = (
        Path(__file__).parent.parent
        / "data"
        / "replay"
        / "peaq_1652398_halt_recovery.jsonl"
    )
    snapshots = load_snapshots(fixture)
    provider = build_snapshot_provider(snapshots)
    target = load_config()["target"]

    emitted = []
    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(state_file=Path(tmpdir) / "state.json")
        source = RuntimeHeadSource(state_store=store, snapshot_provider=provider)
        try:
            for _ in snapshots:
                events = source.collect(target)
                emitted.extend(event["stage"] for event in events)
        finally:
            source.close()

    assert emitted == ["warning", "critical", "recovery"]
