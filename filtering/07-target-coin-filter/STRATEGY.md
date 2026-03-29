# 07. Target Coin Auto-Filtering Engine Strategy

## Purpose
When a signal is generated from the detection systems (01~06), this engine automatically evaluates and scores whether the coin is a **target capable of generating alpha**.
Core principle: **The lighter the coin, the greater the alpha.** Low trading volume does not mean no alpha — rather, low trading volume = maximized closed economy effect = maximum alpha.

## Filter Conditions and Priorities

### Tier 1 (Top Priority Target)
| Condition | Criteria | Score |
|-----------|----------|-------|
| Market Cap | Below 50B KRW | +40 |
| Daily Volume | Below 1B KRW | +30 |
| Network | Independent Mainnet (own chain) | +15 |
| Korea Share | 50%+ compared to global | +10 |
| Overseas Futures | Listed on Binance/OKX futures | +5 |
| **Total 100 points → Top Priority** |

### Tier 2 (Excellent Target)
| Condition | Criteria | Score |
|-----------|----------|-------|
| Market Cap | 50B~200B KRW | +25 |
| Daily Volume | 1B~5B KRW | +20 |
| Network | Independent Mainnet | +15 |
| Korea Share | 30~50% | +7 |
| Overseas Futures | Available | +5 |

### Tier 3 (Average)
| Condition | Criteria | Score |
|-----------|----------|-------|
| Market Cap | Above 200B KRW | +10 |
| Network | ERC-20 etc. (rarely suspended) | +5 |

## Core Logic

### 1. Real-time Data Collection
```
Real-time refresh per coin (5-minute intervals):
  - Market Cap (CoinGecko/CoinMarketCap API)
  - 24h Volume (Upbit/Bithumb + Global)
  - Korea Volume Ratio = (Upbit + Bithumb Volume) / Global Volume
  - Overseas Futures Availability (Binance/OKX/Bybit futures listing)
  - Network Type (own mainnet vs ERC-20 vs other)
```

### 2. Score Calculation
```
score = 0

# Market cap score (lower = higher score)
if market_cap <= 500억:     score += 40
elif market_cap <= 1000억:  score += 30
elif market_cap <= 2000억:  score += 25
elif market_cap <= 5000억:  score += 15
else:                       score += 10

# Volume score (lower = higher score)
if daily_volume <= 10억:    score += 30
elif daily_volume <= 50억:  score += 20
elif daily_volume <= 100억: score += 15
else:                       score += 5

# Network score
if own_mainnet:             score += 15
elif l2_network:            score += 10
else:                       score += 5  # ERC-20 etc.

# Korea share score
if kr_volume_ratio >= 0.7:  score += 15  # Upbit exclusive listing level
elif kr_volume_ratio >= 0.5: score += 10
elif kr_volume_ratio >= 0.3: score += 7
else:                        score += 3

# Overseas futures available
if futures_available:        score += 5  # Perfect delta neutral possible
else:                        score += 0  # proxy hedge required
```

### 3. Target Grade Classification
```
S Grade (85+): Top priority target. Auto-entry candidate.
  Ex: Market cap 30B, Volume 500M, own mainnet, Korea share 60%

A Grade (65~84): Excellent target. Enter when signal strength is high.
  Ex: Market cap 80B, Volume 2B, own mainnet

B Grade (45~64): Average. Enter after confirming signal strength + additional conditions.
  Ex: Market cap 300B, own mainnet, Korea share 40%

C Grade (44 or below): Low. Enter only in special cases.
  Ex: BTC, ETH and other large-cap coins
```

### 4. Special Condition Bonuses
```
Upbit exclusive listing: score += 10 (maximized closed economy effect)
Bithumb liquidity << Upbit: Add Bithumb position recommendation tag
Deposit/withdrawal suspension history in last 6 months: score += 5 (recurrence possibility)
```

## Output
```json
{
  "ticker": "TT",
  "coin_name": "ThunderCore",
  "score": 92,
  "grade": "S",
  "details": {
    "market_cap_krw": 84000000000,
    "market_cap_score": 40,
    "daily_volume_krw": 3000000000,
    "volume_score": 30,
    "network_type": "own_mainnet",
    "network_score": 15,
    "kr_volume_ratio": 0.45,
    "kr_ratio_score": 7,
    "futures_available": false,
    "futures_score": 0,
    "bonus": {
      "upbit_exclusive": false,
      "bithumb_lower_liquidity": true,
      "recent_suspension_history": true
    }
  },
  "recommended_exchange": "bithumb",
  "hedge_type": "proxy_hedge",
  "proxy_hedge_ticker": null
}
```

## Data Dependencies
- `19-data-registry`: Listed coin list, network types, overseas futures list
- `10-proxy-hedge-mapper`: Proxy hedge target lookup when futures are not supported

## Refresh Cycle
- Per-coin score calculation: **5-minute interval** real-time refresh
- Listed coin list: **Once daily** refresh
- Network type: **Manual management** (update on new listings)

## Edge Cases
- Newly listed coins: Conservative evaluation when data is insufficient (default B grade)
- Sudden market cap/volume changes: Compare current value with 7-day average, alert on sudden changes
- Coins scheduled for delisting: Separate flag when designated as caution stock (handled by module 08)

---

# 07. 타겟 코인 자동 필터링 엔진 전략서

