# 16. Funding Rate Tracker Strategy

## Purpose
**Track accumulated funding rate costs** while maintaining overseas futures short positions, monitoring impact on net profit in real time.
If the deposit/withdrawal suspension period extends, funding fees can become the sole cost, so the cost-to-profit ratio must be managed.

## Funding Rate Basics
```
Perpetual futures settle funding rates every 8 hours:
  - Positive funding rate: Longs pay shorts (short holders = profit)
  - Negative funding rate: Shorts pay longs (short holders = cost)

Typical situations:
  - Bull market: Positive funding rate → Favorable for short holders (bonus)
  - Bear market: Negative funding rate → Unfavorable for short holders (cost)

Settlement times (Binance standard):
  00:00 UTC, 08:00 UTC, 16:00 UTC
```

## Core Logic

### 1. Real-time Funding Rate Collection
```
For each active short position's exchange:
  - Binance: GET /fapi/v1/fundingRate
  - OKX: GET /api/v5/public/funding-rate
  - Bybit: GET /v5/market/funding/history

Collected items:
  - Current funding rate (current_funding_rate)
  - Predicted next funding rate (predicted_next)
  - Recent funding rate history (30 days)
```

### 2. Cumulative Funding Fee Calculation
```
At each settlement:
  funding_payment = position_notional x funding_rate

  Positive: Short holder receives (profit)
  Negative: Short holder pays (cost)

Cumulative:
  cumulative_funding = Σ funding_payments (since position opened)

Daily conversion:
  daily_funding_cost = 3 x avg_funding_rate x position_notional
  (3 settlements per day)
```

### 3. Profit-to-Cost Ratio Monitoring
```
Expected premium profit vs funding fee cost:

  profit_ratio = expected_premium_pct / cumulative_funding_pct

  Positive funding (favorable for short):
    → profit_ratio infinite (zero cost, actually profitable)
    → No alert needed

  Negative funding (unfavorable for short):
    profit_ratio > 5: Safe (expected profit 5x+ funding fees)
    profit_ratio 2~5: Caution (funding fees accumulating)
    profit_ratio < 2: Warning (funding fees eroding profit)
    profit_ratio < 1: Danger (funding fees > expected profit, consider liquidation)
```

### 4. Projected Costs for Extended Holding
```
When deposit/withdrawal suspension period extends:

  Projected funding fees by duration:
    1 week: avg_daily_funding x 7
    2 weeks: avg_daily_funding x 14
    1 month: avg_daily_funding x 30

  When projected cost exceeds 30% of target profit:
    → Warning alert
    → Review short reduction or position close
```

### 5. Funding Rate-based Decision Making
```
Case 1: Sustained positive funding rate
  → Bonus for maintaining short → Added to profit
  → Aggressive holding favorable

Case 2: Slightly negative funding rate (-0.01% or less)
  → Negligible level
  → Maintain holding

Case 3: Moderately negative funding rate (-0.01% ~ -0.05%)
  → Daily cost 0.03%~0.15%
  → Weekly 0.21%~1.05%
  → Maintain if premium is sufficient, otherwise review

Case 4: Heavily negative funding rate (-0.05% or more)
  → Daily cost 0.15%+
  → Weekly 1%+
  → Strongly recommend early liquidation
```

## Output
```json
{
  "position_id": "pos_uuid",
  "ticker": "TT",
  "exchange": "binance",
  "current_funding_rate": -0.0085,
  "predicted_next_rate": -0.0092,
  "funding_direction": "short_pays",
  "cumulative_funding_usd": -12.50,
  "cumulative_funding_pct": -0.36,
  "holding_days": 5,
  "daily_avg_cost_pct": 0.072,
  "projected_cost_7d_pct": 0.50,
  "projected_cost_14d_pct": 1.01,
  "current_premium_pct": 15.0,
  "profit_cost_ratio": 41.7,
  "status": "safe",
  "recommendation": "hold"
}
```

## Data Dependencies
- `09-delta-neutral-position`: Active short position information
- `12-premium-realtime-tracker`: Current premium (for profit-to-cost calculation)
- `15-short-liquidation-safety`: Share margin changes due to funding fees
- `18-notification-system`: Warning alerts

## Monitoring Frequency
- Funding rate collection: **1-hour intervals** (check before settlement)
- Cumulative calculation: **8-hour intervals** (after settlement)
- Cost ratio check: **Once daily**

---

# 16. 펀딩비 트래커 전략서

## 목적
해외 선물 숏 유지 중 **펀딩비(funding rate) 누적을 추적**하여 순수익에 미치는 영향을 실시간 모니터링한다.
입출금 정지 기간이 길어지면 펀딩비가 유일한 비용이 될 수 있으므로, 수익 대비 비용 비율을 관리한다.

