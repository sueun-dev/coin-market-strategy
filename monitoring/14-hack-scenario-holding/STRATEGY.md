# 14. Hack Scenario Holding Strategy

## Purpose
During hacking/security incidents/caution designation, **never sell during the panic sell phase and hold**,
**additionally buy during the reverse premium phase** to lock in profit at the global convergence point after deposit/withdrawal resumption.

## Core Principle
```
Since this is spot holding, no loss if you don't sell during panic sell phase (paper loss only)
Deposit/withdrawal resumes → Arbitrage inflow → Global price convergence → At worst, break even
Additional buying during reverse premium phase can yield even more profit (+15~25%)
```

## Verified Cases
- 2025.11.27 Upbit Solana hack 44.5 billion KRW
  - Panic sell occurred → Full deposit/withdrawal suspension → Later resumed → Convergence
- FLOW security incident 2025.12.27
  - DAXA trading risk warning → -40% crash → Deposit/withdrawal suspended

## Execution Phases

### Phase 0: Hack/Incident Detection (Signal received from #05)
```
Signal received from 05-hot-wallet-abnormal-withdrawal or
03-exchange-announcement-monitor (caution/DAXA warning)

Immediate actions:
  - Absolutely no new long entries
  - Switch existing positions to holding mode
  - Maintain overseas short (hedges global decline)
```

### Phase 1: Panic Sell Phase (hours to 1 day)
```
Domestic price crashes, global may also decline

Actions:
  - No spot selling (absolute rule)
  - Maintain overseas short → Profit from global decline
  - Intensify premium monitoring (#12)

Monitoring:
  - Track domestic vs global price divergence
  - Panic sell volume trends
  - Whether reverse premium occurs
```

### Phase 2: Reverse Premium Phase (when panic sell intensifies)
```
Domestic price < Global price = Reverse premium occurs
Irrational selling driven by fear → Domestic becomes cheaper than global

Additional buy criteria:
  Reverse premium -5%: Prepare for additional buy (small scale, 20% of total)
  Reverse premium -10%: 1st additional buy (30% of total)
  Reverse premium -15%: 2nd additional buy (30% of total)
  Reverse premium -20% or more: 3rd additional buy (entire remainder)

Additional overseas short with each buy:
  Add overseas short matching additional buy quantity → Maintain delta neutral
  When reverse premium converges, additional buy profit = reverse premium spread
```

### Phase 3: Stabilization Phase
```
Panic sell ends, volume drops sharply, volatility contracts

Actions:
  - Maintain position holding
  - Monitor for deposit/withdrawal resumption announcements
  - Check accumulated funding fees (#16)
```

### Phase 4: Deposit/Withdrawal Resumes → Convergence → Liquidation
```
When deposit/withdrawal resumption announcement detected:
  1. Expect arbitrage bot inflow → Convergence to global price
  2. Premium/reverse premium → Converges to 0%
  3. After convergence confirmed, liquidate via 13-simultaneous-liquidation

Liquidation timing:
  - Rapid convergence right after resumption: Liquidate after convergence complete
  - Gradual convergence: Liquidate when reverse premium → reaches 0%
  - Premium reversal (reverse premium → positive premium): Liquidate at premium peak
```

## P&L Scenarios

### Hack Occurs with Existing Position
```
Entry: Domestic long 100 KRW, overseas short $0.07

Right after hack:
  Domestic 70 KRW (-30%), overseas $0.065 (-7%)
  Domestic PnL: -30% (paper)
  Overseas PnL: +7%

Phase 2 additional buy (reverse premium -10%):
  Domestic additional buy 65 KRW, overseas additional short $0.065

After resumption convergence (global $0.063 level):
  Domestic: Converges to 85 KRW (additional buy +30%)
  Overseas: Short close ($0.063, original +10%, additional +3%)

Net profit: Additional buy reverse premium capture +15~25%
```

### Hack Detected with No Position
```
Phase 1: No entry
Phase 2: New entry when reverse premium occurs
  Domestic long (at reverse premium price) + overseas short
  After resumption convergence → Reverse premium spread = profit
```

## Output
```json
{
  "scenario": "hack_holding",
  "ticker": "SOL",
  "phase": "phase_2_reverse_premium",
  "current_premium_pct": -12.5,
  "action": "additional_buy",
  "additional_buy": {
    "qty": 50,
    "target_price_krw": 180000,
    "additional_hedge_qty": 50,
    "hedge_exchange": "binance"
  },
  "existing_position": {
    "domestic_qty": 100,
    "domestic_avg_price": 210000,
    "overseas_short_qty": 100,
    "paper_loss_pct": -14.3,
    "actual_loss": 0
  },
  "exit_plan": "wait_for_resumption_then_converge"
}
```

## Data Dependencies
- `05-hot-wallet-abnormal-withdrawal`: Hack signal
- `03-exchange-announcement-monitor`: Caution/DAXA warning, resumption announcements
- `12-premium-realtime-tracker`: Reverse premium monitoring
- `09-delta-neutral-position`: Additional buy position construction
- `13-simultaneous-liquidation`: Final liquidation
- `16-funding-rate-tracker`: Funding fees during extended holding

## Absolute Rules
1. **No spot selling during panic sell phase** -- the most important rule
2. When making additional buys during reverse premium, always add overseas short (maintain delta neutral)
3. This strategy cannot be applied to coins with delisting risk (DAXA warning coins)
4. No liquidation until deposit/withdrawal resumption is confirmed

---

# 14. 해킹 시나리오 홀딩 전략서

## 목적
해킹/보안 사고/유의종목 지정 시 **패닉셀 구간에서 절대 매도하지 않고 홀딩**하며,
**역프리미엄 구간에서 추가 매수**하여 입출금 재개 후 글로벌 수렴 시점에 수익을 확정한다.

