# 09. Delta Neutral Position Construction Strategy

## Purpose
When a "LONG_SHORT" decision is made by module 08, **simultaneously take a domestic spot long + overseas futures 1x short** to completely eliminate global price movement risk and **purely capture the Korea premium**.

## Position Structure

| Category | Domestic (Upbit/Bithumb) | Overseas (Binance/OKX/Bybit) | Net Exposure |
|----------|-------------------------|------------------------------|-------------|
| Position | **Spot Long** | **Futures 1x Short** | Korea Premium Only |
| Characteristics | No liquidation, indefinite holding possible | Cross margin, liquidation price 200%+ headroom | Unaffected by global ups/downs |

## Core Principle
```
Deposit/withdrawal suspension → Arbitrage blocked → Independent price formation on domestic exchange → Premium emerges
Domestic spot long: Premium profit
Overseas futures short: Global price movement hedge
Net profit = Korea Premium
```

## Execution Logic

### 1. Entry Order (Mandatory: Domestic First)
```
Step 1: Domestic spot buy (Upbit or Bithumb)
  - Use exchange recommended by 11-exchange-selection-optimizer
  - Split buy: Enter in 3~5 tranches
  - Market order + order book analysis combined (minimize slippage)

Step 2: Overseas futures short (Binance/OKX/Bybit)
  - Execute immediately after domestic buy is complete
  - Same quantity 1x short
  - Market order entry (speed priority since it's a hedge)

Why order matters:
  - Buy domestic first to minimize order book impact
  - Overseas short has ample liquidity, so lower priority is OK
  - Target time gap within 30 seconds maximum
```

### 2. Quantity Match Verification
```
Domestic buy quantity (qty_domestic)
Overseas short quantity (qty_overseas)

Verification:
  abs(qty_domestic - qty_overseas) / qty_domestic < 0.02  # 2% tolerance

On mismatch:
  - Adjust overseas short quantity (add short or partially close short)
  - Send mismatch alert
```

### 3. Split Buy Strategy
```
urgency == "prepare" (lead time 3+ days):
  5 tranches, 6-hour intervals
  20% each tranche

urgency == "enter" (lead time 1~3 days):
  3 tranches, 2-hour intervals
  33% each tranche

urgency == "urgent_enter" (lead time < 1 day):
  2 tranches, 30-minute intervals
  50% each tranche
  Or market order bulk entry
```

### 4. Overseas Futures Settings
```
Leverage: 1x (fixed, absolutely no changes)
Margin mode: Cross margin
Liquidation price headroom: 200%+ (relative to current price)

Margin calculation:
  Required margin = position_size / leverage
  Additional margin = required_margin × 2  # 200% headroom
  Total margin = required_margin + additional_margin

→ Real-time verification by 15-short-liquidation-safety
```

### 5. Proxy Hedge (Coins Without Futures Support)
```
When the coin's futures are not available on Binance/OKX:
  → Query substitute token from 10-proxy-hedge-mapper
  → Short the major token of the same network

Example:
  TT (ThunderCore) has no futures
  → Proxy hedge with same ecosystem or small-cap alt index
  → Not a perfect hedge but reduces directional risk

Additional caution for proxy hedge:
  - Check correlation coefficient (0.7+ recommended)
  - Adjust size (consider beta)
```

## P&L by Scenario

| Scenario | Domestic Long | Overseas Short | Net Profit |
|----------|--------------|----------------|-----------|
| Upgrade → Premium +20% | +20% | 0% | **+20%** |
| Domestic +20%, Global +10% | +20% | -10% | **+10%** |
| Domestic +5%, Global -15% crash | +5% | +15% | **+20%** |
| No premium, synchronized decline | -10% | +10% | **0%** |
| Hack → Panic sell -30%, Global -5% | -30%(paper) | +5% | **Hold → 0%** |
| Hack panic sell + reverse premium buying | Hold+buy more | Additional hedge | **+15~25%** |

**Key: Since it's spot holding, no loss if you don't sell during panic sell phase. After resumption, convergence → worst case break-even.**

## Output
```json
{
  "position_id": "uuid",
  "ticker": "TT",
  "domestic": {
    "exchange": "bithumb",
    "side": "long",
    "type": "spot",
    "qty": 10000,
    "avg_entry_price_krw": 150,
    "total_cost_krw": 1500000,
    "entries": [
      {"qty": 5000, "price": 148, "time": "..."},
      {"qty": 5000, "price": 152, "time": "..."}
    ]
  },
  "overseas": {
    "exchange": "binance",
    "side": "short",
    "type": "futures_perp",
    "leverage": 1,
    "margin_mode": "cross",
    "qty": 10000,
    "entry_price_usd": 0.115,
    "margin_usd": 3450,
    "liquidation_price_usd": 0.345
  },
  "qty_match_pct": 100,
  "hedge_type": "direct",
  "status": "active",
  "opened_at": "2024-05-08T02:00:00Z"
}
```

## Data Dependencies
- `08-signal-direction-engine`: Position direction, urgency, size ratio
- `10-proxy-hedge-mapper`: Substitute token when futures not supported
- `11-exchange-selection-optimizer`: Domestic exchange selection
- `15-short-liquidation-safety`: Short liquidation price safety verification
- `17-position-sizing`: Size limits relative to total capital

---

# 09. 델타 뉴트럴 포지션 구축 전략서

## 목적
08번에서 "LONG_SHORT" 결정이 내려지면, **국내 현물 롱 + 해외 선물 1x 숏**을 동시에 잡아
글로벌 가격 변동 리스크를 완전 제거하고 **한국 프리미엄만 순수하게 캡처**하는 포지션을 구축한다.

## 포지션 구조

