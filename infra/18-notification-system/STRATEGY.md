# 18. Integrated Notification System Strategy

## Purpose
**Send real-time alerts via Telegram/Discord webhooks** for all events across the entire pipeline.
Cover the full process from signal detection, position opening, premium changes, risk warnings, to liquidation via notifications.

## Notification Channels

### Telegram
```
Bot token: TELEGRAM_BOT_TOKEN
Channel breakdown:
  - #signal-alert: Detection signals (01~06)
  - #position-alert: Position open/close (09, 13)
  - #risk-alert: Risk warnings (15, 16, 17)
  - #premium-monitor: Premium changes (12)
  - #critical: Urgent alerts (hacking, liquidation risk)
```

### Discord (Optional)
```
Same channel separation by webhook URL
```

## Alert Priority

| Priority | Level | Source | Alert Method |
|---------|------|------|---------|
| P0 (Critical) | 🔴 | Hack detection, short liquidation risk Level 4, fill failure | All channels + mobile push + repeat alert (5 min) |
| P1 (High) | 🟠 | Signal detection, position open/close, premium 30%+ | Main channels + mobile alert |
| P2 (Medium) | 🟡 | Premium change, funding fee warning, short margin caution | Relevant channel only |
| P3 (Low) | 🟢 | Periodic reports, normal monitoring logs | Log channel only |

## Alert Message Formats

### Signal Detection Alert (P1)
```
🟠 [SIGNAL] Network Upgrade Detected

Coin: TT (ThunderCore)
Source: 02-GitHub Release (v4.0.0-athena)
Target Grade: S (92 points)
Lead Time: ~6 days
Recommended Exchange: Bithumb

Direction: Long + Short
Urgency: prepare (start split buying)
Estimated Size: 10M KRW (10% of capital)

Detection Time: 2024-05-08 01:00 KST
```

### Position Open Alert (P1)
```
🟠 [POSITION OPEN] Delta Neutral Constructed

Coin: TT
Domestic: Bithumb spot long 10,000 @ 150 KRW
Overseas: Binance futures short 10,000 @ $0.115
Quantity Match: ✅ 100%
Liquidation Price Buffer: 200%+ ✅

Total Deployed: 1,500,000 KRW + $345 margin
```

### Premium Alert (P2/P1)
```
🟡 [PREMIUM] TT Premium Rising

Current Premium:
  Upbit: +34.2%
  Bithumb: +89.5%

Peak: Bithumb +95.0%
Status: Rising
Recommendation: Maintain hold
```

### Hack/Critical Alert (P0)
```
🔴🔴🔴 [CRITICAL] Abnormal Hot Wallet Withdrawal Detected

Exchange: Upbit
Chain: Solana
Amount: ~44.5B KRW ($34M)
Receiving Address: Unidentified (Gq3x...)
Detection Time: 04:42 KST

⚠️ Immediate Actions:
- No new long entries
- Maintain existing position hold
- Confirm overseas short maintained
- Prepare for reverse premium additional buy
```

### Short Liquidation Risk Alert (P0)
```
🔴 [RISK] Approaching Short Liquidation Price

Coin: TT / Binance
Current Price: $0.280
Liquidation Price: $0.345
Distance: 23.2% ⚠️

Required Action:
- Immediately deposit additional margin $500
- Or consider partial short close

Auto Margin Addition: Disabled (manual confirmation required)
```

### Liquidation Complete Alert (P1)
```
🟠 [EXIT] Simultaneous Liquidation Complete

Coin: TT
Exit Premium: +107.0%

Domestic Sell: Bithumb 10,000 @ 330 KRW
Overseas Short Close: Binance @ $0.118

Net Profit: 1,759,500 KRW (+117.3%)
Execution Lag: 333ms ✅

Funding Fee Cost: -$12.50
Trading Fees: ₩15,000
Final Net Profit: 1,727,750 KRW
```

## Core Logic

