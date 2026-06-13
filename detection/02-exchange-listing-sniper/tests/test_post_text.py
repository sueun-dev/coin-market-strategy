"""Telegram source text normalization tests."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.channel_client import TelegramChannelClient
from src.post_text import clean_telegram_html_text, extract_title, has_nonspace
from src.telegram_realtime_client import RealtimeTelegramChannelClient


def test_extract_title_returns_first_nonempty_line():
    text = "\n\n  [마켓 추가] 밈코어(M) 원화 마켓 추가  \n본문 두 번째 줄"

    assert extract_title(text) == "[마켓 추가] 밈코어(M) 원화 마켓 추가"
    assert RealtimeTelegramChannelClient.extract_title(text) == (
        "[마켓 추가] 밈코어(M) 원화 마켓 추가"
    )


def test_clean_telegram_html_text_preserves_visible_text():
    raw_html = (
        '<a href="https://example.test">[거래] 바빌론(BABY)</a>'
        '<br class="x"/>'
        '<mark class="highlight">KRW</mark> 마켓 디지털 자산 추가'
        '<br>수수료 &amp; 거래 안내'
    )

    text = clean_telegram_html_text(raw_html)

    assert text == (
        "[거래] 바빌론(BABY)\n"
        "KRW 마켓 디지털 자산 추가\n"
        "수수료 & 거래 안내"
    )


def test_has_nonspace_matches_realtime_wrapper():
    assert has_nonspace(" \n\t") is False
    assert has_nonspace(" \n[거래]") is True
    assert RealtimeTelegramChannelClient.has_nonspace(" \n\t") is False
    assert RealtimeTelegramChannelClient.has_nonspace(" \n[거래]") is True


def test_public_channel_html_parser_uses_cleaned_first_line_as_title():
    raw_html = """
    <div class="tgme_widget_message" data-post="BithumbExchange/12345">
      <div class="tgme_widget_message_text js-message_text" dir="auto">
        <a href="/s/BithumbExchange">[마켓 추가] 밈코어(M) 원화 마켓 추가</a><br/>
        자세한 내용은 공지 링크를 확인하세요.
      </div>
      <time datetime="2026-06-11T13:00:00+00:00" class="time">13:00</time>
    </div>
    """

    posts = TelegramChannelClient()._parse_posts(raw_html, "BithumbExchange")

    assert posts == [
        {
            "channel_handle": "BithumbExchange",
            "message_id": 12345,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 밈코어(M) 원화 마켓 추가",
            "text": (
                "[마켓 추가] 밈코어(M) 원화 마켓 추가\n"
                "자세한 내용은 공지 링크를 확인하세요."
            ),
            "post_url": "https://t.me/BithumbExchange/12345",
        }
    ]


def test_realtime_build_post_uses_same_title_extraction():
    post = RealtimeTelegramChannelClient.build_post(
        channel_handle="upbit_news",
        message_id=1389,
        text="\n[거래] 바빌론(BABY) KRW 마켓 디지털 자산 추가\n본문",
        published_at=datetime(2026, 6, 11, 13, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 6, 11, 13, 0, 1, tzinfo=timezone.utc),
        received_monotonic_ns=123,
    )

    assert post["title"] == "[거래] 바빌론(BABY) KRW 마켓 디지털 자산 추가"
    assert post["text"] == "[거래] 바빌론(BABY) KRW 마켓 디지털 자산 추가\n본문"
