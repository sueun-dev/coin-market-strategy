# 05. Hot Wallet Abnormal Withdrawal Detection Strategy

## Purpose
Detect **large fund movements (hacking indicators)** from Upbit/Bithumb hot wallets to unidentified external wallets.
Hack occurrence -> exchange-wide deposit/withdrawal suspension -> closed economy -> panic sell -> reverse premium buying opportunity.
Can detect **4-8 hours faster** than official exchange announcements.

## Verified Lead Times
- **4~8 hours**
- 2025.11.27 Upbit Solana hack 44.5 billion KRW:
  - 04:42 On-chain tx occurred
  - 08:55 Full deposit/withdrawal suspension announcement (4 hours later)
  - 12:33 Public disclosure (8 hours later)
  - Lookonchain, PeckShield tweeted alerts within minutes of tx occurrence

## Monitoring Targets

### Upbit Hot Wallets (Per Chain)
| Chain | Address Labeling Source |
|-------|----------------------|
| Ethereum | Arkham Intelligence, Etherscan Labels |
| Solana | Solscan Labels, Arkham |
| Bitcoin | Blockchain.com Labels, Arkham |
| Tron | Tronscan Labels |
| Other EVM | Arkham, respective Explorer Labels |

### Bithumb Hot Wallets (Same Method)
- Same per-chain hot wallet address labeling

## Core Logic

### 1. Hot Wallet Withdrawal Monitoring
```
For each chain's exchange hot wallet address:
  - Poll latest tx via Etherscan API / Solscan API / multi-chain RPC
  - When withdrawal tx detected, verify recipient address
```

### 2. Abnormal Withdrawal Criteria
```
Abnormal judgment conditions (OR):
  1. Single tx amount > average withdrawal x 10
  2. Cumulative withdrawals within 1 hour > daily average withdrawal x 5
  3. Recipient address is unlabeled/unidentified
  4. Recipient address is a mixer/Tornado/bridge contract
  5. Large transfer to newly created address (first tx)

Weighted scoring:
  - Unidentified address + large amount: high score
  - Known exchange/market maker address: low score (normal operations)
  - Mixer/privacy protocol: highest score (high hack probability)
```

### 3. External Surveillance Sources (Supplementary)
```
Twitter/X real-time monitoring (supplementary):
  - @looloconchain, @PeckShieldAlert, @zachxbt accounts
  - "hack", "exploit", "stolen", "drained" + exchange name keywords
  - Leverage their pattern of tweeting within minutes of on-chain tx

Arkham Intelligence alerts:
  - Set up alerts for large outflows from exchange-labeled addresses
```

### 4. Signal Emission
```
IF abnormal withdrawal score > threshold
THEN:
  Level 1 (Warning): Internal log + enhanced monitoring
  Level 2 (Alert): Emit signal, but position entry still prohibited
  Level 3 (Confirmed): Multiple sources confirmed -> emit hack scenario signal

Hack signal specifics:
  - Immediately prohibit long entry (panic sell expected)
  - Connect to 14-hack-scenario-holding strategy
  - Emit separate reverse premium buying signal after bottom confirmation
```

## Output
```json
{
  "signal_type": "hot_wallet_abnormal_withdrawal",
  "exchange": "upbit",
  "chain": "solana",
  "tx_hash": "5Kj3...",
  "amount_usd": 44500000000,
  "recipient_address": "0xabc...",
  "recipient_label": "unknown",
  "anomaly_score": 95,
  "anomaly_reasons": [
    "amount_10x_average",
    "unlabeled_recipient",
    "new_address"
  ],
  "severity": "critical",
  "action": "no_long_entry_wait_for_bottom",
  "confidence": "high",
  "detected_at": "2025-11-27T04:45:00Z"
}
```

## Data Dependencies
- `19-data-registry`: Exchange hot wallet address labeling DB (per chain)
- `19-data-registry`: Known address labels (exchanges, market makers, mixers, etc.)

## Monitoring Frequency
- Hot wallet tx polling: **30-second interval**
- Twitter monitoring: **1-minute interval**
- Arkham alerts: real-time (webhook)

## Edge Cases
- False positive from normal cold wallet transfer: cross-verify with 06-hot-to-cold-wallet-monitor
- Internal wallet reorganization: ignore if recipient address has same exchange label
- Tx detection delay due to chain congestion: use multiple RPC nodes
- Unidentified address later identified as legitimate: signal cancellation logic

---

# 05. 핫월렛 비정상 출금 감지 전략서