## 핵심 원리
```
현물 홀딩이므로 패닉셀 구간에서 안 팔면 손실 없음 (종이 손실만)
입출금 재개 → 아비트라지 유입 → 글로벌 가격 수렴 → 최악에도 본전
역프리미엄 구간에서 추가 매수하면 오히려 더 벌 수 있음 (+15~25%)
```

## 검증 사례
- 2025.11.27 업비트 솔라나 해킹 445억원
  - 패닉셀 발생 → 입출금 전체 중단 → 이후 재개 → 수렴
- FLOW 보안 사고 2025.12.27
  - DAXA 거래위험 경고 → -40% 급락 → 입출금 정지

## 실행 단계

### Phase 0: 해킹/사고 감지 (05번에서 시그널 수신)
```
05-hot-wallet-abnormal-withdrawal 또는
03-exchange-announcement-monitor (유의종목/DAXA 경고) 시그널 수신

즉시 조치:
  - 신규 롱 진입 절대 금지
  - 기존 포지션 있으면 홀딩 모드 전환
  - 해외 숏 유지 (글로벌 하락 헤지)
```

### Phase 1: 패닉셀 구간 (수시간~1일)
```
국내 가격 급락, 글로벌도 하락 가능

행동:
  - 현물 매도 금지 (절대 규칙)
  - 해외 숏 유지 → 글로벌 하락분 수익
  - 프리미엄 모니터링 강화 (12번)

모니터링:
  - 국내 가격 vs 글로벌 가격 괴리 추적
  - 패닉셀 거래량 추이
  - 역프리미엄 발생 여부
```

### Phase 2: 역프리미엄 구간 (패닉셀 심화 시)
```
국내 가격 < 글로벌 가격 = 역프리미엄 발생
공포에 의한 비이성적 매도 → 국내가 글로벌보다 싸짐

추매 기준:
  역프리미엄 -5%: 추매 준비 (소규모, 전체의 20%)
  역프리미엄 -10%: 1차 추매 (전체의 30%)
  역프리미엄 -15%: 2차 추매 (전체의 30%)
  역프리미엄 -20% 이상: 3차 추매 (잔여 전체)

추매 시 해외 숏 추가:
  추매 수량만큼 해외 숏 추가 → 델타 뉴트럴 유지
  역프리미엄 수렴 시 추매분 수익 = 역프리미엄 폭
```

### Phase 3: 안정화 구간
```
패닉셀 종료, 거래량 급감, 변동성 축소

행동:
  - 포지션 홀딩 유지
  - 입출금 재개 공지 모니터링
  - 펀딩비 누적 체크 (16번)
```

### Phase 4: 입출금 재개 → 수렴 → 청산
```
입출금 재개 공지 감지 시:
  1. 아비트라지 봇 유입 예상 → 글로벌 가격으로 수렴
  2. 프리미엄/역프리미엄 → 0% 수렴
  3. 수렴 확인 후 13-simultaneous-liquidation으로 청산

청산 타이밍:
  - 재개 직후 급격한 수렴 시: 수렴 완료 후 청산
  - 점진적 수렴 시: 역프리미엄 → 0% 도달 시 청산
  - 프리미엄 반전 (역프리미엄 → 양의 프리미엄): 프리미엄 피크에서 청산
```

## P&L 시나리오

### 기존 포지션 있을 때 해킹 발생
```
진입: 국내 롱 100원, 해외 숏 $0.07

해킹 직후:
  국내 70원 (-30%), 해외 $0.065 (-7%)
  국내 PnL: -30% (종이)
  해외 PnL: +7%

Phase 2 추매 (역프리미엄 -10%):
  국내 추매 65원, 해외 추가 숏 $0.065

재개 후 수렴 (글로벌 $0.063 수준):
  국내: 85원으로 수렴 (추매분 +30%)
  해외: 숏 청산 ($0.063, 원래 +10%, 추가 +3%)

순수익: 추매분 역프리미엄 캡처 +15~25%
```

### 포지션 없을 때 해킹 감지
```
Phase 1: 진입 금지
Phase 2: 역프리미엄 발생 시 신규 진입
  국내 롱 (역프리미엄 가격) + 해외 숏
  재개 후 수렴 → 역프리미엄 폭 = 수익
```

## 출력
```json
{
  "scenario": "hack_holding",
  "ticker": "SOL",
  "phase": "phase_2_reverse_premium",
  "current_premium_pct": -12.5,
  "action": "additional_buy",
  "additional_buy": {
    "qty": 50,
    "target_price_krw": 180000,
    "additional_hedge_qty": 50,
    "hedge_exchange": "binance"
  },
  "existing_position": {
    "domestic_qty": 100,
    "domestic_avg_price": 210000,
    "overseas_short_qty": 100,
    "paper_loss_pct": -14.3,
    "actual_loss": 0
  },
  "exit_plan": "wait_for_resumption_then_converge"
}
```

## 데이터 의존성
- `05-hot-wallet-abnormal-withdrawal`: 해킹 시그널
- `03-exchange-announcement-monitor`: 유의종목/DAXA 경고, 재개 공지
- `12-premium-realtime-tracker`: 역프리미엄 모니터링
- `09-delta-neutral-position`: 추매 포지션 구축
- `13-simultaneous-liquidation`: 최종 청산
- `16-funding-rate-tracker`: 장기 홀딩 시 펀딩비

## 절대 규칙
1. **패닉셀 구간에서 현물 매도 금지** — 가장 중요한 규칙
2. 역프리미엄 추매 시 반드시 해외 숏 추가 (델타 뉴트럴 유지)
3. 상장폐지 가능성 있는 코인은 이 전략 적용 불가 (DAXA 경고 코인)
4. 입출금 재개 확인 전까지 청산 금지
