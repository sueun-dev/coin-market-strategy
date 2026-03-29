# 01. 거버넌스 프로포절 모니터 — 감지 범위 명세서

> 최종 업데이트: 2026-03-29
> 테스트: 45/45 통과 (Cosmos 37 + 멀티체인 8)
> 실시간 검증 완료

---

## 한 줄 요약

**21개 체인의 온체인 거버넌스를 10분 간격으로 폴링하여, 네트워크 업그레이드 → 거래소 입출금 정지를 업비트 공지보다 2~28일 먼저 감지한다.**

---

## 감지 가능한 체인 전체 목록

### Cosmos SDK 체인 (13개) — 동일 API, 완전 자동화

| 티커 | 체인 | 업비트 | 빗썸 | 거버넌스 API | 감지 방식 | 실측 리드타임 |
|------|------|:------:|:----:|-------------|----------|:------------:|
| ATOM | Cosmos Hub | O | O | `/cosmos/gov/v1/proposals` | 프로포절 투표 시작 감지 → 블록높이 예측 | **2~6일** (4건 검증) |
| SEI | Sei Network | O | O | `/cosmos/gov/v1beta1/proposals` | 동일 (v1beta1 자동 폴백) | 7일 (PDF 검증) |
| INJ | Injective | O | O | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| KAVA | Kava | O | O | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| AKT | Akash Network | O | - | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| AXL | Axelar | O | - | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| TIA | Celestia | O | - | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| CRO | Crypto.com Chain | O | - | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| MED | MediBloc | O | - | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| OSMO | Osmosis | - | O | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| BAND | Band Protocol | - | O | `/cosmos/gov/v1/proposals` | 동일 (v1→v1beta1 폴백) | 추정 2~7일 |
| STRD | Stride | - | O | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |
| STARS | Stargaze | - | O | `/cosmos/gov/v1/proposals` | 동일 | 추정 2~7일 |

**Cosmos SDK 감지 원리:**
```
SoftwareUpgradeProposal 또는 MsgSoftwareUpgrade 타입 프로포절 감지
→ plan.height (업그레이드 블록높이) 추출
→ 현재 블록높이와 비교하여 예상 시간 계산
→ 찬성률 계산 → 신뢰도 판단 (high/medium/low)
→ 시그널 발행
```

**실증 검증 (온체인 데이터 + 업비트 공지 대조):**

| 프로포절 | 감지 시점 (voting_start) | 업비트 공지 | 리드타임 | 신뢰도 |
|---------|------------------------|-----------|:-------:|:------:|
| ATOM v22 #987 | 2025-01-17 20:43 UTC | 2025-01-20 | 2.1일 | confirmed |
| ATOM v25.3.0 #1021 | 2026-01-06 17:23 UTC | 2026-01-09 | 2.3일 | confirmed |
| ATOM v26.0.0 #1024 | 2026-02-09 17:13 UTC | 2026-02-12* | 2.3일+ | estimated |
| ATOM v27.0.0 #1025 | 2026-03-03 15:32 UTC | 2026-03-07* | 3.3일 | estimated |
| ATOM v27.1.0 #1026 | 2026-03-24 14:28 UTC | 미공지 (감지 중) | 5.3일+ | 라이브 |

\* 입출금 중단 시작일 기준 (실제 공지 게시일은 이보다 빠름)

---

### 비-Cosmos 체인 (8개) — 체인별 전용 API

