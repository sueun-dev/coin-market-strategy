# 01. Deposit/Withdrawal Suspension Forecaster Coverage

## Coverage model

The rebuilt `01` does not claim perfect all-chain coverage.
It covers configured chains through the public upstream sources that are currently implemented.

Today those sources are:

1. GitHub releases
2. Cosmos governance upgrade proposals

## Strength buckets

### Strong

These targets have both GitHub release monitoring and Cosmos governance monitoring.

- `ATOM`
- `SEI`
- `INJ`
- `KAVA`
- `AXL`
- `TIA`
- `CRO`
- `MED`
- `OSMO`
- `BAND`

These are the best current candidates for early suspension forecasting because they have two independent public upstream paths.

### Medium

These targets currently have Cosmos governance monitoring only.

- `AKT`
- `STRD`
- `STARS`

They can still emit useful suspension forecasts, but they have less upstream redundancy.

### Partial

These targets currently have GitHub release monitoring only.

- `DOT`
- `XTZ`
- `APT`
- `SUI`
- `ALGO`
- `ADA`
- `ICX`
- `CELO`
- `SOL`
- `POL`
- `ARB`
- `OP`
- `AVAX`
- `FLOW`
- `QTUM`
- `IP`
- `XRP`
- `XLM`
- `NEAR`
- `STX`
- `IOTA`
- `IRIS`
- `ZIL`
- `CKB`
- `VET`

This is useful for early warning, but weaker than dual-source coverage.

## Important limitation

`01` is not yet a perfect "every listed chain, every suspension" system.

The honest status today is:

1. strong on selected Cosmos-family chains
2. partial on many non-Cosmos chains through GitHub only
3. not yet enriched with validator docs, forums, status pages, or bridge incident feeds

## Exchange mapping quality

Targets are only forecast against exchanges that are explicitly configured in `targets.json`.

That means:

1. `listed_on` data is trusted only where it is explicitly set
2. chains with empty `listed_on` will still be collected, but no exchange action forecast will be emitted

## Practical interpretation

When `01` sends an alert, read it as:

`A public upstream event has appeared that could cause Upbit or Bithumb to suspend deposits and withdrawals soon.`

When `01` stays quiet, do not read that as:

`No suspension risk exists.`

It may instead mean:

1. the chain is outside current upstream coverage
2. the event is happening in a source family not implemented yet
3. the exchange learned it from a private or faster operational channel
