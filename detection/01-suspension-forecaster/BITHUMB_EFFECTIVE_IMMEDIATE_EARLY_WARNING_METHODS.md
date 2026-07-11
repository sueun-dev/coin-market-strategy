# Bithumb Effective Immediate Early Warning Methods

- Generated at: 2026-07-11T19:41:53.488540+00:00
- Source file: `config/bithumb_effective_immediate_suspensions.json`
- Total cases: 29
- High pre-detectability: 24
- Medium pre-detectability: 1
- Low pre-detectability: 4

## Reading Guide

- `high`: 체인/네트워크 외부 신호만으로도 notice 이전 또는 same-minute 선포착이 가능한 유형
- `medium`: 부분 선포착은 가능하지만 거래소 stop timing까지는 미리 확정하기 어려운 유형
- `low`: 거래소 내부 지갑/월렛 점검 성격이라 외부 체인 데이터만으로는 사실상 사전 불가 유형

## Case Table

| Notice | Time (KST) | Asset Scope | Trigger | Pre-Knowability | Lead Time |
| --- | --- | --- | --- | --- | --- |
| [1652530](https://feed.bithumb.com/notice/1652530) | 2026-04-02 03:07:55 | DRIFT | security_issue | medium | 수분~수시간 전 부분 선포착 가능 |
| [1652398](https://feed.bithumb.com/notice/1652398) | 2026-03-23 23:10:34 | PEAQ | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1652352](https://feed.bithumb.com/notice/1652352) | 2026-03-20 09:33:51 | WAXP | wallet_system_check | low | 사전 예고 거의 불가, 공지와 동시 포착 |
| [1652147](https://feed.bithumb.com/notice/1652147) | 2026-02-28 15:36:52 | 0G | network_issue | high | 수초~수시간 전 선포착 가능 |
| [1652079](https://feed.bithumb.com/notice/1652079) | 2026-02-24 11:20:00 | FLOW | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1652078](https://feed.bithumb.com/notice/1652078) | 2026-02-23 20:57:49 | POKT | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1652002](https://feed.bithumb.com/notice/1652002) | 2026-02-13 08:46:44 | REI | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1651944](https://feed.bithumb.com/notice/1651944) | 2026-02-09 23:05:00 | VANA | node_sync_issue | high | 수분 전 선포착 가능 |
| [1651736](https://feed.bithumb.com/notice/1651736) | 2026-01-31 04:10:00 | USDT-Tron | wallet_system_check | low | 사전 예고 거의 불가, 공지와 동시 포착 |
| [1651542](https://feed.bithumb.com/notice/1651542) | 2026-01-19 12:55:37 | USDT-Tron | wallet_system_check | low | 사전 예고 거의 불가, 공지와 동시 포착 |
| [1651445](https://feed.bithumb.com/notice/1651445) | 2026-01-05 20:59:50 | STRK | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1650998](https://feed.bithumb.com/notice/1650998) | 2025-12-03 14:40:53 | DIS | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1650802](https://feed.bithumb.com/notice/1650802) | 2025-11-21 17:39:41 | ADA | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1650517](https://feed.bithumb.com/notice/1650517) | 2025-11-03 19:45:40 | BERA | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1650288](https://feed.bithumb.com/notice/1650288) | 2025-10-11 11:45:55 | DYDX | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1650017](https://feed.bithumb.com/notice/1650017) | 2025-09-22 18:10:39 | ADD | wallet_system_check | low | 사전 예고 거의 불가, 공지와 동시 포착 |
| [1649774](https://feed.bithumb.com/notice/1649774) | 2025-09-02 15:56:36 | STRK | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1649671](https://feed.bithumb.com/notice/1649671) | 2025-08-29 13:12:21 | ZRC | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1649062](https://feed.bithumb.com/notice/1649062) | 2025-06-26 14:04:45 | FLR | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1648710](https://feed.bithumb.com/notice/1648710) | 2025-05-31 11:43:30 | REI | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1648132](https://feed.bithumb.com/notice/1648132) | 2025-04-15 00:53:21 | ATOM | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1647038](https://feed.bithumb.com/notice/1647038) | 2025-02-18 20:00:19 | FLOW | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1646858](https://feed.bithumb.com/notice/1646858) | 2025-01-31 18:42:09 | IOTX | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1646423](https://feed.bithumb.com/notice/1646423) | 2025-01-16 02:20:40 | ZIL | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1645260](https://feed.bithumb.com/notice/1645260) | 2024-11-27 11:12:24 | STX,ALEX | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1645244](https://feed.bithumb.com/notice/1645244) | 2024-11-21 19:23:52 | SUI,LWA | block_generation_stop | high | 수초~수시간 전 선포착 가능 |
| [1645183](https://feed.bithumb.com/notice/1645183) | 2024-11-01 11:55:09 | ZETA | network_issue | high | 수초~수시간 전 선포착 가능 |
| [1645123](https://feed.bithumb.com/notice/1645123) | 2024-10-02 17:12:51 | LUNA2 | network_issue | high | 수초~수시간 전 선포착 가능 |
| [1645109](https://feed.bithumb.com/notice/1645109) | 2024-09-27 15:29:20 | ZIL | network_issue | high | 수초~수시간 전 선포착 가능 |

## Case By Case

### 1652530 DRIFT

- 사전 인지 가능도: `medium`
- 실제 맥락: Drift 프로토콜과 Solana 생태계
- 왜 이렇게 봤는가: 체인 halt가 아니라 보안 이슈이므로 프로젝트 보안 채널과 exploit 알림이 핵심이다.
- 기대 가능한 선행 시간: 수분~수시간 전 부분 선포착 가능
- 실전 룰: Drift 프로토콜과 Solana 생태계 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하므로 exploit 알림과 공식 보안 공지를 가장 먼저 봤어야 한다.
- 미리 봤어야 할 채널:
  - 프로젝트 공식 X/Discord/GitHub 보안 공지
  - 온체인 exploit alert, treasury/bridge 대량 이동 알림
  - 거래유의종목/유의촉구 공지와 빗썸 공지 피드
- 한계: 보안 이슈는 거래소 내부 판단이 섞이므로 exact stop time을 미리 맞히는 것은 어렵다.
- 원문: [1652530](https://feed.bithumb.com/notice/1652530)

### 1652398 PEAQ

- 사전 인지 가능도: `high`
- 실제 맥락: peaq 메인넷
- 왜 이렇게 봤는가: peaq 체인 블록 생성 정지 여부를 explorer와 validator 채널에서 먼저 잡았어야 한다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: peaq 메인넷에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1652398](https://feed.bithumb.com/notice/1652398)

### 1652352 WAXP

- 사전 인지 가능도: `low`
- 실제 맥락: WAX 자산의 빗썸 지갑 경로
- 왜 이렇게 봤는가: 체인 문제보다 빗썸 내부 wallet system check 성격이 강해서 거래소 신호 의존도가 높다.
- 기대 가능한 선행 시간: 사전 예고 거의 불가, 공지와 동시 포착
- 실전 룰: WAX 자산의 빗썸 지갑 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- 미리 봤어야 할 채널:
  - 빗썸 공지 피드
  - 빗썸 assetsstatus endpoint
  - 동일 자산의 반복 점검 패턴과 재개 공지 이력
- 한계: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.
- 원문: [1652352](https://feed.bithumb.com/notice/1652352)

### 1652147 0G

- 사전 인지 가능도: `high`
- 실제 맥락: 0G 메인넷
- 왜 이렇게 봤는가: explorer 최신 블록 시간과 공식 장애 공지를 보면 notice 이전에 이상 징후를 잡을 수 있는 유형이다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: 0G 메인넷의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- 미리 봤어야 할 채널:
  - 공식 explorer/RPC health, block lag, transaction failure rate
  - 공식 status/X/Discord/Telegram의 incident 공지
  - 빗썸 공지 피드와 assetsstatus endpoint
- 한계: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.
- 원문: [1652147](https://feed.bithumb.com/notice/1652147)

### 1652079 FLOW

- 사전 인지 가능도: `high`
- 실제 맥락: Flow 네트워크 출금 경로
- 왜 이렇게 봤는가: 입출금 전체가 아니라 출금만 막혔어도 근본 원인은 Flow 체인 측 문제라 chain-side 감시가 유효했다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Flow 네트워크 출금 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1652079](https://feed.bithumb.com/notice/1652079)

### 1652078 POKT

- 사전 인지 가능도: `high`
- 실제 맥락: Pocket Network
- 왜 이렇게 봤는가: 블록 생성 중단형이라 explorer halt와 validator 채널이 가장 중요한 선행 지표다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Pocket Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1652078](https://feed.bithumb.com/notice/1652078)

### 1652002 REI

- 사전 인지 가능도: `high`
- 실제 맥락: REI Network
- 왜 이렇게 봤는가: REI explorer/RPC sync와 공식 X·Discord를 같이 봤어야 하는 전형적 halt 케이스다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1652002](https://feed.bithumb.com/notice/1652002)

### 1651944 VANA

- 사전 인지 가능도: `high`
- 실제 맥락: Vana 메인넷
- 왜 이렇게 봤는가: 노드 sync lag가 핵심이므로 공개 RPC와 explorer의 head lag를 봤어야 한다.
- 기대 가능한 선행 시간: 수분 전 선포착 가능
- 실전 룰: Vana 메인넷 노드 sync lag가 쌓이면 거래소 지갑도 곧 막힐 확률이 높으므로 공식 status와 explorer를 같이 봤어야 한다.
- 미리 봤어야 할 채널:
  - 공식 explorer와 공개 RPC의 sync lag
  - 노드 운영자/validator 공지
  - 빗썸 공지 피드와 assetsstatus endpoint
- 한계: 외부에서 노드 sync 문제를 볼 수 있어도, 거래소가 실제 중지 버튼을 누르는 시점은 별도다.
- 원문: [1651944](https://feed.bithumb.com/notice/1651944)

### 1651736 USDT-Tron

- 사전 인지 가능도: `low`
- 실제 맥락: USDT의 Tron 출금 경로
- 왜 이렇게 봤는가: TRON 전체 장애가 아니라 빗썸 지갑 점검 경로라 사실상 빗썸 notice/assetsstatus가 최초 신호다.
- 기대 가능한 선행 시간: 사전 예고 거의 불가, 공지와 동시 포착
- 실전 룰: USDT의 Tron 출금 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- 미리 봤어야 할 채널:
  - 빗썸 공지 피드
  - 빗썸 assetsstatus endpoint
  - 동일 자산의 반복 점검 패턴과 재개 공지 이력
- 한계: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.
- 원문: [1651736](https://feed.bithumb.com/notice/1651736)

### 1651542 USDT-Tron

- 사전 인지 가능도: `low`
- 실제 맥락: USDT의 Tron 출금 경로
- 왜 이렇게 봤는가: 같은 유형의 재발 사례라 `USDT-Tron wallet check 반복` 자체는 패턴으로 학습할 수 있었지만 사전 확정은 어렵다.
- 기대 가능한 선행 시간: 사전 예고 거의 불가, 공지와 동시 포착
- 실전 룰: USDT의 Tron 출금 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- 미리 봤어야 할 채널:
  - 빗썸 공지 피드
  - 빗썸 assetsstatus endpoint
  - 동일 자산의 반복 점검 패턴과 재개 공지 이력
- 한계: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.
- 원문: [1651542](https://feed.bithumb.com/notice/1651542)

### 1651445 STRK

- 사전 인지 가능도: `high`
- 실제 맥락: Starknet
- 왜 이렇게 봤는가: Starknet sequencer/status와 explorer 최신 블록 시간을 같이 봤어야 했다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1651445](https://feed.bithumb.com/notice/1651445)

### 1650998 DIS

- 사전 인지 가능도: `high`
- 실제 맥락: DIS 프로젝트 네트워크 경로
- 왜 이렇게 봤는가: 프로젝트 네트워크 halt 여부와 공식 채널 incident를 먼저 감시했어야 하는 유형이다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: DIS 프로젝트 네트워크 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1650998](https://feed.bithumb.com/notice/1650998)

### 1650802 ADA

- 사전 인지 가능도: `high`
- 실제 맥락: Cardano
- 왜 이렇게 봤는가: Cardano tip lag, explorer head, stake pool 운영자 채널로 조기 감지가 가능했던 사례다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Cardano에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1650802](https://feed.bithumb.com/notice/1650802)

### 1650517 BERA

- 사전 인지 가능도: `high`
- 실제 맥락: Berachain
- 왜 이렇게 봤는가: Berachain explorer와 validator 채널을 동시에 보면 halt를 빠르게 볼 수 있는 유형이다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Berachain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1650517](https://feed.bithumb.com/notice/1650517)

### 1650288 DYDX

- 사전 인지 가능도: `high`
- 실제 맥락: dYdX Chain
- 왜 이렇게 봤는가: dYdX chain block halt는 체인 explorer와 validator 운영 채널에서 먼저 확인 가능한 편이다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: dYdX Chain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1650288](https://feed.bithumb.com/notice/1650288)

### 1650017 ADD

- 사전 인지 가능도: `low`
- 실제 맥락: ADD 자산의 빗썸 출금 지갑 경로
- 왜 이렇게 봤는가: wallet system check라 외부 체인 모니터링보다 빗썸 자체 상태 감시가 핵심이다.
- 기대 가능한 선행 시간: 사전 예고 거의 불가, 공지와 동시 포착
- 실전 룰: ADD 자산의 빗썸 출금 지갑 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- 미리 봤어야 할 채널:
  - 빗썸 공지 피드
  - 빗썸 assetsstatus endpoint
  - 동일 자산의 반복 점검 패턴과 재개 공지 이력
- 한계: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.
- 원문: [1650017](https://feed.bithumb.com/notice/1650017)

### 1649774 STRK

- 사전 인지 가능도: `high`
- 실제 맥락: Starknet
- 왜 이렇게 봤는가: Starknet 재발 사례라 `동일 체인 반복 장애` 자체를 prior risk로 높게 잡았어야 했다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1649774](https://feed.bithumb.com/notice/1649774)

### 1649671 ZRC

- 사전 인지 가능도: `high`
- 실제 맥락: Zircuit
- 왜 이렇게 봤는가: Zircuit explorer block lag와 status 채널을 보면 notice 전에 이상 징후를 잡을 수 있는 유형이다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Zircuit에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1649671](https://feed.bithumb.com/notice/1649671)

### 1649062 FLR

- 사전 인지 가능도: `high`
- 실제 맥락: Flare
- 왜 이렇게 봤는가: Flare explorer, validator, status 계열 신호가 가장 중요한 선행 정보다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Flare에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1649062](https://feed.bithumb.com/notice/1649062)

### 1648710 REI

- 사전 인지 가능도: `high`
- 실제 맥락: REI Network
- 왜 이렇게 봤는가: REI 반복 장애 사례라 `재발 체인` 버킷에 올려두는 것이 맞았다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1648710](https://feed.bithumb.com/notice/1648710)

### 1648132 ATOM

- 사전 인지 가능도: `high`
- 실제 맥락: Cosmos Hub
- 왜 이렇게 봤는가: Cosmos Hub는 explorer, Mintscan, validator 공지, forum까지 같이 봐야 선포착 확률이 높다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Cosmos Hub에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1648132](https://feed.bithumb.com/notice/1648132)

### 1647038 FLOW

- 사전 인지 가능도: `high`
- 실제 맥락: Flow
- 왜 이렇게 봤는가: Flow 반복 사례라 network halt 재발 위험 체인으로 분류했어야 했다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Flow에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1647038](https://feed.bithumb.com/notice/1647038)

### 1646858 IOTX

- 사전 인지 가능도: `high`
- 실제 맥락: IoTeX
- 왜 이렇게 봤는가: IoTeX explorer, status, validator 채널이 조기 포착 포인트다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: IoTeX에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1646858](https://feed.bithumb.com/notice/1646858)

### 1646423 ZIL

- 사전 인지 가능도: `high`
- 실제 맥락: Zilliqa
- 왜 이렇게 봤는가: Zilliqa explorer, official status, validator 채널에서 halt를 먼저 잡을 수 있었다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Zilliqa에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1646423](https://feed.bithumb.com/notice/1646423)

### 1645260 STX,ALEX

- 사전 인지 가능도: `high`
- 실제 맥락: Stacks; ALEX는 STX 체인 의존
- 왜 이렇게 봤는가: ALEX 자체보다 STX 메인넷 halt를 먼저 감시했어야 했다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Stacks; ALEX는 STX 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1645260](https://feed.bithumb.com/notice/1645260)

### 1645244 SUI,LWA

- 사전 인지 가능도: `high`
- 실제 맥락: Sui; LWA는 Sui 체인 의존
- 왜 이렇게 봤는가: LWA 자체보다 Sui 네트워크 블록 생성 중단을 감시해야 했다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Sui; LWA는 Sui 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- 미리 봤어야 할 채널:
  - 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부
  - 공식 status/X/Discord/Telegram의 장애 공지
  - validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- 한계: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.
- 원문: [1645244](https://feed.bithumb.com/notice/1645244)

### 1645183 ZETA

- 사전 인지 가능도: `high`
- 실제 맥락: ZetaChain
- 왜 이렇게 봤는가: 네트워크 이슈형이라 ZetaScan, validator, status 공지가 선행 지표다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: ZetaChain의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- 미리 봤어야 할 채널:
  - 공식 explorer/RPC health, block lag, transaction failure rate
  - 공식 status/X/Discord/Telegram의 incident 공지
  - 빗썸 공지 피드와 assetsstatus endpoint
- 한계: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.
- 원문: [1645183](https://feed.bithumb.com/notice/1645183)

### 1645123 LUNA2

- 사전 인지 가능도: `high`
- 실제 맥락: Terra 2.0
- 왜 이렇게 봤는가: Terra Finder와 validator 운영 채널에서 네트워크 이상을 먼저 볼 수 있었다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Terra 2.0의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- 미리 봤어야 할 채널:
  - 공식 explorer/RPC health, block lag, transaction failure rate
  - 공식 status/X/Discord/Telegram의 incident 공지
  - 빗썸 공지 피드와 assetsstatus endpoint
- 한계: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.
- 원문: [1645123](https://feed.bithumb.com/notice/1645123)

### 1645109 ZIL

- 사전 인지 가능도: `high`
- 실제 맥락: Zilliqa
- 왜 이렇게 봤는가: 같은 체인 재발 사례라 ZIL은 반복 감시 우선순위가 높았어야 한다.
- 기대 가능한 선행 시간: 수초~수시간 전 선포착 가능
- 실전 룰: Zilliqa의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- 미리 봤어야 할 채널:
  - 공식 explorer/RPC health, block lag, transaction failure rate
  - 공식 status/X/Discord/Telegram의 incident 공지
  - 빗썸 공지 피드와 assetsstatus endpoint
- 한계: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.
- 원문: [1645109](https://feed.bithumb.com/notice/1645109)