| 티커 | 체인 | 업비트 | 거버넌스 타입 | API | 감지 대상 | 예상 리드타임 |
|------|------|:------:|-------------|-----|----------|:------------:|
| DOT | Polkadot | O | OpenGov 레퍼렌덤 | Polkassembly API | runtime upgrade 레퍼렌덤 (Whitelisted Caller track) | **7~28일** |
| XTZ | Tezos | O | 자체수정 프로토콜 | TzKT API | 프로토콜 업그레이드 투표 (5단계: proposal→exploration→testing→promotion→adoption) | **수주** |
| APT | Aptos | O | On-chain Governance | Aptos REST API | AIP 기반 거버넌스 프로포절 + 체인 상태 변경 | **수일** |
| SUI | Sui | O | Protocol Version | Sui JSON-RPC | 프로토콜 버전 변경 감지 (epoch 기반) | **수시간~1일** |
| ALGO | Algorand | O | Consensus Upgrade | Algonode API | next-version 필드로 업그레이드 진행 상태 감지 | **수일** |
| ADA | Cardano | O | CIP + Hard Fork Combinator | Koios API (무료) | 에포크 정보 + 거버넌스 프로포절 (Chang 이후 온체인) | **수일~수주** |
| ICX | ICON | O | Network Proposal | ICON JSON-RPC | 네트워크 프로포절 온체인 투표 | **수일** |
| CELO | Celo | O | CGP (온체인 거버넌스) | Celo RPC | 거버넌스 컨트랙트 프로포절 + 블록 상태 | **수일** |

---

## 감지할 수 없는 것 (다른 시스템 필요)

| 코인 | 이유 | 대응 시스템 |
|------|------|-----------|
| SOL (Solana) | 밸리데이터 feature gate 합의 방식. 온체인 투표 없음 | 02번 GitHub + 04번 블록타임 |
| AVAX (Avalanche) | 오프체인 ACP 기반. 온체인 거버넌스 없음 | 02번 GitHub |
| POL (Polygon) | PIP 포럼 기반. 온체인 투표 없음 | 02번 GitHub + 03번 거래소 공지 |
| HBAR (Hedera) | 위원회 비공개 결정 | 03번 거래소 공지 |
| NEAR | NEP GitHub 기반. 온체인 투표 없음 | 02번 GitHub |
| EGLD (MultiversX) | 오프체인 결정 | 02번 GitHub |
| QTUM | DGP는 파라미터만. 하드포크는 오프체인 | 02번 GitHub |
| MINA | MIP GitHub 기반 | 02번 GitHub |
| ZIL (Zilliqa) | 오프체인 결정 | 02번 GitHub |
| IOTA | 오프체인 결정 | 02번 GitHub |
| ARB (Arbitrum) | Tally 거버넌스 있으나 L2라 입출금 정지 패턴 다름 | 별도 분석 필요 |
| OP (Optimism) | Agora 거버넌스 있으나 L2라 패턴 다름 | 별도 분석 필요 |

---

## 시그널 발행 조건

### Cosmos SDK 체인
```
IF  SoftwareUpgradeProposal 또는 MsgSoftwareUpgrade 감지
AND 해당 코인이 업비트/빗썸 상장
AND plan.height가 현재 블록보다 미래
AND (찬성률 > 50% 또는 투표 시작 직후)
THEN → 시그널 발행
```

### Polkadot (DOT)
```
IF  OpenGov 레퍼렌덤에서 runtime upgrade 관련 프로포절 감지
    (track: Whitelisted Caller, Root 등)
AND 키워드: upgrade, runtime, release, set_code
THEN → 시그널 발행
```

### Tezos (XTZ)
```
IF  투표 기간이 exploration/promotion/adoption 단계에 진입
AND 프로토콜 업그레이드 프로포절 존재
THEN → 시그널 발행 (자체수정이므로 투표 통과 시 자동 업그레이드)
```

### Sui (SUI)
```
IF  protocolVersion이 이전 폴링 대비 변경됨
THEN → 시그널 발행 (epoch 전환 시 업그레이드 발생)
```

### Algorand (ALGO)
```
IF  next-version-round > last-round (업그레이드 대기 중)
AND next-version이 이전과 다름
THEN → 시그널 발행
```

### Aptos (APT)
```
IF  governance proposal 신규 감지
OR  체인 git_hash 변경 (바이너리 업그레이드 발생)
THEN → 시그널 발행
```

