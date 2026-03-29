# 12. 프리미엄 실시간 모니터링 전략서

## 목적
입출금 정지 후 **국내(업비트/빗썸) vs 해외(바이낸스/OKX) 가격 차이(프리미엄)**를 실시간으로 추적하여, 청산 타이밍 판단의 핵심 데이터를 제공한다.

## 프리미엄 계산

### 기본 공식
```
premium_pct = ((kr_price_usd - global_price_usd) / global_price_usd) × 100

kr_price_usd = kr_price_krw / usd_krw_rate

예시:
  업비트 TT 가격: 180원
  바이낸스 TT 가격: $0.115
  환율: 1350원/$

  kr_price_usd = 180 / 1350 = $0.1333
  premium_pct = (0.1333 - 0.115) / 0.115 × 100 = +15.9%
```

### 거래소별 프리미엄
```
upbit_premium = (upbit_price_usd - global_price_usd) / global_price_usd × 100
bithumb_premium = (bithumb_price_usd - global_price_usd) / global_price_usd × 100
```

## 핵심 로직

### 1. 실시간 가격 수집
```
데이터 소스 (1초~5초 간격):
  국내:
    - 업비트 WebSocket: wss://api.upbit.com/websocket/v1
    - 빗썸 WebSocket: wss://pubwss.bithumb.com/pub/ws

  해외:
    - 바이낸스 WebSocket: wss://stream.binance.com/ws
    - OKX WebSocket
    - Bybit WebSocket

  환율:
    - USD/KRW 실시간 (은행 매매기준율 또는 외환 API)
    - 업비트 USDT/KRW 마켓 가격 (크립토 환율)
```

### 2. 프리미엄 대시보드 데이터
```
각 포지션별 실시간 표시:
  - 현재 프리미엄 (%)
  - 프리미엄 추이 차트 (1분/5분/1시간 봉)
  - 프리미엄 최고점/최저점 (입출금 정지 이후)
  - 프리미엄 변화 속도 (1분간 변화율)
  - 호가창 상태 (bid/ask 깊이)
  - 거래량 (1분/5분 집계)
```

### 3. 프리미엄 피크 감지
```
피크 판단 지표:

1) 프리미엄율 절대값:
   > 30%: "매우 높음" 알림
   > 50%: "극단적" 알림
   > 100%: "역사적" 알림

2) 프리미엄 변화 속도 둔화:
   최근 30분 프리미엄 상승률 < 이전 30분의 50%
   → 피크 근접 시그널

3) 거래량 스파이크 후 급감:
   5분 거래량이 평균 대비 5배 이상 → 이후 급감
   → 세력 매도 시작 가능성

4) 호가창 변화:
   매도 호가 두꺼워짐 (매도 압력 증가)
   매수 호가 얇아짐
   → 피크 후 하락 시그널
```

### 4. 역프리미엄 감지 (해킹 시나리오)
```
premium_pct < 0 → 역프리미엄 발생

역프리미엄 레벨:
  -5% 이하: "역프리미엄 시작" 알림
  -10% 이하: "추매 고려" 알림 → 14-hack-scenario-holding 연동
  -20% 이하: "강력 추매 시그널"
  -30% 이하: "극단적 공포, 최대 추매"
```

### 5. 청산 추천 시그널
```
13-simultaneous-liquidation으로 전달하는 조건:

추천 청산 조건 (AND):
  - 프리미엄 > target_premium (시그널별 설정)
  - 프리미엄 변화 속도 둔화 (피크 근접)
  - 호가창에 충분한 매도 유동성 존재
  - 거래량 스파이크 발생 중

기본 target_premium:
  S등급 코인: 15% 이상
  A등급 코인: 10% 이상
  B등급 코인: 5% 이상
```

## 출력

### 실시간 데이터
```json
{
  "ticker": "TT",
  "timestamp": "2024-05-14T06:30:00Z",
  "prices": {
    "upbit_krw": 330,
    "bithumb_krw": 360,
    "binance_usd": 0.115,
    "usd_krw_rate": 1350
  },
  "premiums": {
    "upbit_pct": 112.6,
    "bithumb_pct": 131.0
  },
  "premium_peak": {
    "upbit_max_pct": 120.0,
    "bithumb_max_pct": 135.0,
    "current_vs_peak": "near_peak"
  },
  "volume": {
    "upbit_5min_krw": 500000000,
    "bithumb_5min_krw": 200000000,
    "volume_trend": "spike_then_declining"
  },
  "orderbook": {
    "upbit_ask_depth_1pct": 30000000,
    "upbit_bid_depth_1pct": 15000000,
    "sell_pressure_increasing": true
  },
  "recommendation": "consider_exit"
}
```

## 데이터 의존성
- `09-delta-neutral-position`: 활성 포지션 목록
- `13-simultaneous-liquidation`: 청산 추천 시그널 전달
- `14-hack-scenario-holding`: 역프리미엄 추매 시그널 전달
- `18-notification-system`: 알림 발송

## 모니터링 주기
- 가격 수집: **1~5초 간격** (WebSocket 실시간)
- 프리미엄 계산: **1초 간격**
- 피크 분석: **1분 간격**
- 대시보드 갱신: **실시간**

## 엣지 케이스
- 환율 급변: 원화/달러 환율 변동이 프리미엄에 영향 → 크립토 환율(USDT/KRW) 병행
- 거래소 API 장애: 가격 수집 실패 시 마지막 유효 가격 사용 + 알림
- 급격한 프리미엄 변동: 1분 내 20% 이상 변동 시 데이터 이상 여부 확인
