from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".codeatlas",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "vendor",
}
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXTERNAL_RE = re.compile(r"^(?:https?://|mailto:|#)")


def test_local_markdown_links_resolve():
    missing: list[str] = []
    for md_path in sorted(ROOT.rglob("*.md")):
        if any(part in SKIP_PARTS for part in md_path.relative_to(ROOT).parts):
            continue
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        for match in LINK_RE.finditer(text):
            target = match.group(1).split("#", 1)[0].strip()
            if not target or EXTERNAL_RE.match(target):
                continue
            if Path(target).is_absolute():
                missing.append(
                    f"{md_path.relative_to(ROOT)} -> {target} (non-portable absolute path)"
                )
                continue
            target_path = (md_path.parent / target).resolve()
            if not target_path.exists():
                missing.append(f"{md_path.relative_to(ROOT)} -> {target}")

    assert missing == []
