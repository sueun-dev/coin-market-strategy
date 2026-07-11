# 01F. Deposit/Withdrawal Suspension Forecaster

`01` is now an upstream suspension forecaster, not a pure governance monitor.

It watches public upstream signals that often appear before Upbit or Bithumb publish deposit/withdrawal suspension notices.

Chain-by-chain best-source playbook:

- [CHAIN_APPROACH_PLAYBOOK.md](CHAIN_APPROACH_PLAYBOOK.md)

## Current sources

- GitHub releases for chain or node repositories
- Cosmos governance proposals that schedule software upgrades

## Current output

- predicted affected exchanges
- predicted affected tickers
- likely cause type
- estimated suspension window when the chain event time is known
- evidence links to the upstream source

## Run once

```bash
cd detection/01-suspension-forecaster
../../.venv/bin/python main.py
```

## Run continuously

```bash
cd detection/01-suspension-forecaster
../../.venv/bin/python main.py --loop
```

## Limit sources

```bash
../../.venv/bin/python main.py --source github
../../.venv/bin/python main.py --source governance
```

## GitHub auth

GitHub release polling uses `GITHUB_TOKEN` from environment or `.env` first. If that token is rejected, it retries with `gh auth token`; if no valid token is available, it falls back to unauthenticated public release requests and reports rate-limit/source failures instead of printing a false clean `No new suspension forecasts`.

## Telegram

- preferred env keys: `GOVERNANCE_TELEGRAM_BOT_TOKEN`, `GOVERNANCE_TELEGRAM_CHAT_ID`
- fallback env keys: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- test: `../../.venv/bin/python main.py --test-telegram`
