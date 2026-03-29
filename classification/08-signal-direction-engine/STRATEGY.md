# 08. Signal → Position Direction Auto-Decision Strategy

## Purpose
Classifies signals from the detection systems (01~06) and **automatically determines position direction (long+short / prohibited / skip)**.
The hub for all signals. The center of the Signal → Filter (07) → Direction Decision (08) → Execution (09~11) pipeline.

## Signal → Direction Decision Table

| Signal Type | Expected Domestic Direction | Position Decision | Entry Condition | Notes |
|-------------|---------------------------|-------------------|----------------|-------|
| Network Upgrade | Premium ↑ | **Long + Short** | Enter immediately | Highest win rate, main target. 13/22 cases verified |
| Block Halt (short-term) | Premium ↑ | **Conditional Entry** | Only when recovery is fast | Funding rate risk on long halts |
| Hack/Security Incident | Panic Sell ↓ | **Initial Prohibition** | Reverse premium buying after bottom confirmation | Absolutely no immediate long |
| Caution Designation | Panic Sell ↓ | **Initial Prohibition** | Reverse premium buying after bottom confirmation | Same treatment as hack |
| DAXA Trading Risk Warning | Panic Sell ↓↓ | **Prohibited** | Extremely conservative | Delisting possibility |
| Exchange Internal Maintenance (Hot→Cold) | Uncertain | **Small-scale Entry** | S/A grade only | Weak signal |
| Scheduled Server Maintenance | — | **Skip** | No entry | All trading halted, no alpha |
| Other Exchange Prior Announcement | Premium ↑ | **Long + Short** | Enter immediately | Short lead time, fast execution needed |
| Upbit→Bithumb Cross | Premium ↑ | **Long + Short on Bithumb** | Enter immediately | Bithumb closed economy effect is greater |

## Core Logic

### 1. Signal Reception and Classification
```
On signal reception:
  1. Check signal_type
  2. Query target grade from 07-target-coin-filter
  3. Execute classification logic below
```

### 2. Main Scenario: Network Upgrade
```
IF signal_type IN ["governance_upgrade", "github_release", "exchange_announcement_suspension"]
  AND suspension_reason == "network_upgrade"
THEN:
  direction = "LONG_SHORT"  # Domestic long + overseas short
  urgency = based on lead_time:
    > 3 days: "prepare" (prepare, start split buying)
    1~3 days: "enter" (full-scale entry)
    < 1 day: "urgent_enter" (immediate entry)

  → Forward to 09-delta-neutral-position
  → Include: ticker, direction, urgency, target_grade, recommended_exchange
```

### 3. Block Halt Scenario
```
IF signal_type == "block_halt"
THEN:
  IF halt_type == "expected" (scheduled upgrade):
    → Maintain if position exists, enter if not

  IF halt_type == "unexpected":
    IF estimated recovery time < 24 hours:
      direction = "CONDITIONAL_LONG_SHORT"
      → Small-scale entry (50% of regular size)
    ELSE:
      direction = "WAIT"
      → Decide on entry after recovery confirmation
```

### 4. Hack/Security Incident Scenario
```
IF signal_type == "hot_wallet_abnormal_withdrawal"
  OR (signal_type == "caution_designation" AND caution_type == "security_incident")
THEN:
  Phase 1 (immediate): direction = "NO_ENTRY"
    → Absolutely no long entry
    → Hold existing positions (spot, so no liquidation)
    → Consider additional short hedge overseas

  Phase 2 (after bottom confirmation): direction = "REVERSE_PREMIUM_BUY"
    → Confirm domestic price < global price (reverse premium)
    → Buy signal when reverse premium exceeds -10%
    → Deposit/withdrawal resumption → global convergence → profit

  Bottom judgment criteria:
    - Volume spike during panic sell followed by sharp volume decline
    - Price volatility contraction (volatility convergence)
    - Reverse premium expansion stops
```

### 5. Caution Designation / Investment Warning Scenario
```
IF signal_type == "caution_designation"
THEN:
  IF caution_type == "caution_stock_designation":
    → Apply Phase 1/2 same as hack scenario
    → Additionally check delisting possibility
    → Absolute no entry if delisting is scheduled

  IF caution_type == "DAXA_trading_risk_warning":
    → direction = "ABSOLUTE_NO_ENTRY"
    → Delisting risk too high
    → FLOW case: -40% crash, recovery uncertain
```

