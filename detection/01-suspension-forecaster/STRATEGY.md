# 01. Deposit/Withdrawal Suspension Forecaster Strategy

## Goal

Forecast exchange deposit/withdrawal suspension notices before Upbit or Bithumb publish them.

## Why this exists

The old `01` focused too narrowly on governance status changes.
That missed cases like Injective, where the exchange could already act from earlier public upstream sources such as:

1. GitHub releases
2. validator upgrade notes
3. on-chain upgrade proposals

The rebuilt `01` starts from the actual question that matters:

`What public upstream event is likely to make a Korean exchange suspend deposits and withdrawals soon?`

## What 01 watches now

1. GitHub releases that imply validator, node, consensus, or mandatory upgrades
2. Cosmos governance proposals that include a software upgrade plan and target height

## What 01 outputs

Each signal tries to answer:

1. which chain is affected
2. which listed Korean exchanges are likely to suspend
3. which tickers are likely to be affected
4. why the suspension is likely
5. when the suspension is likely to begin relative to the chain event
6. which upstream evidence supports the forecast

## Signal definition

```json
{
  "signal_type": "suspension_forecast",
  "chain_id": "injective",
  "ticker": "INJ",
  "affected_tickers": ["INJ"],
  "listed_on": ["upbit", "bithumb"],
  "source_type": "governance",
  "source_stage": "governance_voting",
  "cause_type": "network_upgrade",
  "network_event_time": "2026-04-07T15:00:00+00:00",
  "forecast_actions": [
    {
      "exchange": "upbit",
      "action": "deposit_withdrawal_suspend",
      "likelihood": "high",
      "expected_pause_start": "2026-04-06T15:00:00+00:00"
    }
  ],
  "evidence_links": [
    "https://injective-rest.publicnode.com/cosmos/gov/v1/proposals/628"
  ]
}
```

## Core forecasting logic

### 1. Collect upstream events

- GitHub release polling
- Cosmos governance polling

### 2. Normalize them into chain events

Each source becomes a shared event shape:

- `event_key`
- `source_type`
- `stage`
- `cause_type`
- `network_event_time`
- `network_event_height`
- `confidence_hint`
- `evidence_links`

### 3. Convert the chain event into exchange forecasts

Per exchange, `01` applies a lead-time profile:

- `min_lead_hours`
- `default_lead_hours`
- `max_lead_hours`

That creates:

- expected suspension start
- expected suspension window
- exchange-specific likelihood

### 4. Alert only once per source-stage pair

The state store deduplicates by:

`source_type + event_key + stage`

So an early GitHub release and a later governance-passed event can both be surfaced, but the same stage is not repeated.

## What 01 is good at

1. upgrade-driven suspension forecasting for Cosmos-style chains
2. earlier warning from GitHub releases on chains where exchange notices trail the upstream release
3. producing actionable exchange-focused alerts instead of generic protocol alerts

## What 01 is not claiming

1. perfect coverage for every chain
2. perfect visibility into private exchange workflows
3. every release leading to an actual suspension notice

## What comes next

To get closer to true production coverage, the next source families should be added:

1. validator upgrade docs
2. official foundation forums and status pages
3. bridge outage and infra incident feeds
4. exchange notice confirmation for forecast scoring
