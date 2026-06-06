# coin-market-strategy

**KR Exchange Deposit/Withdrawal Suspension — Delta-Neutral Premium Capture**
Early detection → closed-economy premium capture, organized as a research monorepo of numbered strategy modules.

> ⚠️ Research / personal project. This repository contains trading-strategy research and partially implemented monitoring tools. The exchange-listing-sniper module can place **real Bybit spot orders** when explicitly enabled. Use entirely at your own risk. Nothing here is financial advice.

---

## What this is

The repo is a numbered set of strategy modules grouped by stage of a single pipeline:

```
detection → filtering → classification → execution → monitoring → risk → infra
```

The underlying thesis: when a Korean exchange (Upbit / Bithumb) is about to suspend deposits/withdrawals for a coin (network upgrade, chain halt, hack, internal maintenance, etc.), that suspension can create a "closed economy" price premium. Detecting the trigger early and building a delta-neutral position (domestic spot long + overseas futures short) aims to capture that premium with limited directional risk.

Each module lives in its own directory with two documents:

- `README.md` — short summary of the module (English + Korean).
- `STRATEGY.md` — the detailed design / scoring rules / rationale.

**Important:** most modules are *design specifications only*. A handful are actually implemented in Python. See the status table below before assuming a module runs.

## Module status

| # | Module | Category | Status |
|---|--------|----------|--------|
| 01 | Governance Proposal Monitor (`detection/01-governance-monitor`) | detection | ✅ Implemented (Python, tests) |
| 02 | Exchange Listing Sniper (`detection/02-exchange-listing-sniper`) | detection | ✅ Implemented (Python + C++/Rust, tests) |
| 02 | GitHub Release Monitor (`detection/02-github-release-monitor`) | detection | ✅ Implemented (Python, tests) |
| 03 | Other-Exchange Announcement Monitor (`detection/03-exchange-announcement-monitor`) | detection | 📄 Design only |
| 04 | Block-Time Anomaly / Chain-Halt Detector (`detection/04-block-time-anomaly-detector`) | detection | ✅ Implemented (Python, tests) |
| 05 | Hot-Wallet Abnormal Withdrawal Detection (`detection/05-hot-wallet-abnormal-withdrawal`) | detection | 📄 Design only |
| 06 | Hot-to-Cold Wallet Transfer Detection (`detection/06-hot-to-cold-wallet-monitor`) | detection | 📄 Design only |
| 07 | Target Coin Auto-Filtering Engine (`filtering/07-target-coin-filter`) | filtering | 📄 Design only |
| 08 | Signal → Position Direction Engine (`classification/08-signal-direction-engine`) | classification | 📄 Design only |
| 09 | Delta-Neutral Position Builder (`execution/09-delta-neutral-position`) | execution | 📄 Design only |
| 10 | Proxy Hedge Mapper (`execution/10-proxy-hedge-mapper`) | execution | 📄 Design only |
| 11 | Exchange Selection Optimizer (`execution/11-exchange-selection-optimizer`) | execution | 📄 Design only |
| 12 | Premium Real-Time Tracker (`monitoring/12-premium-realtime-tracker`) | monitoring | 📄 Design only |
| 13 | Simultaneous Liquidation System (`monitoring/13-simultaneous-liquidation`) | monitoring | 📄 Design only |
| 14 | Hack Scenario Holding Strategy (`monitoring/14-hack-scenario-holding`) | monitoring | 📄 Design only |
| 15 | Short Liquidation Safety Margin (`risk/15-short-liquidation-safety`) | risk | 📄 Design only |
| 16 | Funding Rate Tracker (`risk/16-funding-rate-tracker`) | risk | 📄 Design only |
| 17 | Position Sizing (`risk/17-position-sizing`) | risk | 📄 Design only |
| 18 | Unified Notification System (`infra/18-notification-system`) | infra | ✅ Implemented (Python, tests) |
| 19 | Data Registry System (`infra/19-data-registry`) | infra | 📄 Design only |

