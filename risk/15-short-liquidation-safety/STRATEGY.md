# 15. Short Liquidation Price Safety Margin Check Strategy

## Purpose
To **prevent forced liquidation** of overseas futures short positions by monitoring margin balance and liquidation price in real time.
Since the deposit/withdrawal suspension period is unpredictable, ensure **200%+ buffer** so the short is not liquidated even during extended holding.

## Why This Matters
```
If the short gets liquidated:
  - Overseas short disappears → Hedge unravels
  - Only domestic spot remains → Full directional risk exposure
  - Selling domestic spot during deposit/withdrawal suspension forfeits premium
  → Worst case scenario: Short liquidated + domestic premium declines = losses on both sides
```

## Safety Margin Criteria

### Liquidation Price Buffer Standards
```
Minimum standard: Liquidation price = entry price x 2.0 (survives 100% price increase)
Recommended standard: Liquidation price = entry price x 3.0 (survives 200% price increase)

Example (1x short, cross margin):
  Entry price: $0.10
  Margin: $0.30 (3x)
  Liquidation price: $0.40 (at 300% increase)
  → Safety buffer: 300% ✓
```

### Margin Calculation
```
Required margin = position_notional / leverage  # For 1x = position_notional
Additional margin = required margin x safety_multiplier  # Minimum 2.0

Total required margin = required margin + additional margin
  = position_notional x (1 + safety_multiplier)
  = position_notional x 3  (when safety_multiplier=2)
```

## Core Logic

### 1. Validation at Position Open
```
Before opening short in 09-delta-neutral-position:

  Calculate: liquidation_price = entry_price x (1 + margin/position_notional)

  IF liquidation_price < entry_price x 2.0:
    → Warning: "Insufficient margin -- minimum 200% buffer not met"
    → Request additional margin deposit

  IF liquidation_price < entry_price x 3.0:
    → Caution: "Recommended 300% buffer not met"
    → Can proceed but display warning
```

### 2. Real-time Liquidation Price Monitoring
```
Every 1 minute for each active short position:

  current_price = overseas exchange current price
  distance_to_liquidation = (liquidation_price - current_price) / current_price x 100

  Level 1 (Safe): distance > 100%
    → Normal, maintain monitoring

  Level 2 (Caution): 50% < distance <= 100%
    → Alert: "Approaching liquidation price"
    → Recommend additional margin

  Level 3 (Warning): 30% < distance <= 50%
    → Urgent alert: "Liquidation risk"
    → Auto-add margin (if configured)
    → Or consider partial short close

  Level 4 (Danger): distance <= 30%
    → Urgent alert: "Liquidation imminent"
    → Auto-add margin or strategic short reduction
    → #18 notification + mobile urgent alert
```

### 3. Automatic Margin Addition (Optional)
```
When configured:
  Maintain reserve margin in overseas exchange account
  Automatically add margin when Level 3 is reached

Auto margin addition limit:
  Total margin < 15% of total capital
  Request manual intervention when limit exceeded
```

### 4. Global Price Surge Scenario
```
When global price surges during deposit/withdrawal suspension:
  - Short position unrealized loss increases
  - However, domestic spot may also rise (hedge works)
  - Problem: Domestic is a closed economy so may not rise as much as global
  - In this case: Short unrealized loss > domestic spot unrealized gain

  Response:
    - If margin is sufficient, hold (convergence after resumption)
    - If margin is insufficient, partially reduce short + partially sell domestic spot (balance)
```

## Output
```json
{
  "position_id": "pos_uuid",
  "ticker": "TT",
  "exchange": "binance",
  "check_time": "2024-05-14T06:00:00Z",
  "entry_price_usd": 0.115,
  "current_price_usd": 0.125,
  "liquidation_price_usd": 0.345,
  "distance_to_liquidation_pct": 176,
  "margin_balance_usd": 3450,
  "unrealized_pnl_usd": -100,
  "safety_level": "safe",
  "safety_grade": "Level 1",
  "action_required": false,
  "recommendation": null
}
```

## Data Dependencies
- `09-delta-neutral-position`: Active short position information
- `18-notification-system`: Warning/urgent alert delivery
- `16-funding-rate-tracker`: Reflect margin changes due to funding fees

## Monitoring Frequency
- Normal state: **1-minute intervals**
- Level 2: **30-second intervals**
- Level 3/4: **10-second intervals**

---

# 15. 숏 청산가 안전 마진 체크 전략서

## 목적
해외 선물 숏 포지션의 **강제 청산(liquidation)을 방지**하기 위해 마진 잔고와 청산가를 실시간 모니터링한다.
입출금 정지 기간이 예측 불가이므로, 장기간 숏 유지 시에도 청산되지 않도록 **200%+ 여유** 확보.