### 6. Internal Maintenance Scenario
```
IF signal_type == "hot_to_cold_movement"
THEN:
  IF target_grade IN ["S", "A"]:
    direction = "SMALL_LONG_SHORT"  # 30% of regular
  ELSE:
    direction = "SKIP"

  Low confidence, small-scale only
```

### 7. Scheduled Maintenance Filter
```
IF signal_type == "scheduled_maintenance"
  OR movement_pattern == "all_chains"  # All-chain movement
THEN:
  direction = "SKIP"
  reason = "All trading halted, no individual coin alpha"
```

## Final Output (Forwarded to Execution System)
```json
{
  "decision_id": "uuid",
  "ticker": "TT",
  "direction": "LONG_SHORT",
  "urgency": "enter",
  "position_size_ratio": 1.0,
  "target_grade": "S",
  "target_score": 92,
  "recommended_exchange": "bithumb",
  "hedge_type": "proxy_hedge",
  "signal_source": "03-exchange-announcement",
  "original_signal": { ... },
  "constraints": {
    "max_position_pct": 10,
    "entry_method": "split_buy",
    "stop_loss": null
  },
  "created_at": "2024-05-08T01:30:00Z"
}
```

## Simultaneous Multi-Signal Handling
```
When multiple signals received for the same coin simultaneously:
  1. Prioritize the signal with highest confidence
  2. Conflicting signals (upgrade + hack): Choose conservative direction
  3. Reinforcing signals (governance + GitHub): Upgrade confidence, upgrade urgency

Multiple signals for different coins:
  - Consider capital allocation (linked with 17-position-sizing)
  - Prioritize allocation to higher-grade coins
```

## Data Dependencies
- `01~06`: Signal input from all detection systems
- `07-target-coin-filter`: Target grade/score
- `09-delta-neutral-position`: Forward position construction commands
- `14-hack-scenario-holding`: Hack scenario strategy linkage
- `17-position-sizing`: Capital allocation check

---

# 08. 시그널 → 포지션 방향 자동 결정 전략서

## 목적
감지 시스템(01~06)에서 들어오는 시그널을 **분류하고, 포지션 방향(롱+숏 / 금지 / 스킵)을 자동 결정**한다.
모든 시그널의 허브. 시그널 → 필터(07) → 방향 결정(08) → 실행(09~11) 파이프라인의 중심.

## 시그널 → 방향 결정표

| 시그널 유형 | 국내 예상 방향 | 포지션 결정 | 진입 조건 | 비고 |
|------------|-------------|-----------|---------|------|
| 네트워크 업그레이드 | 프리미엄 ↑ | **롱 + 숏** | 즉시 진입 | 최고 승률, 메인 타겟. 13/22건 검증 |
| 블록 halt (단기) | 프리미엄 ↑ | **조건부 진입** | 복구 빠를 때만 | 장기 halt 시 펀딩비 리스크 |
| 해킹/보안 사고 | 패닉셀 ↓ | **초기 금지** | 바닥 확인 후 역프리미엄 추매 | 즉시 롱 절대 금지 |
| 유의종목 지정 | 패닉셀 ↓ | **초기 금지** | 바닥 확인 후 역프리미엄 추매 | 해킹과 동일 처리 |
| DAXA 거래위험 경고 | 패닉셀 ↓↓ | **금지** | 극도 보수적 | 상장폐지 가능성 |
| 거래소 내부 점검 (핫→콜드) | 불확실 | **소규모 진입** | S/A등급만 | 시그널 약함 |
| 정기 서버 점검 | — | **스킵** | 진입 안 함 | 전체 거래 중단, 알파 없음 |
| 타 거래소 선행 공지 | 프리미엄 ↑ | **롱 + 숏** | 즉시 진입 | 리드타임 짧으므로 빠른 실행 |
| 업비트→빗썸 교차 | 프리미엄 ↑ | **빗썸에서 롱 + 숏** | 즉시 진입 | 빗썸 폐쇄경제 효과 더 큼 |

## 핵심 로직

### 1. 시그널 수신 및 분류
```
시그널 수신 시:
  1. signal_type 확인
  2. 07-target-coin-filter에서 타겟 등급 조회
  3. 아래 분류 로직 실행
```