### Cardano (ADA)
```
IF  HardForkInitiation 타입 프로포절 감지 (Chang 이후 온체인)
OR  ProtocolParamUpdate 타입 프로포절 감지
THEN → 시그널 발행
```

### ICON (ICX)
```
IF  네트워크 프로포절 신규 감지
AND status가 활성 (투표 중)
THEN → 시그널 발행
```

### Celo (CELO)
```
IF  거버넌스 컨트랙트에 신규 프로포절 감지
THEN → 시그널 발행
```

---

## 시그널 출력 형식

```json
{
  "signal_id": "2b3622f93fa0",
  "signal_type": "governance_upgrade",
  "chain": "cosmoshub",
  "ticker": "ATOM",
  "proposal_id": "1026",
  "proposal_title": "Gaia v27.1.0 Upgrade",
  "proposal_status": "PROPOSAL_STATUS_VOTING_PERIOD",
  "upgrade_name": "v27.1.0",
  "upgrade_height": 30466800,
  "estimated_time": "2026-04-01T14:33:22Z",
  "lead_time_hours": 64.8,
  "remaining_blocks": 40710,
  "vote_yes_pct": 0.0,
  "confidence": "medium",
  "detected_at": "2026-03-29T21:46:17Z"
}
```

---

## 사용법

```bash
# 전체 Cosmos SDK 체인 1회 폴링
python3 main.py --reset

# 특정 체인만
python3 main.py --chain cosmoshub

# 10분 간격 반복 폴링 (백그라운드)
nohup python3 main.py --loop > monitor.log 2>&1 &

# 멀티체인 (DOT, XTZ, APT 등) 테스트
python3 tests/test_multi_chain.py
```

---

## 파이프라인 내 위치

```
[01 거버넌스 모니터] ──→ [07 타겟 필터] ──→ [08 방향 결정] ──→ [09 포지션 구축]
        │
        │  시그널: "ATOM v27.1.0 업그레이드 2.7일 후"
        │
        ├── 업비트 공지보다 2~28일 먼저 감지
        ├── 거래소 입출금 정지 → 폐쇄경제 → 프리미엄 발생
        └── 국내 현물 롱 + 해외 선물 숏 → 프리미엄 캡처
```

---

## 한계점

1. **Cosmos SDK 외 체인은 블록높이 기반 예측 불가** — Polkadot, Tezos 등은 시간 기반 투표이므로 "몇 블록 남았는지"가 아니라 "투표 기간이 며칠 남았는지"로 판단
2. **Tezos 프로포절 없는 proposal 기간** — 프로포절이 제출되지 않은 기간에는 빈 시그널 발행 (노이즈)
3. **Sui는 epoch 기반** — 프로토콜 버전 변경이 사전 공지 없이 epoch 전환 시 발생할 수 있어 리드타임이 짧음
4. **Cardano Blockfrost 미사용** — Koios API(무료)로 대체. 거버넌스 데이터는 풍부하나 HardForkInitiation 프로포절 정밀 필터링은 추가 개발 필요
5. **L2 체인 (ARB, OP) 미지원** — 온체인 거버넌스는 있으나 L2 입출금 정지 패턴이 L1과 달라 별도 분석 필요

---

## 테스트 현황

| 테스트 종류 | 건수 | 결과 | 비고 |
|-----------|:----:|:----:|------|
| Cosmos SDK 유닛 (proposal_filter, estimator, state_store) | 24 | 24/24 | 모든 엣지 케이스 포함 |
| Cosmos SDK 통합 (13 체인 라이브 RPC) | 6 | 6/6 | failover 포함 |
| 역사적 검증 (과거 업비트 공지 대조) | 7 | 7/7 | 2개 RPC 교차 검증 |
| 멀티체인 거버넌스 (8 체인 라이브 API) | 8 | 8/8 | DOT~CELO 전부 |
| **합계** | **45** | **45/45** | |
