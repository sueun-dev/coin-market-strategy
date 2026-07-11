# Bithumb High Predictability Watchlist

- Generated at: 2026-07-11T19:42:16.043555+00:00
- Source file: [`config/bithumb_immediate_suspensions_master.json`](config/bithumb_immediate_suspensions_master.json)
- Total high cases: 36
- Trigger counts: block_generation_stop 30, network_issue 6

## How To Catch

### block_generation_stop

- First signal: explorer 최신 블록 시간 정지, 블록 높이 증가 멈춤, validator/RPC 채널 장애 언급
- Action rule: 블록 생성 멈춤과 공식 incident 언급이 동시에 보이면 즉시 `빗썸 입출금 중단 가능성 높음`으로 승격

### network_issue

- First signal: explorer 지연, RPC 에러율 증가, tx fail 증가, 공식 status/X/Discord incident 공지
- Action rule: RPC health 악화와 공식 incident 신호가 붙는 순간 바로 경보

## High Cases

| Notice | Published (KST) | Assets | Trigger | Delta | How To Catch | Official |
| --- | --- | --- | --- | --- | --- | --- |
| 1652398 | 2026-03-23 23:10:34 | PEAQ | block_generation_stop | -34s | peaq 메인넷에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1652398) |
| 1652375 | 2026-03-23 08:55:00 | 0G | block_generation_stop | 0s | 0G 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1652375) |
| 1652147 | 2026-02-28 15:36:52 | 0G | block_generation_stop | +188s | 0G 메인넷의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다. | [link](https://feed.bithumb.com/notice/1652147) |
| 1652079 | 2026-02-24 11:20:00 | FLOW | block_generation_stop | 0s | Flow 네트워크 출금 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1652079) |
| 1652078 | 2026-02-23 20:57:49 | POKT | block_generation_stop | +131s | Pocket Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1652078) |
| 1652002 | 2026-02-13 08:46:44 | REI | block_generation_stop | +196s | REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1652002) |
| 1651945 | 2026-02-10 08:54:08 | G | network_issue | +52s | G 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1651945) |
| 1651944 | 2026-02-09 23:05:00 | VANA | network_issue | 0s | Vana 메인넷 노드 sync lag가 쌓이면 거래소 지갑도 곧 막힐 확률이 높으므로 공식 status와 explorer를 같이 봤어야 한다. | [link](https://feed.bithumb.com/notice/1651944) |
| 1651927 | 2026-02-08 11:45:07 | STX | block_generation_stop | -7s | STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1651927) |
| 1651496 | 2026-01-15 00:45:06 | SUI | block_generation_stop | -6s | SUI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1651496) |
| 1651445 | 2026-01-05 20:59:50 | STRK | block_generation_stop | +10s | Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1651445) |
| 1650998 | 2025-12-03 14:40:53 | DIS | block_generation_stop | +67s | DIS 프로젝트 네트워크 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1650998) |
| 1650802 | 2025-11-21 17:39:41 | ADA | block_generation_stop | +19s | Cardano에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1650802) |
| 1650517 | 2025-11-03 19:45:40 | BERA | block_generation_stop | -40s | Berachain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1650517) |
| 1650288 | 2025-10-11 11:45:55 | DYDX | block_generation_stop | -55s | dYdX Chain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1650288) |
| 1649832 | 2025-09-10 22:40:25 | POL | block_generation_stop | -25s | POL 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1649832) |
| 1649774 | 2025-09-02 15:56:36 | STRK | block_generation_stop | -96s | Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1649774) |
| 1649671 | 2025-08-29 13:12:21 | ZRC | block_generation_stop | -21s | Zircuit에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1649671) |
| 1649625 | 2025-08-23 02:00:00 | SEI | network_issue | 0s | SEI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1649625) |
| 1649062 | 2025-06-26 14:04:45 | FLR | block_generation_stop | +15s | Flare에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1649062) |
| 1648710 | 2025-05-31 11:43:30 | REI | block_generation_stop | +90s | REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648710) |
| 1648626 | 2025-05-26 10:42:19 | REI | block_generation_stop | -19s | REI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648626) |
| 1648624 | 2025-05-24 11:00:13 | ALEX,STX | block_generation_stop | -13s | ALEX,STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648624) |
| 1648448 | 2025-05-20 19:00:12 | REI | block_generation_stop | -12s | REI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648448) |
| 1648435 | 2025-05-20 08:29:21 | ALEX,STX | block_generation_stop | +39s | ALEX,STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648435) |
| 1648422 | 2025-05-14 23:05:44 | EGLD | block_generation_stop | +16s | EGLD 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648422) |
| 1648402 | 2025-05-10 08:15:01 | KSM | block_generation_stop | -1s | KSM 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648402) |
| 1648132 | 2025-04-15 00:53:21 | ATOM | block_generation_stop | +99s | Cosmos Hub에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1648132) |
| 1647038 | 2025-02-18 20:00:19 | FLOW | block_generation_stop | -19s | Flow에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1647038) |
| 1646858 | 2025-01-31 18:42:09 | IOTX | block_generation_stop | +171s | IoTeX에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1646858) |
| 1646423 | 2025-01-16 02:20:40 | ZIL | block_generation_stop | +560s | Zilliqa에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1646423) |
| 1645260 | 2024-11-27 11:12:24 | STX,ALEX | block_generation_stop | +36s | Stacks; ALEX는 STX 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1645260) |
| 1645244 | 2024-11-21 19:23:52 | SUI,LWA | block_generation_stop | +368s | Sui; LWA는 Sui 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다. | [link](https://feed.bithumb.com/notice/1645244) |
| 1645183 | 2024-11-01 11:55:09 | ZETA | network_issue | -9s | ZetaChain의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다. | [link](https://feed.bithumb.com/notice/1645183) |
| 1645123 | 2024-10-02 17:12:51 | LUNA2 | network_issue | +9s | Terra 2.0의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다. | [link](https://feed.bithumb.com/notice/1645123) |
| 1645109 | 2024-09-27 15:29:20 | ZIL | network_issue | +40s | Zilliqa의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다. | [link](https://feed.bithumb.com/notice/1645109) |

## Case Notes

### 1652398 PEAQ

- Official: https://feed.bithumb.com/notice/1652398
- Published: 2026-03-23 23:10:34
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `-34s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: peaq 메인넷
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: peaq 메인넷에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: peaq 체인 블록 생성 정지 여부를 explorer와 validator 채널에서 먼저 잡았어야 한다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652375 0G

- Official: https://feed.bithumb.com/notice/1652375
- Published: 2026-03-23 08:55:00
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `0s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: 0G 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: 0G 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1652147 0G

- Official: https://feed.bithumb.com/notice/1652147
- Published: 2026-02-28 15:36:52
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+188s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: 0G 메인넷
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: 0G 메인넷의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Why high: explorer 최신 블록 시간과 공식 장애 공지를 보면 notice 이전에 이상 징후를 잡을 수 있는 유형이다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.

### 1652079 FLOW

- Official: https://feed.bithumb.com/notice/1652079
- Published: 2026-02-24 11:20:00
- Trigger: `block_generation_stop`
- Scope: `withdrawal_only`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `0s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Flow 네트워크 출금 경로
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Flow 네트워크 출금 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: 입출금 전체가 아니라 출금만 막혔어도 근본 원인은 Flow 체인 측 문제라 chain-side 감시가 유효했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652078 POKT

- Official: https://feed.bithumb.com/notice/1652078
- Published: 2026-02-23 20:57:49
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+131s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Pocket Network
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Pocket Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: 블록 생성 중단형이라 explorer halt와 validator 채널이 가장 중요한 선행 지표다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652002 REI

- Official: https://feed.bithumb.com/notice/1652002
- Published: 2026-02-13 08:46:44
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+196s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI Network
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: REI explorer/RPC sync와 공식 X·Discord를 같이 봤어야 하는 전형적 halt 케이스다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1651945 G

- Official: https://feed.bithumb.com/notice/1651945
- Published: 2026-02-10 08:54:08
- Trigger: `network_issue`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `+52s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: G 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: G 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1651944 VANA

- Official: https://feed.bithumb.com/notice/1651944
- Published: 2026-02-09 23:05:00
- Trigger: `network_issue`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `0s`
- Expected lead time: 수분 전 선포착 가능
- Context: Vana 메인넷
- Watch channels: 공식 explorer와 공개 RPC의 sync lag; 노드 운영자/validator 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: Vana 메인넷 노드 sync lag가 쌓이면 거래소 지갑도 곧 막힐 확률이 높으므로 공식 status와 explorer를 같이 봤어야 한다.
- Why high: 노드 sync lag가 핵심이므로 공개 RPC와 explorer의 head lag를 봤어야 한다.
- Hard limit: 외부에서 노드 sync 문제를 볼 수 있어도, 거래소가 실제 중지 버튼을 누르는 시점은 별도다.

### 1651927 STX

- Official: https://feed.bithumb.com/notice/1651927
- Published: 2026-02-08 11:45:07
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-7s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: STX 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1651496 SUI

- Official: https://feed.bithumb.com/notice/1651496
- Published: 2026-01-15 00:45:06
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-6s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: SUI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: SUI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1651445 STRK

- Official: https://feed.bithumb.com/notice/1651445
- Published: 2026-01-05 20:59:50
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+10s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Starknet
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Starknet sequencer/status와 explorer 최신 블록 시간을 같이 봤어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650998 DIS

- Official: https://feed.bithumb.com/notice/1650998
- Published: 2025-12-03 14:40:53
- Trigger: `block_generation_stop`
- Scope: `withdrawal_only`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `+67s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: DIS 프로젝트 네트워크 경로
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: DIS 프로젝트 네트워크 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: 프로젝트 네트워크 halt 여부와 공식 채널 incident를 먼저 감시했어야 하는 유형이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650802 ADA

- Official: https://feed.bithumb.com/notice/1650802
- Published: 2025-11-21 17:39:41
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+19s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Cardano
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Cardano에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Cardano tip lag, explorer head, stake pool 운영자 채널로 조기 감지가 가능했던 사례다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650517 BERA

- Official: https://feed.bithumb.com/notice/1650517
- Published: 2025-11-03 19:45:40
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `-40s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Berachain
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Berachain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Berachain explorer와 validator 채널을 동시에 보면 halt를 빠르게 볼 수 있는 유형이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650288 DYDX

- Official: https://feed.bithumb.com/notice/1650288
- Published: 2025-10-11 11:45:55
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `-55s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: dYdX Chain
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: dYdX Chain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: dYdX chain block halt는 체인 explorer와 validator 운영 채널에서 먼저 확인 가능한 편이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1649832 POL

- Official: https://feed.bithumb.com/notice/1649832
- Published: 2025-09-10 22:40:25
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-25s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: POL 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: POL 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1649774 STRK

- Official: https://feed.bithumb.com/notice/1649774
- Published: 2025-09-02 15:56:36
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `-96s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Starknet
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Starknet 재발 사례라 `동일 체인 반복 장애` 자체를 prior risk로 높게 잡았어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1649671 ZRC

- Official: https://feed.bithumb.com/notice/1649671
- Published: 2025-08-29 13:12:21
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `-21s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Zircuit
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Zircuit에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Zircuit explorer block lag와 status 채널을 보면 notice 전에 이상 징후를 잡을 수 있는 유형이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1649625 SEI

- Official: https://feed.bithumb.com/notice/1649625
- Published: 2025-08-23 02:00:00
- Trigger: `network_issue`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `0s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: SEI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: SEI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1649062 FLR

- Official: https://feed.bithumb.com/notice/1649062
- Published: 2025-06-26 14:04:45
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+15s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Flare
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Flare에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Flare explorer, validator, status 계열 신호가 가장 중요한 선행 정보다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1648710 REI

- Official: https://feed.bithumb.com/notice/1648710
- Published: 2025-05-31 11:43:30
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+90s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI Network
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: REI 반복 장애 사례라 `재발 체인` 버킷에 올려두는 것이 맞았다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1648626 REI

- Official: https://feed.bithumb.com/notice/1648626
- Published: 2025-05-26 10:42:19
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-19s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: REI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648624 ALEX,STX

- Official: https://feed.bithumb.com/notice/1648624
- Published: 2025-05-24 11:00:13
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-13s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: ALEX,STX 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: ALEX,STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648448 REI

- Official: https://feed.bithumb.com/notice/1648448
- Published: 2025-05-20 19:00:12
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-12s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: REI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648435 ALEX,STX

- Official: https://feed.bithumb.com/notice/1648435
- Published: 2025-05-20 08:29:21
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `+39s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: ALEX,STX 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: ALEX,STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648422 EGLD

- Official: https://feed.bithumb.com/notice/1648422
- Published: 2025-05-14 23:05:44
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `+16s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: EGLD 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: EGLD 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648402 KSM

- Official: https://feed.bithumb.com/notice/1648402
- Published: 2025-05-10 08:15:01
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Delta: `-1s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: KSM 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: KSM 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Why high: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648132 ATOM

- Official: https://feed.bithumb.com/notice/1648132
- Published: 2025-04-15 00:53:21
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+99s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Cosmos Hub
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Cosmos Hub에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Cosmos Hub는 explorer, Mintscan, validator 공지, forum까지 같이 봐야 선포착 확률이 높다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1647038 FLOW

- Official: https://feed.bithumb.com/notice/1647038
- Published: 2025-02-18 20:00:19
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `-19s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Flow
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Flow에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Flow 반복 사례라 network halt 재발 위험 체인으로 분류했어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1646858 IOTX

- Official: https://feed.bithumb.com/notice/1646858
- Published: 2025-01-31 18:42:09
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Delta: `+171s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: IoTeX
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: IoTeX에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: IoTeX explorer, status, validator 채널이 조기 포착 포인트다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1646423 ZIL

- Official: https://feed.bithumb.com/notice/1646423
- Published: 2025-01-16 02:20:40
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `+560s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Zilliqa
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Zilliqa에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: Zilliqa explorer, official status, validator 채널에서 halt를 먼저 잡을 수 있었다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1645260 STX,ALEX

- Official: https://feed.bithumb.com/notice/1645260
- Published: 2024-11-27 11:12:24
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `+36s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Stacks; ALEX는 STX 체인 의존
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Stacks; ALEX는 STX 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: ALEX 자체보다 STX 메인넷 halt를 먼저 감시했어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1645244 SUI,LWA

- Official: https://feed.bithumb.com/notice/1645244
- Published: 2024-11-21 19:23:52
- Trigger: `block_generation_stop`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `+368s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Sui; LWA는 Sui 체인 의존
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- How to catch: Sui; LWA는 Sui 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Why high: LWA 자체보다 Sui 네트워크 블록 생성 중단을 감시해야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1645183 ZETA

- Official: https://feed.bithumb.com/notice/1645183
- Published: 2024-11-01 11:55:09
- Trigger: `network_issue`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `-9s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: ZetaChain
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: ZetaChain의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Why high: 네트워크 이슈형이라 ZetaScan, validator, status 공지가 선행 지표다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.

### 1645123 LUNA2

- Official: https://feed.bithumb.com/notice/1645123
- Published: 2024-10-02 17:12:51
- Trigger: `network_issue`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `+9s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Terra 2.0
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: Terra 2.0의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Why high: Terra Finder와 validator 운영 채널에서 네트워크 이상을 먼저 볼 수 있었다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.

### 1645109 ZIL

- Official: https://feed.bithumb.com/notice/1645109
- Published: 2024-09-27 15:29:20
- Trigger: `network_issue`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Delta: `+40s`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Zilliqa
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- How to catch: Zilliqa의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Why high: 같은 체인 재발 사례라 ZIL은 반복 감시 우선순위가 높았어야 한다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.
