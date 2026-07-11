# 03. PEAQ Runtime Watch

Standalone PEAQ early-warning watcher.

이 폴더는 `01`과 분리된 별도 감시기다.
목적은 `PEAQ 체인 head stall`을 거래소 공지보다 먼저 잡는 것이다.
원칙은 `정량 신호만 사용`이다.

## What It Watches

- HTTP `latest`
- HTTP `finalized`
- quorum `head age`
- quorum `finalized age`
- quorum `finality gap`
- endpoint `divergence`
- quorum stall progression: `observe -> warning -> critical`
- recovery after consecutive healthy rounds

## What It Does Not Watch

- `X`
- `Discord`
- 거래소 공지
- 거래소 `assetsstatus`
- 텍스트 키워드
- 기타 언어 기반 분류

자동 텔레그램 경보는 `정량 조건 충족 시에만` 발생한다.

## Telegram

- preferred env keys: `PEAQ_TELEGRAM_BOT_TOKEN`, `PEAQ_TELEGRAM_CHAT_ID`
- fallback env keys: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- disable send: `--no-telegram`
- test: `../../.venv/bin/python main.py --test-telegram`

## Run Once

```bash
cd detection/03-peaq-runtime-watch
../../.venv/bin/python main.py --no-telegram
```

## Run Continuously

```bash
cd detection/03-peaq-runtime-watch
../../.venv/bin/python main.py --loop
```

## Run Soak

```bash
cd detection/03-peaq-runtime-watch
../../.venv/bin/python scripts/run_peaq_soak.py \
  --duration-seconds 10800 \
  --interval 5 \
  --reset \
  --output-jsonl data/soak/peaq_soak.jsonl \
  --summary-json data/soak/peaq_soak_summary.json
```

## Replay Halt Fixture

```bash
cd detection/03-peaq-runtime-watch
../../.venv/bin/python scripts/replay_runtime_snapshots.py \
  data/replay/peaq_1652398_halt_recovery.jsonl \
  --expect-stages warning critical recovery
```

현재 구현은 `warning`, `critical`, `recovery` 이벤트만 알림으로 보낸다. `observe` 단계는 상태에는 남지만 Telegram alert로 전송하지 않는다.

## Docs

- [PEAQ_EARLY_WARNING_PLAYBOOK.md](PEAQ_EARLY_WARNING_PLAYBOOK.md)
