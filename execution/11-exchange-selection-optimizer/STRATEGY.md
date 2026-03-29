# 11. Exchange Selection Optimization Strategy

## Purpose
Automatically select the optimal exchange between Upbit and Bithumb for **taking spot long positions**.
Key: Positions must be taken on the exchange with lower liquidity to maximize the closed economy effect.

## Verified Case
- ThunderCore (TT) 2024.05.14: Bithumb **120%** vs Upbit **34%**
  - Bithumb had less supply, resulting in 120% pump
  - Same event, but 3.5x profit difference just from exchange selection

## Selection Criteria

### 1st Criterion: Per-Coin Liquidity by Exchange
```
Comparison items:
  - 24h Volume (Upbit vs Bithumb)
  - Order book depth (ask/bid spread, 1%/2% depth)
  - Estimated coin holdings (on-chain data)

Judgment:
  volume_ratio = bithumb_volume / upbit_volume

  IF volume_ratio < 0.3:  # Bithumb volume less than 30% of Upbit
    → Select Bithumb (maximize closed economy effect)

  IF volume_ratio > 3.0:  # Upbit volume less than 30% of Bithumb
    → Select Upbit

  IF 0.3 <= volume_ratio <= 3.0:
    → Judge by additional criteria
```

### 2nd Criterion: Order Book Depth
```
1% depth comparison (order quantity within ±1% of current price):
  bithumb_depth / upbit_depth ratio

depth_ratio < 0.5 → Select Bithumb (thin order book = maximize premium)
depth_ratio > 2.0 → Select Upbit
```

### 3rd Criterion: Listing Status
```
Upbit exclusive listing → Upbit (no choice, but closed economy maximized)
Bithumb exclusive listing → Bithumb
Listed on both → Apply 1st/2nd criteria
```

### 4th Criterion: Deposit/Withdrawal Suspension Timing
```
Upbit announced first, Bithumb not yet → Position on Bithumb (enter before Bithumb suspension)
Bithumb announced first, Upbit not yet → Position on Upbit
Both simultaneously → Select exchange with lower liquidity
```

## Core Logic

### Composite Score Calculation
```
exchange_score(exchange) =
  liquidity_inverse_score × 0.5     # Lower liquidity = higher score
  + depth_inverse_score × 0.3       # Thinner order book = higher score
  + timing_score × 0.2              # Bonus for exchange not yet announced

bithumb_score = exchange_score("bithumb")
upbit_score = exchange_score("upbit")

selected = argmax(bithumb_score, upbit_score)
```

### Dual Entry on Both Exchanges (Advanced)
```
When capital is sufficient and alpha expected on both sides:
  - Spot long on both Upbit + Bithumb
  - Overseas short = combined quantity of both
  - Close the side with higher premium first
```

## Output
```json
{
  "ticker": "TT",
  "recommended_exchange": "bithumb",
  "reason": "bithumb_lower_liquidity",
  "comparison": {
    "upbit": {
      "24h_volume_krw": 5000000000,
      "1pct_depth_krw": 50000000,
      "spread_pct": 0.8,
      "suspension_announced": true,
      "score": 35
    },
    "bithumb": {
      "24h_volume_krw": 800000000,
      "1pct_depth_krw": 8000000,
      "spread_pct": 2.5,
      "suspension_announced": false,
      "score": 85
    }
  },
  "dual_entry_recommended": false
}
```

## Data Dependencies
- `19-data-registry`: Upbit/Bithumb API endpoints
- `03-exchange-announcement-monitor`: Deposit/withdrawal suspension announcement timing
- `09-delta-neutral-position`: Forward selection results

## Refresh Cycle
- Volume/order book data: **1-minute interval** real-time
- Immediate re-evaluation on signal generation

## Cautions
- Low-liquidity coins on Bithumb also have high entry slippage → Split buy mandatory
- If order book is too thin (spread > 5%), entry itself may be inefficient
- Consider exchange fee differences as well (minimal but meaningful at scale)

---

# 11. 거래소 선택 최적화 전략서

## 목적
업비트와 빗썸 중 **어느 거래소에서 현물 롱 포지션을 잡을지** 최적의 거래소를 자동 선택한다.
핵심: 유동성이 낮은 거래소에서 포지션을 잡아야 폐쇄경제 효과가 극대화된다.

