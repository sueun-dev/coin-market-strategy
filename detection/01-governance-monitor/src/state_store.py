from __future__ import annotations

"""
감지한 프로포절 상태 저장소. 중복 시그널 방지 + 상태 변화 추적.
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path(__file__).parent.parent / "data" / "detected_proposals.json"


class StateStore:
    """감지된 프로포절 상태를 JSON 파일로 관리."""

    def __init__(self, state_file: Path | str = DEFAULT_STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("상태 파일 로드 실패, 초기화: %s", e)
        return {}

    def _save(self):
        tmp = self.state_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    def _key(self, chain_id: str, proposal_id: str) -> str:
        return f"{chain_id}_{proposal_id}"

    def is_new_signal(self, chain_id: str, proposal_id: str, status: str) -> bool:
        """새로운 시그널인지 판단.

        - 완전히 새로운 프로포절 → True
        - 기존 프로포절이지만 상태 변경 (VOTING → PASSED) → True
        - 이미 같은 상태로 기록됨 → False
        """
        key = self._key(chain_id, proposal_id)
        existing = self._state.get(key)

        if existing is None:
            return True

        if existing.get("last_status") != status:
            return True

        return False

    def mark_detected(
        self,
        chain_id: str,
        proposal_id: str,
        status: str,
        signal_data: dict | None = None,
    ):
        """프로포절을 감지 완료로 기록."""
        key = self._key(chain_id, proposal_id)
        now = datetime.now(timezone.utc).isoformat()

        existing = self._state.get(key, {})
        history = existing.get("status_history", [])
        history.append({"status": status, "time": now})
        # 히스토리 무한 증가 방지
        if len(history) > 50:
            history = history[-50:]

        self._state[key] = {
            "chain_id": chain_id,
            "proposal_id": proposal_id,
            "first_detected": existing.get("first_detected", now),
            "last_updated": now,
            "last_status": status,
            "status_history": history,
            "signal_data": signal_data,
        }
        self._save()
        logger.info(
            "상태 기록: %s 프로포절 #%s [%s]", chain_id, proposal_id, status
        )

    def get_all(self) -> dict:
        return self._state.copy()

    def get(self, chain_id: str, proposal_id: str) -> dict | None:
        return self._state.get(self._key(chain_id, proposal_id))

    def clear(self):
        """전체 상태 초기화 (테스트용)."""
        self._state = {}
        self._save()