## 목적
업비트/빗썸 핫월렛에서 미확인 외부 지갑으로 **대량 자금 이동(해킹 징후)**을 감지한다.
해킹 발생 → 거래소 전체 입출금 중단 → 폐쇄경제 → 패닉셀 → 역프리미엄 추매 기회.
거래소 공식 발표보다 **4~8시간 빠르게** 감지 가능.

## 검증된 리드타임
- **4~8시간**
- 2025.11.27 업비트 솔라나 해킹 445억원:
  - 04:42 온체인 tx 발생
  - 08:55 전체 입출금 중단 공지 (4시간 후)
  - 12:33 대중 공개 (8시간 후)
  - Lookonchain, PeckShield가 tx 발생 수분 내 트위터 알림

## 모니터링 대상

### 업비트 핫월렛 (체인별)
| 체인 | 주소 라벨링 소스 |
|------|----------------|
| Ethereum | Arkham Intelligence, Etherscan Labels |
| Solana | Solscan Labels, Arkham |
| Bitcoin | Blockchain.com Labels, Arkham |
| Tron | Tronscan Labels |
| 기타 EVM | Arkham, 각 Explorer Labels |

### 빗썸 핫월렛 (동일 방식)
- 동일 체인별 핫월렛 주소 라벨링

## 핵심 로직

### 1. 핫월렛 출금 모니터링
```
각 체인별 거래소 핫월렛 주소에서:
  - Etherscan API / Solscan API / 멀티체인 RPC로 최신 tx 폴링
  - 출금 tx 감지 시 수신 주소 확인
```

### 2. 비정상 출금 판단 기준
```
비정상 판단 조건 (OR):
  1. 단일 tx 금액 > 평균 출금액 × 10
  2. 1시간 내 누적 출금 > 일평균 출금 × 5
  3. 수신 주소가 라벨링되지 않은 미확인 주소
  4. 수신 주소가 믹서/토네이도/브릿지 컨트랙트
  5. 새로 생성된 주소(first tx)로 대량 이동

가중 점수:
  - 미확인 주소 + 대량: 점수 높음
  - 기존 거래소/마켓메이커 주소: 점수 낮음 (정상 운영)
  - 믹서/프라이버시 프로토콜: 점수 최고 (해킹 확률 높음)
```

### 3. 외부 감시 소스 병행
```
트위터/X 실시간 모니터링 (보조):
  - @looloconchain, @PeckShieldAlert, @zachxbt 계정
  - "hack", "exploit", "stolen", "drained" + 거래소명 키워드
  - 이들이 온체인 tx를 수분 내 트윗하는 패턴 활용

Arkham Intelligence 알림:
  - 거래소 라벨 주소에서 대량 유출 알림 설정
```

### 4. 시그널 발행
```
IF 비정상 출금 점수 > threshold
THEN:
  Level 1 (주의): 내부 기록 + 모니터링 강화
  Level 2 (경고): 시그널 발행, 단 포지션은 아직 금지
  Level 3 (확정): 복수 소스 확인 → 해킹 시나리오 시그널 발행

해킹 시그널의 특수성:
  - 즉시 롱 진입 금지 (패닉셀 예상)
  - 14-hack-scenario-holding 전략으로 연결
  - 바닥 확인 후 역프리미엄 추매 시그널 별도 발행
```

## 출력
```json
{
  "signal_type": "hot_wallet_abnormal_withdrawal",
  "exchange": "upbit",
  "chain": "solana",
  "tx_hash": "5Kj3...",
  "amount_usd": 44500000000,
  "recipient_address": "0xabc...",
  "recipient_label": "unknown",
  "anomaly_score": 95,
  "anomaly_reasons": [
    "amount_10x_average",
    "unlabeled_recipient",
    "new_address"
  ],
  "severity": "critical",
  "action": "no_long_entry_wait_for_bottom",
  "confidence": "high",
  "detected_at": "2025-11-27T04:45:00Z"
}
```

## 데이터 의존성
- `19-data-registry`: 거래소 핫월렛 주소 라벨링 DB (체인별)
- `19-data-registry`: 알려진 주소 라벨 (거래소, 마켓메이커, 믹서 등)

## 모니터링 주기
- 핫월렛 tx 폴링: **30초 간격**
- 트위터 모니터링: **1분 간격**
- Arkham 알림: 실시간 (웹훅)

## 엣지 케이스
- 정상적인 콜드월렛 이동 오탐: 06-hot-to-cold-wallet-monitor와 교차 검증
- 내부 월렛 재편성: 수신 주소가 동일 거래소 라벨이면 무시
- 체인 혼잡으로 tx 감지 지연: 복수 RPC 노드 사용
- 미확인 주소가 사후에 정상 주소로 판명: 시그널 취소 로직