## 펀딩비 기본 개념
```
무기한 선물(perpetual)은 8시간마다 펀딩비 정산:
  - 양수 펀딩비: 롱이 숏에게 지불 (숏 보유자 = 수익)
  - 음수 펀딩비: 숏이 롱에게 지불 (숏 보유자 = 비용)

일반적 상황:
  - 상승장: 양수 펀딩비 → 숏 홀더에게 유리 (보너스)
  - 하락장: 음수 펀딩비 → 숏 홀더에게 불리 (비용)

정산 시간 (바이낸스 기준):
  00:00 UTC, 08:00 UTC, 16:00 UTC
```

## 핵심 로직

### 1. 펀딩비 실시간 수집
```
각 활성 숏 포지션의 거래소:
  - 바이낸스: GET /fapi/v1/fundingRate
  - OKX: GET /api/v5/public/funding-rate
  - Bybit: GET /v5/market/funding/history

수집 항목:
  - 현재 펀딩비율 (current_funding_rate)
  - 예상 다음 펀딩비율 (predicted_next)
  - 최근 펀딩비 히스토리 (30일)
```

### 2. 누적 펀딩비 계산
```
각 정산 시:
  funding_payment = position_notional × funding_rate

  양수: 숏 홀더 수취 (수익)
  음수: 숏 홀더 지불 (비용)

누적:
  cumulative_funding = Σ funding_payments (포지션 오픈 이후)

일 환산:
  daily_funding_cost = 3 × avg_funding_rate × position_notional
  (하루 3회 정산)
```

### 3. 수익 대비 비용 비율 모니터링
```
예상 프리미엄 수익 vs 펀딩비 비용:

  profit_ratio = expected_premium_pct / cumulative_funding_pct

  양수 펀딩 (숏에 유리):
    → profit_ratio 무한대 (비용 0, 오히려 수익)
    → 알림 불필요

  음수 펀딩 (숏에 불리):
    profit_ratio > 5: 안전 (펀딩비 대비 5배 이상 수익 예상)
    profit_ratio 2~5: 주의 (펀딩비 누적 중)
    profit_ratio < 2: 경고 (펀딩비가 수익 잠식)
    profit_ratio < 1: 위험 (펀딩비 > 예상 수익, 청산 고려)
```

### 4. 장기 홀딩 시 예상 비용
```
입출금 정지 기간이 길어질 경우:

  예상 기간별 펀딩비:
    1주: avg_daily_funding × 7
    2주: avg_daily_funding × 14
    1개월: avg_daily_funding × 30

  예상 비용이 목표 수익의 30% 초과 시:
    → 경고 알림
    → 숏 축소 또는 포지션 정리 검토
```

### 5. 펀딩비 기반 의사결정
```
Case 1: 양수 펀딩비 지속
  → 숏 유지 보너스 → 수익에 추가
  → 적극적 홀딩 유리

Case 2: 음수 펀딩비 소폭 (-0.01% 이하)
  → 무시 가능 수준
  → 홀딩 유지

Case 3: 음수 펀딩비 중폭 (-0.01% ~ -0.05%)
  → 일 비용 0.03%~0.15%
  → 주간 0.21%~1.05%
  → 프리미엄 충분하면 유지, 아니면 검토

Case 4: 음수 펀딩비 대폭 (-0.05% 이상)
  → 일 비용 0.15%+
  → 주간 1%+
  → 조기 청산 강력 권고
```

## 출력
```json
{
  "position_id": "pos_uuid",
  "ticker": "TT",
  "exchange": "binance",
  "current_funding_rate": -0.0085,
  "predicted_next_rate": -0.0092,
  "funding_direction": "short_pays",
  "cumulative_funding_usd": -12.50,
  "cumulative_funding_pct": -0.36,
  "holding_days": 5,
  "daily_avg_cost_pct": 0.072,
  "projected_cost_7d_pct": 0.50,
  "projected_cost_14d_pct": 1.01,
  "current_premium_pct": 15.0,
  "profit_cost_ratio": 41.7,
  "status": "safe",
  "recommendation": "hold"
}
```

## 데이터 의존성
- `09-delta-neutral-position`: 활성 숏 포지션 정보
- `12-premium-realtime-tracker`: 현재 프리미엄 (수익 대비 비용 계산)
- `15-short-liquidation-safety`: 펀딩비로 인한 마진 변동 공유
- `18-notification-system`: 경고 알림

## 모니터링 주기
- 펀딩비율 수집: **1시간 간격** (정산 전 확인)
- 누적 계산: **8시간 간격** (정산 후)
- 비용 비율 체크: **일 1회**