### 1. Event Reception
```
All systems (01~17) publish events:
  event = {
    source: "12-premium-tracker",
    priority: "P2",
    type: "premium_update",
    data: { ... }
  }

System #18 receives → formats → sends
```

### 2. Duplicate Alert Prevention
```
Prevent duplicate sending of identical events:
  - Same ticker + same signal_type: No re-send within 1 hour
  - P0 is an exception (always send)
  - Premium alerts: Only send on 10% unit changes
```

### 3. Daily Report (P3)
```
Every day at 09:00 KST:
  - Active position summary
  - Current premium status for each position
  - Accumulated funding fees
  - List of signals being monitored
  - Number of signals detected today
```

### 4. P0 Repeat Alerts
```
On P0 event occurrence:
  Send immediately → Re-send after 5 min → Re-send after 15 min
  Stop repeat on user acknowledgment (ACK)
  ACK method: Telegram bot inline button "Confirm"
```

## Data Dependencies
- All event outputs from systems 01~17

## Configuration
```json
{
  "telegram": {
    "bot_token": "env:TELEGRAM_BOT_TOKEN",
    "channels": {
      "signal": "chat_id_1",
      "position": "chat_id_2",
      "risk": "chat_id_3",
      "premium": "chat_id_4",
      "critical": "chat_id_5"
    }
  },
  "discord": {
    "webhooks": {
      "signal": "webhook_url_1",
      "critical": "webhook_url_2"
    }
  },
  "settings": {
    "p0_repeat_interval_min": 5,
    "dedup_window_min": 60,
    "premium_alert_step_pct": 10,
    "daily_report_time": "09:00",
    "timezone": "Asia/Seoul"
  }
}
```

---

# 18. 통합 알림 시스템 전략서

## 목적
전체 파이프라인의 모든 이벤트를 **Telegram/Discord 웹훅으로 실시간 알림** 발송한다.
시그널 감지부터 포지션 오픈, 프리미엄 변화, 리스크 경고, 청산까지 전 과정을 알림으로 커버.

## 알림 채널

### Telegram
```
봇 토큰: TELEGRAM_BOT_TOKEN
채널 구분:
  - #signal-alert: 감지 시그널 (01~06)
  - #position-alert: 포지션 오픈/청산 (09, 13)
  - #risk-alert: 리스크 경고 (15, 16, 17)
  - #premium-monitor: 프리미엄 변화 (12)
  - #critical: 긴급 알림 (해킹, 청산 위험)
```

### Discord (선택)
```
웹훅 URL별 채널 분리 동일
```

## 알림 우선순위

| 우선순위 | 레벨 | 소스 | 알림 방식 |
|---------|------|------|---------|
| P0 (Critical) | 🔴 | 해킹 감지, 숏 청산 위험 Level 4, 체결 실패 | 모든 채널 + 모바일 푸시 + 반복 알림(5분) |
| P1 (High) | 🟠 | 시그널 감지, 포지션 오픈/청산, 프리미엄 30%+ | 주요 채널 + 모바일 알림 |
| P2 (Medium) | 🟡 | 프리미엄 변화, 펀딩비 경고, 숏 마진 주의 | 해당 채널만 |
| P3 (Low) | 🟢 | 정기 리포트, 정상 모니터링 로그 | 로그 채널만 |

## 알림 메시지 포맷

### 시그널 감지 알림 (P1)
```
🟠 [SIGNAL] 네트워크 업그레이드 감지

코인: TT (ThunderCore)
소스: 02-GitHub Release (v4.0.0-athena)
타겟 등급: S (92점)
리드타임: ~6일
추천 거래소: 빗썸

방향: 롱 + 숏
긴급도: prepare (분할 매수 시작)
예상 사이즈: 1000만원 (자본 10%)

감지 시각: 2024-05-08 01:00 KST
```