## 검증 사례
- 썬더코어(TT) 2024.05.14: 빗썸 **120%** vs 업비트 **34%**
  - 빗썸에 물량이 더 적어서 120% 펌핑
  - 동일 이벤트인데 거래소 선택만으로 3.5배 수익 차이

## 선택 기준

### 1차 기준: 해당 코인의 거래소별 유동성
```
비교 항목:
  - 24h 거래량 (업비트 vs 빗썸)
  - 호가창 깊이 (ask/bid spread, 1%/2% depth)
  - 해당 코인 보유 물량 추정 (온체인 데이터)

판단:
  거래량_비율 = bithumb_volume / upbit_volume

  IF 거래량_비율 < 0.3:  # 빗썸 거래량이 업비트의 30% 미만
    → 빗썸 선택 (폐쇄경제 효과 극대화)

  IF 거래량_비율 > 3.0:  # 업비트 거래량이 빗썸의 30% 미만
    → 업비트 선택

  IF 0.3 <= 거래량_비율 <= 3.0:
    → 추가 기준으로 판단
```

### 2차 기준: 호가창 깊이
```
1% depth 비교 (현재가 ±1% 내 주문 잔량):
  bithumb_depth / upbit_depth 비율

depth_비율 < 0.5 → 빗썸 선택 (호가 얇음 = 프리미엄 극대화)
depth_비율 > 2.0 → 업비트 선택
```

### 3차 기준: 상장 여부
```
업비트 단독 상장 → 업비트 (선택의 여지 없음, 하지만 폐쇄경제 극대화)
빗썸 단독 상장 → 빗썸
양쪽 상장 → 1차/2차 기준 적용
```

### 4차 기준: 입출금 정지 타이밍
```
업비트 먼저 공지, 빗썸 아직 → 빗썸에서 포지션 (빗썸 정지 전 진입)
빗썸 먼저 공지, 업비트 아직 → 업비트에서 포지션
양쪽 동시 → 유동성 낮은 거래소 선택
```

## 핵심 로직

### 종합 점수 산출
```
exchange_score(exchange) =
  liquidity_inverse_score × 0.5     # 유동성 낮을수록 높은 점수
  + depth_inverse_score × 0.3       # 호가 얇을수록 높은 점수
  + timing_score × 0.2              # 아직 공지 안 난 거래소 보너스

bithumb_score = exchange_score("bithumb")
upbit_score = exchange_score("upbit")

selected = argmax(bithumb_score, upbit_score)
```

### 양쪽 동시 진입 (고급)
```
자본이 충분하고 양쪽 모두 알파 예상 시:
  - 업비트 + 빗썸 양쪽 현물 롱
  - 해외 숏 = 양쪽 합산 수량
  - 프리미엄 높은 쪽 먼저 청산
```

## 출력
```json
{
  "ticker": "TT",
  "recommended_exchange": "bithumb",
  "reason": "bithumb_lower_liquidity",
  "comparison": {
    "upbit": {
      "24h_volume_krw": 5000000000,
      "1pct_depth_krw": 50000000,
      "spread_pct": 0.8,
      "suspension_announced": true,
      "score": 35
    },
    "bithumb": {
      "24h_volume_krw": 800000000,
      "1pct_depth_krw": 8000000,
      "spread_pct": 2.5,
      "suspension_announced": false,
      "score": 85
    }
  },
  "dual_entry_recommended": false
}
```

## 데이터 의존성
- `19-data-registry`: 업비트/빗썸 API 엔드포인트
- `03-exchange-announcement-monitor`: 입출금 정지 공지 타이밍
- `09-delta-neutral-position`: 선택 결과 전달

## 갱신 주기
- 거래량/호가 데이터: **1분 간격** 실시간
- 시그널 발생 시 즉시 재평가

## 주의사항
- 빗썸 유동성 낮은 코인은 진입 슬리피지도 큼 → 분할 매수 필수
- 호가창이 너무 얇으면 (스프레드 > 5%) 진입 자체가 비효율적일 수 있음
- 거래소 수수료 차이도 고려 (미미하지만 대량 시 의미)
