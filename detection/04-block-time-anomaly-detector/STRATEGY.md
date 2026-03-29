# 04. 블록 타임 이상 감지 전략서

## 목적
자체 메인넷 체인의 블록 생성 중단(chain halt)을 **수분 내에** RPC 폴링으로 감지한다.
거래소 공지보다 수시간 빠르게 감지 가능. 예고 없이 발생하는 블록 halt는 거래소가 즉시 입출금을 정지하므로 폐쇄경제 프리미엄 기회.

## 검증된 리드타임
- **수분** (거래소 공지 대비)
- DisChain 블록 중단 → 빗썸 공지 후행
- Polygon PoS 블록 생성 중단 → 업비트 POL/GMT 입출금 중단 공지 수시간 후

## 모니터링 대상
업비트/빗썸 상장 코인 중 **자체 메인넷 전체** (약 30~50개 체인)

### 주요 대상
| 체인 | RPC 타입 | 정상 블록타임 | 이상 판단 기준 |
|------|----------|-------------|--------------|
| Cosmos Hub (ATOM) | Tendermint RPC | ~6.5s | >13s |
| SEI | Tendermint RPC | ~0.4s | >0.8s |
| Injective (INJ) | Tendermint RPC | ~1.5s | >3s |
| Polygon PoS (POL) | Ethereum-compatible | ~2s | >4s |
| Flow (FLOW) | Flow Access API | ~1s | >2s |
| Solana (SOL) | Solana RPC | ~0.4s | >0.8s |
| Sui (SUI) | Sui RPC | ~0.5s | >1s |
| Aptos (APT) | Aptos REST | ~0.5s | >1s |
| 기타 | 체인별 RPC | 체인별 상이 | avg × 2 |

## 핵심 로직

### 1. 블록 타임 폴링
```
매 10초마다 각 체인 RPC 노드:
  GET latest block → timestamp, block_height 기록

블록타임 계산:
  current_block_time = latest_block.timestamp - previous_block.timestamp
```

### 2. 이동평균 블록타임 관리
```
각 체인별:
  avg_block_time = 최근 1000 블록의 평균 블록타임 (1시간마다 갱신)
  stddev = 표준편차
```

### 3. 이상 감지 기준
```
Level 1 - 주의 (Warning):
  현재 블록타임 > avg_block_time × 2
  → 내부 로그만 기록

Level 2 - 경고 (Alert):
  마지막 블록 이후 경과 시간 > avg_block_time × 5
  → 시그널 발행 준비

Level 3 - 긴급 (Critical / Chain Halt):
  마지막 블록 이후 경과 시간 > avg_block_time × 10
  또는 마지막 블록 이후 경과 시간 > 60초 (절대 기준)
  → 즉시 시그널 발행
```

### 4. 체인 halt 확인 로직
```
단순 느려짐 vs 완전 halt 구분:
  - 3회 연속 폴링(30초)에서 block_height 변화 없음 → halt 확정
  - 복수 RPC 노드에서 동일 현상 확인 → false positive 방지

halt 확정 시:
  → 즉시 시그널 발행
  → 해당 체인 모니터링 주기 10초 → 5초로 상향
  → 복구 감지 시 "chain_resumed" 시그널 발행
```

### 5. 예정된 업그레이드 halt 구분
```
01-governance-monitor 또는 02-github-release-monitor에서
이미 업그레이드 시그널이 발행된 체인의 halt:
  → "expected_halt" 태그 추가
  → 이미 포지션이 잡혀있을 수 있으므로 중복 시그널 방지

예고 없는 halt:
  → "unexpected_halt" 태그
  → 높은 긴급도로 시그널 발행
```

## 출력
```json
{
  "signal_type": "block_halt",
  "chain": "polygon_pos",
  "tickers_affected": ["POL", "GMT"],
  "last_block_height": 65432100,
  "last_block_time": "2025-12-15T10:30:00Z",
  "seconds_since_last_block": 180,
  "avg_block_time": 2.0,
  "halt_type": "unexpected",
  "severity": "critical",
  "rpc_nodes_confirming": 3,
  "confidence": "high",
  "detected_at": "2025-12-15T10:33:00Z"
}
```

## 데이터 의존성
- `19-data-registry`: 체인별 RPC 엔드포인트 목록, 평균 블록타임
- `01-governance-monitor`: 예정된 업그레이드 정보 (expected vs unexpected 구분)
- `07-target-coin-filter`: 영향받는 코인 중 타겟 적합성 체크

## 모니터링 주기
- 정상 상태: **10초 간격** 폴링
- Level 1 감지 후: **5초 간격**
- halt 확정 후: **5초 간격** (복구 감지용)

## 엣지 케이스
- RPC 노드 자체 다운 vs 체인 halt: 복수 노드(최소 2개)로 교차 확인
- 블록타임 급격한 변화 (네트워크 혼잡): stddev 기반 판단
- 단일 블록만 지연: 3회 연속 확인 필수
- 복구 후 재halt: 복구 시그널 발행 후에도 모니터링 강화 유지 (30분간)
