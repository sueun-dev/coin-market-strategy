# 01. Governance Proposal Monitor Strategy

## Purpose
Detect network upgrade schedules **3 days to several weeks before** exchange announcements by monitoring on-chain governance votes.
Upgrade -> deposit/withdrawal suspension -> closed economy -> premium generation. This system captures the very starting point of this chain.

## Verified Lead Times
- **3 days ~ several weeks**
- ATOM v25.3.0: Proposal #1021 submitted 1/6 -> Upbit announcement 1/9+ (3+ days)
- SEI v2: Proposal #55 announced 5/20 -> Upbit deposit/withdrawal suspension 5/27 (7 days)

## Target Chains
| Chain | Governance Type | Endpoint |
|-------|----------------|----------|
| ATOM (Cosmos Hub) | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| SEI | Cosmos SDK Gov + SIP | `/cosmos/gov/v1/proposals` |
| INJ (Injective) | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| OSMO (Osmosis) | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| KAVA | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| BAND | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| Polygon | PIP (Polygon Improvement Proposal) | Governance Forum RSS |
| Other Cosmos SDK chains | Same | Per-chain RPC |

## Core Logic

### 1. Proposal Polling
```
Every 10 minutes:
  Each Cosmos SDK chain RPC -> GET /cosmos/gov/v1/proposals?proposal_status=PROPOSAL_STATUS_VOTING_PERIOD
  + GET /cosmos/gov/v1/proposals?proposal_status=PROPOSAL_STATUS_PASSED
```

### 2. Upgrade Proposal Filtering
```
Filter conditions:
  - msg_type == "SoftwareUpgradeProposal" or "MsgSoftwareUpgrade"
  - title/description contains "upgrade", "hard fork", "v[number]"
  - plan.height (upgrade block height) exists
```

### 3. Upgrade Time Estimation
```
Estimated time = (target_block_height - current_block_height) x avg_block_time
avg_block_time = average of last 1000 blocks
```

### 4. Signal Emission Conditions
```
IF new SoftwareUpgradeProposal detected
  AND the coin is listed on Upbit/Bithumb
  AND vote approval rate > 50% (or already passed)
THEN:
  Emit signal -> forward to 08-signal-direction-engine
  Included data: {
    chain, coin_ticker, proposal_id,
    affected_tickers, exchanges_affected,
    upgrade_block_height, estimated_time,
    vote_yes_ratio, proposal_status
  }
```

### 5. Polygon PIP Separate Handling
```
Subscribe to Polygon Governance Forum RSS
Keywords: "PIP", "upgrade", "hardfork", "migration"
When new PIP detected, emit signal in the same manner
```

## Data Dependencies
- `19-data-registry`: Per-chain RPC endpoints, listed coin inventory
- `07-target-coin-filter`: Target suitability check before signal emission

## Output
```json
{
  "signal_type": "governance_upgrade",
  "chain": "cosmos",
  "ticker": "ATOM",
  "affected_tickers": ["ATOM"],
  "exchanges_affected": ["upbit", "bithumb"],
  "proposal_id": 1021,
  "upgrade_height": 29288700,
  "estimated_time": "2026-01-09T14:00:00Z",
  "lead_time_hours": 72,
  "vote_yes_pct": 99.82,
  "confidence": "high",
  "detected_at": "2026-01-06T10:00:00Z"
}
```

## Monitoring Frequency
- Cosmos SDK chains: **10-minute interval** polling
- Polygon Forum: **30-minute interval** RSS check
- Proposals in voting period: frequency increased to **5-minute interval**

## Edge Cases
- Proposal passed then cancelled/postponed: emit signal cancellation
- Recalculate estimated time when block time changes drastically
- RPC node down: automatic failover to backup RPC (minimum 2 nodes/chain)

---

# 01. 거버넌스 프로포절 모니터 전략서