## 왜 중요한가
```
숏이 청산되면:
  - 해외 숏 소멸 → 헤지 풀림
  - 국내 현물만 남음 → 방향성 리스크 전면 노출
  - 입출금 정지 상태에서 국내 현물 매도는 프리미엄 포기
  → 최악의 시나리오: 숏 청산 + 국내 프리미엄 하락 = 양쪽 손실
```

## 안전 마진 기준

### 청산가 여유 기준
```
최소 기준: 청산가 = 진입가 × 2.0 (100% 상승해도 청산 안 됨)
권장 기준: 청산가 = 진입가 × 3.0 (200% 상승해도 청산 안 됨)

예시 (1x 숏, 크로스 마진):
  진입가: $0.10
  마진: $0.30 (3x)
  청산가: $0.40 (300% 상승 시)
  → 안전 여유: 300% ✓
```

### 마진 계산
```
필요 마진 = position_notional / leverage  # 1x이면 = position_notional
추가 마진 = 필요 마진 × safety_multiplier  # 최소 2.0

총 필요 마진 = 필요 마진 + 추가 마진
  = position_notional × (1 + safety_multiplier)
  = position_notional × 3  (safety_multiplier=2일 때)
```

## 핵심 로직

### 1. 포지션 오픈 시 검증
```
09-delta-neutral-position에서 숏 오픈 전:

  계산: liquidation_price = entry_price × (1 + margin/position_notional)

  IF liquidation_price < entry_price × 2.0:
    → 경고: "마진 부족 — 최소 200% 여유 미달"
    → 추가 마진 입금 요청

  IF liquidation_price < entry_price × 3.0:
    → 주의: "권장 300% 여유 미달"
    → 진행 가능하지만 경고 표시
```

### 2. 실시간 청산가 모니터링
```
매 1분마다 각 활성 숏 포지션:

  current_price = 해외 거래소 현재가
  distance_to_liquidation = (liquidation_price - current_price) / current_price × 100

  Level 1 (안전): distance > 100%
    → 정상, 모니터링 유지

  Level 2 (주의): 50% < distance <= 100%
    → 알림: "청산가 접근 주의"
    → 추가 마진 권고

  Level 3 (경고): 30% < distance <= 50%
    → 긴급 알림: "청산 위험"
    → 자동 추가 마진 (설정된 경우)
    → 또는 일부 숏 청산 고려

  Level 4 (위험): distance <= 30%
    → 긴급 알림: "청산 임박"
    → 자동 마진 추가 또는 전략적 숏 축소
    → 18번 알림 + 모바일 긴급 알림
```

### 3. 자동 마진 추가 (선택적)
```
설정 시:
  해외 거래소 계정에 예비 마진 확보
  Level 3 도달 시 자동으로 마진 추가

자동 마진 추가 한도:
  총 마진 < 전체 자본의 15% 이내
  한도 초과 시 수동 개입 요청
```

### 4. 글로벌 가격 급등 시나리오
```
입출금 정지 중 글로벌 가격 급등 시:
  - 숏 포지션 미실현 손실 증가
  - 하지만 국내 현물도 동반 상승 가능 (헤지 작동)
  - 문제: 국내는 폐쇄경제이므로 글로벌만큼 안 오를 수 있음
  - 이 경우 숏 미실현 손실 > 국내 현물 미실현 이익

  대응:
    - 마진 충분하면 홀딩 (입출금 재개 후 수렴)
    - 마진 부족 시 일부 숏 축소 + 국내 현물 일부 매도 (균형)
```

## 출력
```json
{
  "position_id": "pos_uuid",
  "ticker": "TT",
  "exchange": "binance",
  "check_time": "2024-05-14T06:00:00Z",
  "entry_price_usd": 0.115,
  "current_price_usd": 0.125,
  "liquidation_price_usd": 0.345,
  "distance_to_liquidation_pct": 176,
  "margin_balance_usd": 3450,
  "unrealized_pnl_usd": -100,
  "safety_level": "safe",
  "safety_grade": "Level 1",
  "action_required": false,
  "recommendation": null
}
```

## 데이터 의존성
- `09-delta-neutral-position`: 활성 숏 포지션 정보
- `18-notification-system`: 경고/긴급 알림 발송
- `16-funding-rate-tracker`: 펀딩비로 인한 마진 변동도 반영

## 모니터링 주기
- 정상 상태: **1분 간격**
- Level 2: **30초 간격**
- Level 3/4: **10초 간격**