✅ Implemented modules: **01, 02 (listing sniper), 02 (github release), 04, 18**.
📄 Everything else is a written specification (`README.md` + `STRATEGY.md`) with no code yet.

## ChainPulse — unified monitor

`run_monitor.py` ("ChainPulse") at the repo root is the convenience entry point that wires three of the implemented detection systems together and pushes alerts to Telegram:

- **Governance (Cosmos)** — module 01, 13 chains
- **Governance (multi-chain, non-Cosmos)** — module 01's multi-chain client, 8 chains
- **GitHub releases** — module 02 (github release monitor), 34 repos
- **Block-time / chain-halt** — module 04, 21 chains

(Chain/repo counts come from the config files under each module.)

### Usage

```bash
python3 run_monitor.py                 # single poll of all systems
python3 run_monitor.py --loop          # continuous monitoring loop
python3 run_monitor.py --gov-only      # governance + github + multi-chain only
python3 run_monitor.py --block-only    # block-time monitor only
python3 run_monitor.py --test          # send a test Telegram alert
python3 run_monitor.py --loop --gov-interval 600 --block-interval 10
```

ChainPulse reads Telegram credentials from a `.env` file at the repo root:

```ini
TELEGRAM_BOT_TOKEN=123456:abc...
TELEGRAM_CHAT_ID=-1001234567890
GITHUB_TOKEN=ghp_...            # optional, raises GitHub release-poll rate limits
```

If the Telegram variables are unset, polling still runs but alerts are skipped (a warning is logged).

## Requirements

- Python 3.10+ (the code uses `list[dict]` / `str | None` style annotations)
- Python packages used by the implemented modules:
  - `httpx`, `python-dotenv` — used everywhere (ChainPulse, governance, github, block-time, notifications)
  - `telethon`, `pyrogram` — only the exchange-listing-sniper real-time backends
  - `pytest` — running the test suites