## 목적
온체인 거버넌스 투표를 통해 네트워크 업그레이드 일정을 거래소 공지보다 **3일~수주 전에** 사전 감지한다.
업그레이드 → 입출금 정지 → 폐쇄경제 → 프리미엄 발생. 이 체인의 시작점을 가장 먼저 잡는 시스템.

## 검증된 리드타임
- **3일 ~ 수주**
- ATOM v25.3.0: 프로포절 #1021 1/6 제출 → 업비트 공지 1/9+ (3일+)
- SEI v2: 프로포절 #55 5/20 발표 → 업비트 입출금 중단 5/27 (7일)

## 대상 체인
| 체인 | 거버넌스 타입 | 엔드포인트 |
|------|-------------|-----------|
| ATOM (Cosmos Hub) | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| SEI | Cosmos SDK Gov + SIP | `/cosmos/gov/v1/proposals` |
| INJ (Injective) | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| OSMO (Osmosis) | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| KAVA | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| BAND | Cosmos SDK Gov | `/cosmos/gov/v1/proposals` |
| Polygon | PIP (Polygon Improvement Proposal) | Governance Forum RSS |
| 기타 Cosmos SDK 체인 | 동일 | 체인별 RPC |

## 핵심 로직

### 1. 프로포절 폴링
```
매 10분마다:
  각 Cosmos SDK 체인 RPC → GET /cosmos/gov/v1/proposals?proposal_status=PROPOSAL_STATUS_VOTING_PERIOD
  + GET /cosmos/gov/v1/proposals?proposal_status=PROPOSAL_STATUS_PASSED
```

### 2. 업그레이드 프로포절 필터링
```
필터 조건:
  - msg_type == "SoftwareUpgradeProposal" 또는 "MsgSoftwareUpgrade"
  - title/description에 "upgrade", "hard fork", "v숫자" 포함
  - plan.height (업그레이드 블록높이) 존재
```

### 3. 업그레이드 시간 예측
```
예상 시간 = (target_block_height - current_block_height) × avg_block_time
avg_block_time = 최근 1000 블록 평균
```

### 4. 시그널 발행 조건
```
IF 신규 SoftwareUpgradeProposal 감지
  AND 해당 코인이 업비트/빗썸 상장
  AND 투표 찬성률 > 50% (또는 이미 통과)
THEN:
  시그널 발행 → 08-signal-direction-engine으로 전달
  포함 데이터: {
    chain, coin_ticker, proposal_id,
    affected_tickers, exchanges_affected,
    upgrade_block_height, estimated_time,
    vote_yes_ratio, proposal_status
  }
```

### 5. Polygon PIP 별도 처리
```
Polygon Governance Forum RSS 구독
키워드: "PIP", "upgrade", "hardfork", "migration"
새 PIP 감지 시 동일하게 시그널 발행
```

## 데이터 의존성
- `19-data-registry`: 체인별 RPC 엔드포인트, 상장 코인 목록
- `07-target-coin-filter`: 시그널 발행 전 타겟 적합성 체크

## 출력
```json
{
  "signal_type": "governance_upgrade",
  "chain": "cosmos",
  "ticker": "ATOM",
  "affected_tickers": ["ATOM"],
  "exchanges_affected": ["upbit", "bithumb"],
  "proposal_id": 1021,
  "upgrade_height": 29288700,
  "estimated_time": "2026-01-09T14:00:00Z",
  "lead_time_hours": 72,
  "vote_yes_pct": 99.82,
  "confidence": "high",
  "detected_at": "2026-01-06T10:00:00Z"
}
```

## 모니터링 주기
- Cosmos SDK 체인: **10분 간격** 폴링
- Polygon Forum: **30분 간격** RSS 체크
- 투표 진행 중 프로포절: **5분 간격**으로 빈도 상향

## 엣지 케이스
- 프로포절 통과 후 취소/연기: 시그널 취소 발행
- 블록타임 급변 시 예상 시간 재계산
- RPC 노드 다운: 백업 RPC 자동 전환 (최소 2개 노드/체인)