| 구분 | 국내 (업비트/빗썸) | 해외 (바이낸스/OKX/Bybit) | 순노출 |
|------|------------------|------------------------|--------|
| 포지션 | **현물 롱** | **선물 1x 숏** | 한국 프리미엄만 |
| 특징 | 청산 없음, 무기한 홀딩 가능 | 크로스 마진, 청산가 200%+ 여유 | 글로벌 상승/하락 무관 |

## 핵심 원리
```
입출금 정지 → 아비트라지 차단 → 국내 거래소 독립 가격 형성 → 프리미엄 발생
국내 현물 롱: 프리미엄 수익
해외 선물 숏: 글로벌 가격 변동 헤지
순수익 = 한국 프리미엄
```

## 실행 로직

### 1. 진입 순서 (필수: 국내 먼저)
```
Step 1: 국내 현물 매수 (업비트 또는 빗썸)
  - 11-exchange-selection-optimizer에서 추천한 거래소 사용
  - 분할 매수: 3~5회로 나누어 진입
  - 시장가 + 호가 분석 병행 (슬리피지 최소화)

Step 2: 해외 선물 숏 (바이낸스/OKX/Bybit)
  - 국내 매수 완료 후 즉시 실행
  - 동일 수량 1x 숏
  - 시장가 진입 (헤지이므로 속도 우선)

순서가 중요한 이유:
  - 국내 먼저 매수해야 호가 영향 최소화
  - 해외 숏은 유동성 풍부하므로 후순위 OK
  - 시간차 최대 30초 이내 목표
```

### 2. 수량 일치 검증
```
국내 매수 수량 (qty_domestic)
해외 숏 수량 (qty_overseas)

검증:
  abs(qty_domestic - qty_overseas) / qty_domestic < 0.02  # 2% 이내 오차 허용

불일치 시:
  - 해외 숏 수량 조정 (추가 숏 또는 일부 숏 청산)
  - 불일치 알림 발송
```

### 3. 분할 매수 전략
```
urgency == "prepare" (리드타임 3일+):
  5회 분할, 6시간 간격
  각 회차 20%씩

urgency == "enter" (리드타임 1~3일):
  3회 분할, 2시간 간격
  각 회차 33%씩

urgency == "urgent_enter" (리드타임 < 1일):
  2회 분할, 30분 간격
  각 회차 50%씩
  또는 시장가 일괄 진입
```

### 4. 해외 선물 설정
```
레버리지: 1x (고정, 절대 변경 금지)
마진 모드: 크로스 마진
청산가 여유: 200%+ (현재가 대비)

마진 계산:
  필요 마진 = position_size / leverage
  추가 마진 = 필요 마진 × 2  # 200% 여유
  총 마진 = 필요 마진 + 추가 마진

→ 15-short-liquidation-safety에서 실시간 검증
```

### 5. Proxy Hedge (선물 미지원 코인)
```
해당 코인 선물이 바이낸스/OKX에 없는 경우:
  → 10-proxy-hedge-mapper에서 대체 토큰 조회
  → 같은 네트워크 메이저 토큰으로 숏

예시:
  TT (ThunderCore) 선물 없음
  → 같은 생태계 또는 소형알트 인덱스로 proxy hedge
  → 완벽한 헤지는 아니지만 방향성 리스크 감소

proxy hedge 시 추가 주의:
  - 상관계수 확인 (0.7 이상 권장)
  - 사이즈 조정 (베타 고려)
```

## 시나리오별 P&L

| 시나리오 | 국내 롱 | 해외 숏 | 순수익 |
|---------|--------|--------|--------|
| 업그레이드 → 프리미엄 +20% | +20% | 0% | **+20%** |
| 국내 +20%, 글로벌 +10% | +20% | -10% | **+10%** |
| 국내 +5%, 글로벌 -15% 급락 | +5% | +15% | **+20%** |
| 프리미엄 안 붙음, 동조 하락 | -10% | +10% | **0%** |
| 해킹 → 패닉셀 -30%, 글로벌 -5% | -30%(종이) | +5% | **홀딩 → 0%** |
| 해킹 패닉셀 + 역프리미엄 추매 | 홀딩+추매 | 추가 헤지 | **+15~25%** |

**핵심: 현물 홀딩이므로 패닉셀 구간에서 안 팔면 손실 없음. 재개 후 수렴 → 최악 본전.**

## 출력
```json
{
  "position_id": "uuid",
  "ticker": "TT",
  "domestic": {
    "exchange": "bithumb",
    "side": "long",
    "type": "spot",
    "qty": 10000,
    "avg_entry_price_krw": 150,
    "total_cost_krw": 1500000,
    "entries": [
      {"qty": 5000, "price": 148, "time": "..."},
      {"qty": 5000, "price": 152, "time": "..."}
    ]
  },
  "overseas": {
    "exchange": "binance",
    "side": "short",
    "type": "futures_perp",
    "leverage": 1,
    "margin_mode": "cross",
    "qty": 10000,
    "entry_price_usd": 0.115,
    "margin_usd": 3450,
    "liquidation_price_usd": 0.345
  },
  "qty_match_pct": 100,
  "hedge_type": "direct",
  "status": "active",
  "opened_at": "2024-05-08T02:00:00Z"
}
```

## 데이터 의존성
- `08-signal-direction-engine`: 포지션 방향, urgency, 사이즈 비율
- `10-proxy-hedge-mapper`: 선물 미지원 시 대체 토큰
- `11-exchange-selection-optimizer`: 국내 거래소 선택
- `15-short-liquidation-safety`: 숏 청산가 안전 검증
- `17-position-sizing`: 전체 자본 대비 사이즈 제한