### 2. 메인 시나리오: 네트워크 업그레이드
```
IF signal_type IN ["governance_upgrade", "github_release", "exchange_announcement_suspension"]
  AND suspension_reason == "network_upgrade"
THEN:
  direction = "LONG_SHORT"  # 국내 롱 + 해외 숏
  urgency = lead_time에 따라:
    > 3일: "prepare" (준비, 분할 매수 시작)
    1~3일: "enter" (본격 진입)
    < 1일: "urgent_enter" (즉시 진입)

  → 09-delta-neutral-position으로 전달
  → 포함: ticker, direction, urgency, target_grade, recommended_exchange
```

### 3. 블록 halt 시나리오
```
IF signal_type == "block_halt"
THEN:
  IF halt_type == "expected" (예정된 업그레이드):
    → 이미 포지션 있으면 유지, 없으면 진입

  IF halt_type == "unexpected":
    IF 예상 복구 시간 < 24시간:
      direction = "CONDITIONAL_LONG_SHORT"
      → 소규모 진입 (정규 사이즈의 50%)
    ELSE:
      direction = "WAIT"
      → 복구 확인 후 진입 판단
```

### 4. 해킹/보안 사고 시나리오
```
IF signal_type == "hot_wallet_abnormal_withdrawal"
  OR (signal_type == "caution_designation" AND caution_type == "보안사고")
THEN:
  Phase 1 (즉시): direction = "NO_ENTRY"
    → 절대 롱 진입 금지
    → 기존 포지션 있으면 홀딩 (현물이므로 청산 없음)
    → 해외 숏 추가 헤지 고려

  Phase 2 (바닥 확인 후): direction = "REVERSE_PREMIUM_BUY"
    → 국내 가격 < 글로벌 가격 (역프리미엄) 확인
    → 역프리미엄 -10% 이상 시 추매 시그널
    → 입출금 재개 후 글로벌 수렴 → 수익

  바닥 판단 기준:
    - 패닉셀 거래량 피크 후 거래량 급감
    - 가격 변동률 축소 (변동성 수렴)
    - 역프리미엄 확대 정지
```

### 5. 유의종목/투자경고 시나리오
```
IF signal_type == "caution_designation"
THEN:
  IF caution_type == "유의종목지정":
    → 해킹과 동일하게 Phase 1/2 적용
    → 단, 상장폐지 가능성 체크
    → 상장폐지 예정이면 절대 진입 금지

  IF caution_type == "DAXA거래위험경고":
    → direction = "ABSOLUTE_NO_ENTRY"
    → 상장폐지 리스크 너무 높음
    → FLOW 사례: -40% 급락, 복구 불확실
```

### 6. 내부 점검 시나리오
```
IF signal_type == "hot_to_cold_movement"
THEN:
  IF target_grade IN ["S", "A"]:
    direction = "SMALL_LONG_SHORT"  # 정규의 30%
  ELSE:
    direction = "SKIP"

  신뢰도 낮으므로 소규모만
```

### 7. 정기 점검 필터
```
IF signal_type == "scheduled_maintenance"
  OR movement_pattern == "all_chains"  # 전 체인 이동
THEN:
  direction = "SKIP"
  reason = "전체 거래 중단, 개별 코인 알파 없음"
```

## 최종 출력 (실행 시스템으로 전달)
```json
{
  "decision_id": "uuid",
  "ticker": "TT",
  "direction": "LONG_SHORT",
  "urgency": "enter",
  "position_size_ratio": 1.0,
  "target_grade": "S",
  "target_score": 92,
  "recommended_exchange": "bithumb",
  "hedge_type": "proxy_hedge",
  "signal_source": "03-exchange-announcement",
  "original_signal": { ... },
  "constraints": {
    "max_position_pct": 10,
    "entry_method": "split_buy",
    "stop_loss": null
  },
  "created_at": "2024-05-08T01:30:00Z"
}
```

## 동시 다중 시그널 처리
```
같은 코인에 복수 시그널 동시 수신 시:
  1. 가장 높은 신뢰도 시그널 우선
  2. 상충 시그널 (업그레이드 + 해킹): 보수적 방향 선택
  3. 보강 시그널 (거버넌스 + GitHub): 신뢰도 상향, urgency 상향

다른 코인 복수 시그널:
  - 자본 배분 고려 (17-position-sizing과 연동)
  - 등급 높은 코인 우선 배분
```

## 데이터 의존성
- `01~06`: 모든 감지 시스템의 시그널 입력
- `07-target-coin-filter`: 타겟 등급/점수
- `09-delta-neutral-position`: 포지션 구축 명령 전달
- `14-hack-scenario-holding`: 해킹 시나리오 전략 연동
- `17-position-sizing`: 자본 배분 확인