## 목적
감지 시스템(01~06)에서 시그널이 발생하면, 해당 코인이 **알파를 낼 수 있는 타겟인지** 자동으로 평가/점수화한다.
핵심 원리: **가벼울수록 알파가 크다.** 거래량 미미 = 알파 없음이 아니라, 거래량 미미 = 폐쇄경제 효과 극대화 = 알파 최대.

## 필터 조건 및 우선순위

### Tier 1 (최우선 타겟)
| 조건 | 기준 | 점수 |
|------|------|------|
| 시총 | 500억원 이하 | +40 |
| 일 거래량 | 10억원 이하 | +30 |
| 네트워크 | 독자 메인넷 (자체 체인) | +15 |
| 한국 비중 | 글로벌 대비 50% 이상 | +10 |
| 해외 선물 | 바이낸스/OKX 선물 존재 | +5 |
| **총점 100점 → 최우선** |

### Tier 2 (우수 타겟)
| 조건 | 기준 | 점수 |
|------|------|------|
| 시총 | 500억~2000억원 | +25 |
| 일 거래량 | 10억~50억원 | +20 |
| 네트워크 | 독자 메인넷 | +15 |
| 한국 비중 | 30~50% | +7 |
| 해외 선물 | 존재 | +5 |

### Tier 3 (보통)
| 조건 | 기준 | 점수 |
|------|------|------|
| 시총 | 2000억원 이상 | +10 |
| 네트워크 | ERC-20 등 (드물게 정지) | +5 |

## 핵심 로직

### 1. 실시간 데이터 수집
```
각 코인별 실시간 갱신 (5분 간격):
  - 시총 (CoinGecko/CoinMarketCap API)
  - 24h 거래량 (업비트/빗썸 + 글로벌)
  - 한국 거래량 비중 = (업비트 + 빗썸 거래량) / 글로벌 거래량
  - 해외 선물 존재 여부 (바이낸스/OKX/Bybit 선물 목록)
  - 네트워크 타입 (자체 메인넷 vs ERC-20 vs 기타)
```

### 2. 점수 산출
```
score = 0

# 시총 점수 (낮을수록 높은 점수)
if market_cap <= 500억:     score += 40
elif market_cap <= 1000억:  score += 30
elif market_cap <= 2000억:  score += 25
elif market_cap <= 5000억:  score += 15
else:                       score += 10

# 거래량 점수 (적을수록 높은 점수)
if daily_volume <= 10억:    score += 30
elif daily_volume <= 50억:  score += 20
elif daily_volume <= 100억: score += 15
else:                       score += 5

# 네트워크 점수
if own_mainnet:             score += 15
elif l2_network:            score += 10
else:                       score += 5  # ERC-20 등

# 한국 비중 점수
if kr_volume_ratio >= 0.7:  score += 15  # 업비트 단독 상장급
elif kr_volume_ratio >= 0.5: score += 10
elif kr_volume_ratio >= 0.3: score += 7
else:                        score += 3

# 해외 선물 존재
if futures_available:        score += 5  # 완벽한 델타 뉴트럴 가능
else:                        score += 0  # proxy hedge 필요
```

### 3. 타겟 등급 분류
```
S등급 (85+): 최우선 타겟. 자동 진입 후보.
  예: 시총 300억, 거래량 5억, 독자 메인넷, 한국 비중 60%

A등급 (65~84): 우수 타겟. 시그널 강도 높으면 진입.
  예: 시총 800억, 거래량 20억, 독자 메인넷

B등급 (45~64): 보통. 시그널 강도 + 추가 조건 확인 후 진입.
  예: 시총 3000억, 독자 메인넷, 한국 비중 40%

C등급 (44 이하): 낮음. 특별한 경우에만 진입.
  예: BTC, ETH 등 대형 코인
```

### 4. 특수 조건 보너스
```
업비트 단독 상장: score += 10 (폐쇄경제 효과 극대화)
빗썸 유동성 << 업비트: 빗썸 포지션 추천 태그 추가
최근 6개월 입출금 정지 이력 있음: score += 5 (재발 가능성)
```

## 출력
```json
{
  "ticker": "TT",
  "coin_name": "ThunderCore",
  "score": 92,
  "grade": "S",
  "details": {
    "market_cap_krw": 84000000000,
    "market_cap_score": 40,
    "daily_volume_krw": 3000000000,
    "volume_score": 30,
    "network_type": "own_mainnet",
    "network_score": 15,
    "kr_volume_ratio": 0.45,
    "kr_ratio_score": 7,
    "futures_available": false,
    "futures_score": 0,
    "bonus": {
      "upbit_exclusive": false,
      "bithumb_lower_liquidity": true,
      "recent_suspension_history": true
    }
  },
  "recommended_exchange": "bithumb",
  "hedge_type": "proxy_hedge",
  "proxy_hedge_ticker": null
}
```

## 데이터 의존성
- `19-data-registry`: 상장 코인 목록, 네트워크 타입, 해외 선물 목록
- `10-proxy-hedge-mapper`: 선물 미지원 시 proxy hedge 대상 조회

## 갱신 주기
- 코인별 점수 산출: **5분 간격** 실시간 갱신
- 상장 코인 목록: **일 1회** 갱신
- 네트워크 타입: **수동 관리** (신규 상장 시 업데이트)

## 엣지 케이스
- 신규 상장 코인: 데이터 부족 시 보수적 평가 (B등급 기본)
- 시총/거래량 급변: 직전 7일 평균과 현재 값 비교, 급변 시 알림
- 상장폐지 예정 코인: 유의종목 지정 시 별도 플래그 (08번에서 처리)