### 포지션 오픈 알림 (P1)
```
🟠 [POSITION OPEN] 델타 뉴트럴 구축

코인: TT
국내: 빗썸 현물 롱 10,000개 @ 150원
해외: 바이낸스 선물 숏 10,000개 @ $0.115
수량 일치: ✅ 100%
청산가 여유: 200%+ ✅

총 투입: 1,500,000원 + $345 마진
```

### 프리미엄 알림 (P2/P1)
```
🟡 [PREMIUM] TT 프리미엄 상승

현재 프리미엄:
  업비트: +34.2%
  빗썸: +89.5%

최고점: 빗썸 +95.0%
상태: 상승 중
추천: 홀딩 유지
```

### 해킹/긴급 알림 (P0)
```
🔴🔴🔴 [CRITICAL] 핫월렛 비정상 출금 감지

거래소: 업비트
체인: Solana
금액: ~445억원 ($34M)
수신 주소: 미확인 (Gq3x...)
감지 시각: 04:42 KST

⚠️ 즉시 조치:
- 신규 롱 진입 금지
- 기존 포지션 홀딩 유지
- 해외 숏 유지 확인
- 역프리미엄 추매 준비
```

### 숏 청산 위험 알림 (P0)
```
🔴 [RISK] 숏 청산가 접근

코인: TT / 바이낸스
현재가: $0.280
청산가: $0.345
거리: 23.2% ⚠️

필요 조치:
- 즉시 추가 마진 $500 입금
- 또는 일부 숏 청산 검토

자동 마진 추가: 비활성 (수동 확인 필요)
```

### 청산 완료 알림 (P1)
```
🟠 [EXIT] 동시 청산 완료

코인: TT
청산 프리미엄: +107.0%

국내 매도: 빗썸 10,000개 @ 330원
해외 숏 청산: 바이낸스 @ $0.118

순수익: 1,759,500원 (+117.3%)
실행 시차: 333ms ✅

펀딩비 비용: -$12.50
거래 수수료: ₩15,000
최종 순수익: 1,727,750원
```

## 핵심 로직

### 1. 이벤트 수신
```
모든 시스템(01~17)에서 이벤트 발행:
  event = {
    source: "12-premium-tracker",
    priority: "P2",
    type: "premium_update",
    data: { ... }
  }

18번 시스템이 수신 → 포맷팅 → 발송
```

### 2. 중복 알림 방지
```
동일 이벤트 중복 발송 방지:
  - 동일 ticker + 동일 signal_type: 1시간 내 재발송 금지
  - P0은 예외 (항상 발송)
  - 프리미엄 알림: 10% 단위 변화 시에만 발송
```

### 3. 일일 리포트 (P3)
```
매일 09:00 KST:
  - 활성 포지션 요약
  - 각 포지션 프리미엄 현황
  - 누적 펀딩비
  - 모니터링 중 시그널 목록
  - 금일 감지된 시그널 건수
```

### 4. P0 반복 알림
```
P0 이벤트 발생 시:
  즉시 발송 → 5분 후 재발송 → 15분 후 재발송
  사용자 확인(ACK) 시 반복 중단
  ACK 방법: Telegram 봇 인라인 버튼 "확인"
```

## 데이터 의존성
- 모든 시스템(01~17)의 이벤트 출력

## 설정
```json
{
  "telegram": {
    "bot_token": "env:TELEGRAM_BOT_TOKEN",
    "channels": {
      "signal": "chat_id_1",
      "position": "chat_id_2",
      "risk": "chat_id_3",
      "premium": "chat_id_4",
      "critical": "chat_id_5"
    }
  },
  "discord": {
    "webhooks": {
      "signal": "webhook_url_1",
      "critical": "webhook_url_2"
    }
  },
  "settings": {
    "p0_repeat_interval_min": 5,
    "dedup_window_min": 60,
    "premium_alert_step_pct": 10,
    "daily_report_time": "09:00",
    "timezone": "Asia/Seoul"
  }
}
```