- Optional native toolchains, only for the exchange-listing-sniper fast paths: a C++ compiler and/or Rust/Cargo (see that module's README).

There is no top-level dependency manifest. Install what you need directly, e.g.:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install httpx python-dotenv telethon pyrogram pytest
```

## Running an individual module

Each implemented module is self-contained and run from its own directory. Examples:

```bash
# Governance monitor (module 01)
cd detection/01-governance-monitor
python main.py --test-telegram          # test the standalone Telegram wiring
python main.py --loop                    # poll every 10 min
python main.py --chain cosmoshub         # one chain only

# GitHub release monitor (module 02)
cd detection/02-github-release-monitor
python main.py

# Block-time / chain-halt detector (module 04)
cd detection/04-block-time-anomaly-detector
python main.py

# Notification system (module 18)
cd infra/18-notification-system
python main.py
```

The exchange-listing-sniper (module 02) has many more modes (real-time backends, native classifiers, automated Bybit buying) and its own benchmark/deploy scripts — see
[`detection/02-exchange-listing-sniper/README.md`](detection/02-exchange-listing-sniper/README.md).

Many modules support their own Telegram env keys with a fallback to the root `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (for example governance uses `GOVERNANCE_TELEGRAM_BOT_TOKEN` first). Check each module's README for its specific keys.

## Tests

The implemented modules ship `pytest` suites under their `tests/` directories. Run them per module, for example:

```bash
cd detection/01-governance-monitor && python -m pytest
cd detection/02-github-release-monitor && python -m pytest
cd detection/04-block-time-anomaly-detector && python -m pytest
cd detection/02-exchange-listing-sniper && python -m pytest
cd infra/18-notification-system && python -m pytest
```

## Repository layout

```
.
├── run_monitor.py            # ChainPulse unified monitor (entry point)
├── detection/                # 01–06: early-detection signal sources
│   ├── 01-governance-monitor/            (implemented)
│   ├── 02-exchange-listing-sniper/       (implemented)
│   ├── 02-github-release-monitor/        (implemented)
│   ├── 03-exchange-announcement-monitor/ (design)
│   ├── 04-block-time-anomaly-detector/   (implemented)
│   ├── 05-hot-wallet-abnormal-withdrawal/ (design)
│   └── 06-hot-to-cold-wallet-monitor/    (design)
├── filtering/                # 07: target-coin scoring (design)
├── classification/           # 08: signal → position direction (design)
├── execution/                # 09–11: position building / hedging (design)
├── monitoring/               # 12–14: premium tracking & liquidation (design)
├── risk/                     # 15–17: safety, funding, sizing (design)
└── infra/                    # 18 notifications (implemented), 19 data registry (design)
```

Implemented modules generally follow the same internal shape: `main.py` CLI, a `src/` package, `config/*.json`, `tests/`, and a `data/` directory for runtime state (git-ignored).

## License

No license file is currently included. All rights reserved by the author unless a `LICENSE` is added.

---

# coin-market-strategy (한국어)

**국내 거래소 입출금 정지 — 델타 뉴트럴 프리미엄 캡처**
선행 감지 → 폐쇄 경제 프리미엄 캡처를 목표로, 번호가 매겨진 전략 모듈들을 모은 리서치 모노레포입니다.

> ⚠️ 개인 리서치 프로젝트입니다. 이 저장소는 트레이딩 전략 리서치와 일부만 구현된 모니터링 도구를 담고 있습니다. exchange-listing-sniper 모듈은 명시적으로 활성화하면 **실제 Bybit 현물 주문**을 넣을 수 있습니다. 모든 사용은 전적으로 본인 책임이며, 투자 조언이 아닙니다.

## 개요

핵심 아이디어: 업비트/빗썸이 어떤 코인의 입출금을 정지하려 할 때(네트워크 업그레이드, 체인 halt, 해킹, 내부 점검 등) 그 정지가 "폐쇄 경제" 프리미엄을 만들 수 있습니다. 트리거를 미리 감지하고 델타 뉴트럴 포지션(국내 현물 롱 + 해외 선물 숏)을 구성해 방향 리스크를 제한하면서 그 프리미엄을 캡처하는 것이 목표입니다.

각 모듈은 자체 디렉터리에 `README.md`(요약)와 `STRATEGY.md`(상세 설계)를 가집니다.

**중요:** 대부분의 모듈은 *설계 문서만* 있습니다. 실제로 Python으로 구현된 모듈은 위의 **Module status** 표에서 ✅로 표시된 **01, 02(listing sniper), 02(github release), 04, 18** 뿐입니다.

## ChainPulse 통합 모니터

저장소 루트의 `run_monitor.py`("ChainPulse")는 구현된 감지 시스템(거버넌스 Cosmos, 멀티체인 거버넌스, GitHub 릴리스, 블록타임/halt)을 묶어 텔레그램으로 알림을 보내는 진입점입니다.

```bash
python3 run_monitor.py            # 전체 시스템 1회 폴링
python3 run_monitor.py --loop     # 연속 모니터링
python3 run_monitor.py --test     # 텔레그램 테스트 알림
```

루트 `.env`에서 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`(선택: `GITHUB_TOKEN`)를 읽습니다. 미설정 시 폴링은 동작하되 알림은 건너뜁니다.

## 요구 사항 / 실행 / 테스트

- Python 3.10+
- 패키지: `httpx`, `python-dotenv`(공통), `telethon`/`pyrogram`(리스팅 스나이퍼 실시간 백엔드), `pytest`(테스트)
- 루트에 통합 의존성 매니페스트는 없습니다. 필요한 패키지를 직접 설치하세요.

구현된 모듈은 각자 디렉터리에서 `python main.py ...`로 실행하고, `tests/` 아래 pytest 스위트를 `python -m pytest`로 돌립니다. 자세한 사용법은 각 모듈의 README를 참고하세요(특히 [exchange-listing-sniper](detection/02-exchange-listing-sniper/README.md)).

## 라이선스

현재 라이선스 파일이 없습니다. `LICENSE`가 추가되기 전까지 모든 권리는 작성자에게 있습니다.
