# Bithumb Immediate Suspensions Master

- Generated at: 2026-07-11T19:42:16.024259+00:00
- Scope: 빗썸 `공지 직후 정지형` 관련 단일 기준 문서
- Total cases: 52
- Source coverage: both 22, notice_scan_only 23, legacy_only 7
- Classification: explicit_near_immediate 42, implicit_on_notice 3, legacy_effective_immediate 7
- Predictability: high 36, medium 5, low 11

## Source Files

- [bithumb_notice_posted_immediate_suspensions.json](config/bithumb_notice_posted_immediate_suspensions.json)
- [bithumb_effective_immediate_suspensions.json](config/bithumb_effective_immediate_suspensions.json)
- [bithumb_effective_immediate_early_warning_methods.json](config/bithumb_effective_immediate_early_warning_methods.json)

## Reading Guide

- `both`: 확장 notice-scan 세트와 기존 legacy 세트 양쪽에서 같이 잡힌 케이스
- `notice_scan_only`: 공식 notice 목록 전수 스캔에서 새로 잡힌 케이스
- `legacy_only`: 기존 수기 검증 세트에는 있었지만 현재 notice 목록 전수 스캔 범위 밖이라 legacy 근거로만 유지한 케이스
- `explicit_near_immediate`: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내
- `implicit_on_notice`: 별도 중지 시각 없이 공지 자체가 첫 public stop 신호
- `legacy_effective_immediate`: 기존 작업본에서 same-minute/near-immediate로 검증된 legacy 케이스

## Master Table

| Notice | Published (KST) | Assets | Scope | Source | Class | Trigger | Delta | Predictability | Official |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1652530 | 2026-04-02 03:07:55 | DRIFT | deposit_withdrawal | both | explicit_near_immediate | security_issue | -55s | medium | [link](https://feed.bithumb.com/notice/1652530) |
| 1652398 | 2026-03-23 23:10:34 | PEAQ | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | -34s | high | [link](https://feed.bithumb.com/notice/1652398) |
| 1652375 | 2026-03-23 08:55:00 | 0G | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | 0s | high | [link](https://feed.bithumb.com/notice/1652375) |
| 1652352 | 2026-03-20 09:33:51 | WAXP | deposit_withdrawal | both | explicit_near_immediate | unknown | +69s | low | [link](https://feed.bithumb.com/notice/1652352) |
| 1652284 | 2026-03-15 23:23:44 | CAKE,THE,XVS | deposit_withdrawal | notice_scan_only | implicit_on_notice | security_issue | - | medium | [link](https://feed.bithumb.com/notice/1652284) |
| 1652147 | 2026-02-28 15:36:52 | 0G | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +188s | high | [link](https://feed.bithumb.com/notice/1652147) |
| 1652079 | 2026-02-24 11:20:00 | FLOW | withdrawal_only | both | explicit_near_immediate | block_generation_stop | 0s | high | [link](https://feed.bithumb.com/notice/1652079) |
| 1652078 | 2026-02-23 20:57:49 | POKT | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +131s | high | [link](https://feed.bithumb.com/notice/1652078) |
| 1652029 | 2026-02-21 19:40:00 | IOTX | deposit_withdrawal | notice_scan_only | implicit_on_notice | security_issue | - | medium | [link](https://feed.bithumb.com/notice/1652029) |
| 1652014 | 2026-02-14 09:20:34 | USDT | withdrawal_only | notice_scan_only | explicit_near_immediate | wallet_system_check | -34s | low | [link](https://feed.bithumb.com/notice/1652014) |
| 1652002 | 2026-02-13 08:46:44 | REI | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +196s | high | [link](https://feed.bithumb.com/notice/1652002) |
| 1652001 | 2026-02-13 02:15:00 | USDT | withdrawal_only | notice_scan_only | explicit_near_immediate | unknown | 0s | low | [link](https://feed.bithumb.com/notice/1652001) |
| 1651945 | 2026-02-10 08:54:08 | G | deposit_withdrawal | notice_scan_only | explicit_near_immediate | network_issue | +52s | high | [link](https://feed.bithumb.com/notice/1651945) |
| 1651944 | 2026-02-09 23:05:00 | VANA | deposit_withdrawal | both | explicit_near_immediate | network_issue | 0s | high | [link](https://feed.bithumb.com/notice/1651944) |
| 1651927 | 2026-02-08 11:45:07 | STX | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -7s | high | [link](https://feed.bithumb.com/notice/1651927) |
| 1651736 | 2026-01-31 04:10:00 | USDT-Tron | withdrawal_only | both | explicit_near_immediate | unknown | 0s | low | [link](https://feed.bithumb.com/notice/1651736) |
| 1651542 | 2026-01-19 12:55:37 | USDT-Tron | withdrawal_only | both | explicit_near_immediate | unknown | -37s | low | [link](https://feed.bithumb.com/notice/1651542) |
| 1651496 | 2026-01-15 00:45:06 | SUI | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -6s | high | [link](https://feed.bithumb.com/notice/1651496) |
| 1651445 | 2026-01-05 20:59:50 | STRK | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +10s | high | [link](https://feed.bithumb.com/notice/1651445) |
| 1651396 | 2025-12-27 21:02:17 | FLOW | deposit_withdrawal | notice_scan_only | explicit_near_immediate | security_issue | -17s | medium | [link](https://feed.bithumb.com/notice/1651396) |
| 1650998 | 2025-12-03 14:40:53 | DIS | withdrawal_only | legacy_only | legacy_effective_immediate | block_generation_stop | +67s | high | [link](https://feed.bithumb.com/notice/1650998) |
| 1650802 | 2025-11-21 17:39:41 | ADA | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +19s | high | [link](https://feed.bithumb.com/notice/1650802) |
| 1650635 | 2025-11-07 21:35:30 | MERL | deposit_withdrawal | notice_scan_only | explicit_near_immediate | unknown | -30s | low | [link](https://feed.bithumb.com/notice/1650635) |
| 1650517 | 2025-11-03 19:45:40 | BERA | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | -40s | high | [link](https://feed.bithumb.com/notice/1650517) |
| 1650288 | 2025-10-11 11:45:55 | DYDX | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | -55s | high | [link](https://feed.bithumb.com/notice/1650288) |
| 1650017 | 2025-09-22 18:10:39 | ADD | withdrawal_only | both | explicit_near_immediate | unknown | -39s | low | [link](https://feed.bithumb.com/notice/1650017) |
| 1649832 | 2025-09-10 22:40:25 | POL | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -25s | high | [link](https://feed.bithumb.com/notice/1649832) |
| 1649774 | 2025-09-02 15:56:36 | STRK | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | -96s | high | [link](https://feed.bithumb.com/notice/1649774) |
| 1649671 | 2025-08-29 13:12:21 | ZRC | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | -21s | high | [link](https://feed.bithumb.com/notice/1649671) |
| 1649625 | 2025-08-23 02:00:00 | SEI | deposit_withdrawal | notice_scan_only | explicit_near_immediate | network_issue | 0s | high | [link](https://feed.bithumb.com/notice/1649625) |
| 1649384 | 2025-07-29 00:49:55 | TIA | deposit_withdrawal | notice_scan_only | explicit_near_immediate | unknown | +5s | low | [link](https://feed.bithumb.com/notice/1649384) |
| 1649237 | 2025-07-12 19:30:05 | PUNDIAI | deposit_withdrawal | notice_scan_only | explicit_near_immediate | unknown | -5s | low | [link](https://feed.bithumb.com/notice/1649237) |
| 1649062 | 2025-06-26 14:04:45 | FLR | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +15s | high | [link](https://feed.bithumb.com/notice/1649062) |
| 1648776 | 2025-06-06 20:15:05 | ALEX,STX | deposit_withdrawal | notice_scan_only | implicit_on_notice | security_issue | - | medium | [link](https://feed.bithumb.com/notice/1648776) |
| 1648710 | 2025-05-31 11:43:30 | REI | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +90s | high | [link](https://feed.bithumb.com/notice/1648710) |
| 1648626 | 2025-05-26 10:42:19 | REI | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -19s | high | [link](https://feed.bithumb.com/notice/1648626) |
| 1648624 | 2025-05-24 11:00:13 | ALEX,STX | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -13s | high | [link](https://feed.bithumb.com/notice/1648624) |
| 1648448 | 2025-05-20 19:00:12 | REI | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -12s | high | [link](https://feed.bithumb.com/notice/1648448) |
| 1648435 | 2025-05-20 08:29:21 | ALEX,STX | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | +39s | high | [link](https://feed.bithumb.com/notice/1648435) |
| 1648422 | 2025-05-14 23:05:44 | EGLD | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | +16s | high | [link](https://feed.bithumb.com/notice/1648422) |
| 1648414 | 2025-05-13 11:52:26 | BABY | deposit_withdrawal | notice_scan_only | explicit_near_immediate | unknown | +154s | low | [link](https://feed.bithumb.com/notice/1648414) |
| 1648402 | 2025-05-10 08:15:01 | KSM | deposit_withdrawal | notice_scan_only | explicit_near_immediate | block_generation_stop | -1s | high | [link](https://feed.bithumb.com/notice/1648402) |
| 1648132 | 2025-04-15 00:53:21 | ATOM | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +99s | high | [link](https://feed.bithumb.com/notice/1648132) |
| 1647090 | 2025-02-19 18:00:00 | WLD | deposit_withdrawal | notice_scan_only | explicit_near_immediate | unknown | 0s | low | [link](https://feed.bithumb.com/notice/1647090) |
| 1647038 | 2025-02-18 20:00:19 | FLOW | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | -19s | high | [link](https://feed.bithumb.com/notice/1647038) |
| 1646858 | 2025-01-31 18:42:09 | IOTX | deposit_withdrawal | both | explicit_near_immediate | block_generation_stop | +171s | high | [link](https://feed.bithumb.com/notice/1646858) |
| 1646423 | 2025-01-16 02:20:40 | ZIL | deposit_withdrawal | legacy_only | legacy_effective_immediate | block_generation_stop | +560s | high | [link](https://feed.bithumb.com/notice/1646423) |
| 1645260 | 2024-11-27 11:12:24 | STX,ALEX | deposit_withdrawal | legacy_only | legacy_effective_immediate | block_generation_stop | +36s | high | [link](https://feed.bithumb.com/notice/1645260) |
| 1645244 | 2024-11-21 19:23:52 | SUI,LWA | deposit_withdrawal | legacy_only | legacy_effective_immediate | block_generation_stop | +368s | high | [link](https://feed.bithumb.com/notice/1645244) |
| 1645183 | 2024-11-01 11:55:09 | ZETA | deposit_withdrawal | legacy_only | legacy_effective_immediate | network_issue | -9s | high | [link](https://feed.bithumb.com/notice/1645183) |
| 1645123 | 2024-10-02 17:12:51 | LUNA2 | deposit_withdrawal | legacy_only | legacy_effective_immediate | network_issue | +9s | high | [link](https://feed.bithumb.com/notice/1645123) |
| 1645109 | 2024-09-27 15:29:20 | ZIL | deposit_withdrawal | legacy_only | legacy_effective_immediate | network_issue | +40s | high | [link](https://feed.bithumb.com/notice/1645109) |

## Case Notes

### 1652530 드리프트(DRIFT) 입출금 일시 중단 안내(04/02 출금 재개)Update

- Official: https://feed.bithumb.com/notice/1652530
- Published: 2026-04-02 03:07:55
- Asset scope: `DRIFT`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `security_issue`
- Stated stop: `2026-04-02 03:07:00`
- Delta: `-55s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 드리프트(DRIFT) 보안 문제 의심 정황으로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. **[ 드리프트(DRIFT)입출금 일시 중지 안내 ]** * 대상 가상자산 **-드리프트(DRIFT)** * 입출금 중지 시점 **- 2026.04.02(목) 오전 3시 07분(KST) 예정**
- Pre-detectability: `medium`
- Expected lead time: 수분~수시간 전 부분 선포착 가능
- Context: Drift 프로토콜과 Solana 생태계
- Watch channels: 프로젝트 공식 X/Discord/GitHub 보안 공지; 온체인 exploit alert, treasury/bridge 대량 이동 알림; 거래유의종목/유의촉구 공지와 빗썸 공지 피드
- Practical rule: Drift 프로토콜과 Solana 생태계 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하므로 exploit 알림과 공식 보안 공지를 가장 먼저 봤어야 한다.
- Case note: 체인 halt가 아니라 보안 이슈이므로 프로젝트 보안 채널과 exploit 알림이 핵심이다.
- Hard limit: 보안 이슈는 거래소 내부 판단이 섞이므로 exact stop time을 미리 맞히는 것은 어렵다.

### 1652398 피크(PEAQ) 입출금 일시 중단 안내(03/24 재개)

- Official: https://feed.bithumb.com/notice/1652398
- Published: 2026-03-23 23:10:34
- Asset scope: `PEAQ`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-03-23 23:10:00`
- Delta: `-34s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸 입니다. 피크(PEAQ)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**피크(PEAQ)** * 서비스 제한 범위 -피크(PEAQ)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: peaq 메인넷
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: peaq 메인넷에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: peaq 체인 블록 생성 정지 여부를 explorer와 validator 채널에서 먼저 잡았어야 한다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652375 제로지(0G) 입출금 일시 중단 안내 (03/24 재개)

- Official: https://feed.bithumb.com/notice/1652375
- Published: 2026-03-23 08:55:00
- Asset scope: `0G`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-03-23 08:55:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸 입니다. 제로지(0G)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**제로지(0G)** * 서비스 제한 범위 - 제로지(0G)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: 0G 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: 0G 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1652352 왁스(WAXP) 입출금 일시 중지 안내 (03/20 재개)

- Official: https://feed.bithumb.com/notice/1652352
- Published: 2026-03-20 09:33:51
- Asset scope: `WAXP`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2026-03-20 09:35:00`
- Delta: `+69s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융파트너, 빗썸입니다. 왁스(WAXP)지갑 시스템 점검에 따라, 안정적인 입출금 서비스 제공을 위해 아래와 같이 입출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. **[ 왁스(WAXP)입출금 일시 중지 안내 ]** * 대상 가상자산 -왁스(WAXP) * 입출금 중지 시점 **- 2026.03.20(금) 오전 9시 35분 (KST) 예정**
- Pre-detectability: `low`
- Expected lead time: 사전 예고 거의 불가, 공지와 동시 포착
- Context: WAX 자산의 빗썸 지갑 경로
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 동일 자산의 반복 점검 패턴과 재개 공지 이력
- Practical rule: WAX 자산의 빗썸 지갑 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- Case note: 체인 문제보다 빗썸 내부 wallet system check 성격이 강해서 거래소 신호 의존도가 높다.
- Hard limit: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.

### 1652284 비너스(XVS), 테나(THE), 팬케이크스왑(CAKE) 유의촉구 및 입출금 일시 중단 안내 (THE 03/19 재개)

- Official: https://feed.bithumb.com/notice/1652284
- Published: 2026-03-15 23:23:44
- Asset scope: `CAKE,THE,XVS`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `implicit_on_notice`
- Trigger: `security_issue`
- Stated stop: `-`
- Delta: `-`
- Confidence: `medium`
- Inclusion reason: 원문 본문이 별도 미래 중지 시각 없이 공지와 함께 즉시형/무기한 중단 문구를 사용
- Evidence phrase: 이로 인해 비너스(XVS), 테나(THE), 팬케이크스왑(CAKE)의 시세 변동성 증대가 우려됩니다. 비너스(XVS)에 대한 투자에 각별히 유의해 주시기를 바랍니다. 또한 안정성 확보 시점까지 비너스(XVS), 테나(THE) 에 대한 입출금 서비스가 일시 중단될 예정입니다
- Pre-detectability: `medium`
- Expected lead time: 수분~수시간 전 부분 선포착 가능
- Context: CAKE,THE,XVS 관련 네트워크/프로젝트
- Watch channels: 프로젝트 공식 X/Discord/GitHub 보안 공지; on-chain exploit alert, treasury/bridge 대량 이동 알림; 빗썸 공지 피드와 거래유의/유의촉구 공지
- Practical rule: CAKE,THE,XVS 관련 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하는 경우가 많아 exploit 알림과 공식 보안 채널을 먼저 봤어야 한다.
- Case note: 보안 이슈는 외부 신호는 먼저 보일 수 있지만 거래소 stop timing까지 맞히긴 어렵다.
- Hard limit: 거래소 내부 리스크 판단이 개입돼 exact stop time 예측은 어렵다.

### 1652147 제로지(0G) 입출금 일시 중단 안내 (03/01 재개)

- Official: https://feed.bithumb.com/notice/1652147
- Published: 2026-02-28 15:36:52
- Asset scope: `0G`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-02-28 15:40:00`
- Delta: `+188s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 제로지(0G)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**제로지(0G)** * 서비스 제한 범위 - 제로지(0G)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: 0G 메인넷
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: 0G 메인넷의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Case note: explorer 최신 블록 시간과 공식 장애 공지를 보면 notice 이전에 이상 징후를 잡을 수 있는 유형이다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.

### 1652079 플로우(FLOW) 출금 일시 중지 안내 (02/25 출금 재개)

- Official: https://feed.bithumb.com/notice/1652079
- Published: 2026-02-24 11:20:00
- Asset scope: `FLOW`
- Scope: `withdrawal_only`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-02-24 11:20:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 플로우(FLOW)네트워크 이슈로 인해 일시적으로 출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**플로우(FLOW)** * 서비스 제한 범위 - 플로우(FLOW)가상자산 출금 * 출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Flow 네트워크 출금 경로
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Flow 네트워크 출금 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: 입출금 전체가 아니라 출금만 막혔어도 근본 원인은 Flow 체인 측 문제라 chain-side 감시가 유효했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652078 포켓네트워크(POKT) 입출금 일시 중지 안내 (2/24 재개)

- Official: https://feed.bithumb.com/notice/1652078
- Published: 2026-02-23 20:57:49
- Asset scope: `POKT`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-02-23 21:00:00`
- Delta: `+131s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 포켓네트워크(POKT)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**포켓네트워크(POKT)** * 서비스 제한 범위 - 포켓네트워크(POKT)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Pocket Network
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Pocket Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: 블록 생성 중단형이라 explorer halt와 validator 채널이 가장 중요한 선행 지표다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652029 아이오텍스(IOTX) 유의촉구 및 입출금 일시 중단 안내 (02/25 출금 재개)

- Official: https://feed.bithumb.com/notice/1652029
- Published: 2026-02-21 19:40:00
- Asset scope: `IOTX`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `implicit_on_notice`
- Trigger: `security_issue`
- Stated stop: `-`
- Delta: `-`
- Confidence: `medium`
- Inclusion reason: 원문 본문이 별도 미래 중지 시각 없이 공지와 함께 즉시형/무기한 중단 문구를 사용
- Evidence phrase: 이로 인해 아이오텍스(IOTX)의 시세 변동성 증대가 우려됩니다. 아이오텍스(IOTX)에 대한 투자에 각별히 유의해 주시기를 바랍니다. 또한 안정성 확보 시점까지 아이오텍스(IOTX)에 대한 입출금 서비스가 일시 중단될 예정입니다
- Pre-detectability: `medium`
- Expected lead time: 수분~수시간 전 부분 선포착 가능
- Context: IOTX 관련 네트워크/프로젝트
- Watch channels: 프로젝트 공식 X/Discord/GitHub 보안 공지; on-chain exploit alert, treasury/bridge 대량 이동 알림; 빗썸 공지 피드와 거래유의/유의촉구 공지
- Practical rule: IOTX 관련 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하는 경우가 많아 exploit 알림과 공식 보안 채널을 먼저 봤어야 한다.
- Case note: 보안 이슈는 외부 신호는 먼저 보일 수 있지만 거래소 stop timing까지 맞히긴 어렵다.
- Hard limit: 거래소 내부 리스크 판단이 개입돼 exact stop time 예측은 어렵다.

### 1652014 테더(USDT) Kaia 네트워크 출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1652014
- Published: 2026-02-14 09:20:34
- Asset scope: `USDT`
- Scope: `withdrawal_only`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `wallet_system_check`
- Stated stop: `2026-02-14 09:20:00`
- Delta: `-34s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 테더(USDT)지갑 시스템 점검에 따라 안정적인 서비스 제공을 위해 아래와 같이 출금이 일시 중지될 예정이며, 출금 중지 시점은 2026.02.14(토) 오전 9시 20분 예정으로 공지 시각과 사실상 동일하다.
- Pre-detectability: `low`
- Expected lead time: 사전 예고 거의 불가, 공지와 동시 포착
- Context: USDT의 빗썸 지갑 경로
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 동일 자산의 반복 점검 패턴과 재개 공지 이력
- Practical rule: USDT 쪽은 체인 외부 신호보다 거래소 내부 월렛 점검이 원인인 경우가 많아 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- Case note: 외부 체인 데이터만으로는 사전 포착이 거의 불가능한 유형이다.
- Hard limit: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 어렵다.

### 1652002 레이(REI) 입출금 일시 중지 안내 (02/13 재개)

- Official: https://feed.bithumb.com/notice/1652002
- Published: 2026-02-13 08:46:44
- Asset scope: `REI`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-02-13 08:50:00`
- Delta: `+196s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 레이(REI)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**레이(REI)** * 서비스 제한 범위 - 레이(REI)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI Network
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: REI explorer/RPC sync와 공식 X·Discord를 같이 봤어야 하는 전형적 halt 케이스다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1652001 테더(USDT) Tron 네트워크 출금 일시 중단 안내 (2/16 재개)

- Official: https://feed.bithumb.com/notice/1652001
- Published: 2026-02-13 02:15:00
- Asset scope: `USDT`
- Scope: `withdrawal_only`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2026-02-13 02:15:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 테더(USDT)지갑 시스템 점검에 따라, 안정적인 서비스 제공을 위해 아래와 같이 출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. * 대상 가상자산 - **테더****(USDT) - Tron 네트워크** * 서비스 제한 범위 - 테더(USDT) - Tron 네트워크 가상자산 출금 * 출금 중지 시점
- Pre-detectability: `low`
- Expected lead time: 공개 신호만으로는 제한적
- Context: USDT 관련 네트워크/프로젝트
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 자산별 반복 중단 패턴과 프로젝트 공식 채널
- Practical rule: USDT 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다.
- Case note: 원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.
- Hard limit: 원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.

### 1651945 그래비티(G) 입출금 일시 중지 안내 (02/11 재개)

- Official: https://feed.bithumb.com/notice/1651945
- Published: 2026-02-10 08:54:08
- Asset scope: `G`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `network_issue`
- Stated stop: `2026-02-10 08:55:00`
- Delta: `+52s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 그래비티(G)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -그래비티(G) * 서비스 제한 범위 -그래비티(G) - Gravity 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: G 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: G 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1651944 바나(VANA) 입출금 일시 중지 안내 (02/10 재개)

- Official: https://feed.bithumb.com/notice/1651944
- Published: 2026-02-09 23:05:00
- Asset scope: `VANA`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `network_issue`
- Stated stop: `2026-02-09 23:05:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 바나(VANA)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 - 바나(VANA) * 서비스 제한 범위 - 바나(VANA)- Vana 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수분 전 선포착 가능
- Context: Vana 메인넷
- Watch channels: 공식 explorer와 공개 RPC의 sync lag; 노드 운영자/validator 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: Vana 메인넷 노드 sync lag가 쌓이면 거래소 지갑도 곧 막힐 확률이 높으므로 공식 status와 explorer를 같이 봤어야 한다.
- Case note: 노드 sync lag가 핵심이므로 공개 RPC와 explorer의 head lag를 봤어야 한다.
- Hard limit: 외부에서 노드 sync 문제를 볼 수 있어도, 거래소가 실제 중지 버튼을 누르는 시점은 별도다.

### 1651927 스택스(STX) 네트워크 계열 입출금 일시 중지 안내 (02/09 재개)

- Official: https://feed.bithumb.com/notice/1651927
- Published: 2026-02-08 11:45:07
- Asset scope: `STX`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-02-08 11:45:00`
- Delta: `-7s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 스택스(STX)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -스택스(STX) * 서비스 제한 범위 - 스택스(STX)- Stacks 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: STX 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1651736 테더(USDT) 일부 네트워크 출금 일시 중단 안내 (2/13 카이아 네트워크 재개)

- Official: https://feed.bithumb.com/notice/1651736
- Published: 2026-01-31 04:10:00
- Asset scope: `USDT-Tron`
- Scope: `withdrawal_only`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2026-01-31 04:10:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 테더(USDT)지갑 시스템 점검에 따라, 안정적인 서비스 제공을 위해 아래와 같이 출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. * 대상 가상자산 - **테더****(USDT) - Tron 네트워크** * 서비스 제한 범위 - 테더(USDT) - Tron 네트워크 가상자산 출금 * 출금 중지 시점
- Pre-detectability: `low`
- Expected lead time: 사전 예고 거의 불가, 공지와 동시 포착
- Context: USDT의 Tron 출금 경로
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 동일 자산의 반복 점검 패턴과 재개 공지 이력
- Practical rule: USDT의 Tron 출금 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- Case note: TRON 전체 장애가 아니라 빗썸 지갑 점검 경로라 사실상 빗썸 notice/assetsstatus가 최초 신호다.
- Hard limit: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.

### 1651542 테더(USDT) 일부 네트워크 출금 일시 중단 안내 (01/27 재개)

- Official: https://feed.bithumb.com/notice/1651542
- Published: 2026-01-19 12:55:37
- Asset scope: `USDT-Tron`
- Scope: `withdrawal_only`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2026-01-19 12:55:00`
- Delta: `-37s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 테더(USDT)지갑 시스템 점검에 따라, 안정적인 서비스 제공을 위해 아래와 같이 출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. * 대상 가상자산 - **테더****(USDT) - Tron 네트워크** * 서비스 제한 범위 - 테더(USDT) - Tron 네트워크 가상자산 출금 * 출금 중지 시점
- Pre-detectability: `low`
- Expected lead time: 사전 예고 거의 불가, 공지와 동시 포착
- Context: USDT의 Tron 출금 경로
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 동일 자산의 반복 점검 패턴과 재개 공지 이력
- Practical rule: USDT의 Tron 출금 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- Case note: 같은 유형의 재발 사례라 `USDT-Tron wallet check 반복` 자체는 패턴으로 학습할 수 있었지만 사전 확정은 어렵다.
- Hard limit: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.

### 1651496 수이(SUI) 네트워크 계열 입출금 일시 중지 안내 (01/15 재개)

- Official: https://feed.bithumb.com/notice/1651496
- Published: 2026-01-15 00:45:06
- Asset scope: `SUI`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-01-15 00:45:00`
- Delta: `-6s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 수이(SUI)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -수이(SUI) 딥북(DEEP) 월러스(WAL) 루미웨이브(LWA) 블루핀(BLUE) 해달 프로토콜(HAEDAL) 모멘텀(MMT) * 서비스 제한 범위 - 수이(SUI)- Sui 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: SUI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: SUI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1651445 스타크넷(STRK) 입출금 일시 중지 안내 (01/06 재개)

- Official: https://feed.bithumb.com/notice/1651445
- Published: 2026-01-05 20:59:50
- Asset scope: `STRK`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2026-01-05 21:00:00`
- Delta: `+10s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 스타크넷(STRK)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**스타크넷(STRK)** * 서비스 제한 범위 - 스타크넷(STRK) - Starknet 네트워크 가상자산 입출금 ***Starknet 입출금 중지이며 Ethereum 네트워크로는 입출금 서비스 이용 가능합니다.*** 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Starknet
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Starknet sequencer/status와 explorer 최신 블록 시간을 같이 봤어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1651396 플로우(FLOW) 입출금 일시 중지 안내(01/05 출금 재개)

- Official: https://feed.bithumb.com/notice/1651396
- Published: 2025-12-27 21:02:17
- Asset scope: `FLOW`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `security_issue`
- Stated stop: `2025-12-27 21:02:00`
- Delta: `-17s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안정성 확보 시점까지 플로우(FLOW)에 대한 입출금 서비스가 일시 중단될 예정입니다
- Pre-detectability: `medium`
- Expected lead time: 수분~수시간 전 부분 선포착 가능
- Context: FLOW 관련 네트워크/프로젝트
- Watch channels: 프로젝트 공식 X/Discord/GitHub 보안 공지; on-chain exploit alert, treasury/bridge 대량 이동 알림; 빗썸 공지 피드와 거래유의/유의촉구 공지
- Practical rule: FLOW 관련 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하는 경우가 많아 exploit 알림과 공식 보안 채널을 먼저 봤어야 한다.
- Case note: 보안 이슈는 외부 신호는 먼저 보일 수 있지만 거래소 stop timing까지 맞히긴 어렵다.
- Hard limit: 거래소 내부 리스크 판단이 개입돼 exact stop time 예측은 어렵다.

### 1650998 디스(DIS) 출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1650998
- Published: 2025-12-03 14:40:53
- Asset scope: `DIS`
- Scope: `withdrawal_only`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-12-03 14:42:00`
- Delta: `+67s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: DIS 프로젝트 네트워크 경로
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: DIS 프로젝트 네트워크 경로에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: 프로젝트 네트워크 halt 여부와 공식 채널 incident를 먼저 감시했어야 하는 유형이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650802 에이다(ADA) 입출금 일시 중지 안내(11/26 재개)

- Official: https://feed.bithumb.com/notice/1650802
- Published: 2025-11-21 17:39:41
- Asset scope: `ADA`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-11-21 17:40:00`
- Delta: `+19s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 에이다(ADA)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 - 에이다(ADA) * 서비스 제한 범위 - 에이다(ADA)- Cardano 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Cardano
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Cardano에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Cardano tip lag, explorer head, stake pool 운영자 채널로 조기 감지가 가능했던 사례다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650635 멀린 체인(MERL) 입출금 일시 중지 안내 (11/10 재개)

- Official: https://feed.bithumb.com/notice/1650635
- Published: 2025-11-07 21:35:30
- Asset scope: `MERL`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2025-11-07 21:35:00`
- Delta: `-30s`
- Confidence: `high`
- Inclusion reason: 공식 원문이 `오후 21시 35분`처럼 24시간 표기와 PM 표기를 섞어 썼지만, 정규화하면 공지 시각과 30초 차이의 near-immediate 케이스
- Evidence phrase: 멀린 체인(MERL) 네트워크 업그레이드 지원에 따라 입출금이 일시 중지될 예정이며, 본문 중지 시점은 2025.11.07(금) 오후 21시 35분 예정으로 공지 시각과 사실상 동일하다.
- Pre-detectability: `low`
- Expected lead time: 공개 신호만으로는 제한적
- Context: MERL 관련 네트워크/프로젝트
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 자산별 반복 중단 패턴과 프로젝트 공식 채널
- Practical rule: MERL 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다.
- Case note: 원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.
- Hard limit: 원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.

### 1650517 베라체인(BERA) 입출금 일시 중지 안내 (11/05 재개)

- Official: https://feed.bithumb.com/notice/1650517
- Published: 2025-11-03 19:45:40
- Asset scope: `BERA`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-11-03 19:45:00`
- Delta: `-40s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 베라체인(BERA)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 - 베라체인**(BERA)** * 서비스 제한 범위 - 베라체인**(BERA)**- BERA 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Berachain
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Berachain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Berachain explorer와 validator 채널을 동시에 보면 halt를 빠르게 볼 수 있는 유형이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650288 디와이디엑스(DYDX) 입출금 일시 중지 안내 (10/13 재개)

- Official: https://feed.bithumb.com/notice/1650288
- Published: 2025-10-11 11:45:55
- Asset scope: `DYDX`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-10-11 11:45:00`
- Delta: `-55s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 디와이디엑스(DYDX)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -디와이디엑스(DYDX) * 서비스 제한 범위 -디와이디엑스(DYDX) 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: dYdX Chain
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: dYdX Chain에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: dYdX chain block halt는 체인 explorer와 validator 운영 채널에서 먼저 확인 가능한 편이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1650017 애드(ADD) 출금 일시 중지 안내

- Official: https://feed.bithumb.com/notice/1650017
- Published: 2025-09-22 18:10:39
- Asset scope: `ADD`
- Scope: `withdrawal_only`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2025-09-22 18:10:00`
- Delta: `-39s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: Title: 애드(ADD) 출금 일시 중지 안내 URL Source: http://feed.bithumb.com/notice/1650017 Markdown Content: * [공지사항](https://feed.bithumb.com/notice) * [보도자료](https://feed.bithumb.com/press) * [가상자산 트렌드](https://feed.bithumb.com/trend) * [가상자산설명서](https://feed.bithumb.com/manual) * [주요내용설명서
- Pre-detectability: `low`
- Expected lead time: 사전 예고 거의 불가, 공지와 동시 포착
- Context: ADD 자산의 빗썸 출금 지갑 경로
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 동일 자산의 반복 점검 패턴과 재개 공지 이력
- Practical rule: ADD 자산의 빗썸 출금 지갑 경로는 체인 문제라기보다 거래소 내부 지갑 점검이어서 외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다.
- Case note: wallet system check라 외부 체인 모니터링보다 빗썸 자체 상태 감시가 핵심이다.
- Hard limit: 거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다.

### 1649832 폴리곤 에코시스템 토큰(POL) 입출금 일시 중지 안내 (09/11 재개)

- Official: https://feed.bithumb.com/notice/1649832
- Published: 2025-09-10 22:40:25
- Asset scope: `POL`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-09-10 22:40:00`
- Delta: `-25s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 폴리곤 에코시스템 토큰(POL)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**폴리곤 에코시스템 토큰(POL)** * 서비스 제한 범위 - 폴리곤 에코시스템 토큰(POL) 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: POL 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: POL 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1649774 스타크넷(STRK) 입출금 일시 중지 안내 (09/03 재개)

- Official: https://feed.bithumb.com/notice/1649774
- Published: 2025-09-02 15:56:36
- Asset scope: `STRK`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-09-02 15:55:00`
- Delta: `-96s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 스타크넷(STRK)메인넷 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**스타크넷(STRK)** * 서비스 제한 범위 - 스타크넷(STRK) - Starknet 네트워크 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Starknet
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Starknet에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Starknet 재발 사례라 `동일 체인 반복 장애` 자체를 prior risk로 높게 잡았어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1649671 저킷(ZRC) 입출금 일시 중지 안내 (09/02 재개)

- Official: https://feed.bithumb.com/notice/1649671
- Published: 2025-08-29 13:12:21
- Asset scope: `ZRC`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-08-29 13:12:00`
- Delta: `-21s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 저킷(ZRC)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**저킷(ZRC)** * 서비스 제한 범위 -저킷(ZRC)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Zircuit
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Zircuit에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Zircuit explorer block lag와 status 채널을 보면 notice 전에 이상 징후를 잡을 수 있는 유형이다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1649625 세이(SEI) 입출금 일시 중지 안내 (08/23 재개)

- Official: https://feed.bithumb.com/notice/1649625
- Published: 2025-08-23 02:00:00
- Asset scope: `SEI`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `network_issue`
- Stated stop: `2025-08-23 02:00:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 당신의 안전한 금융 파트너, 빗썸입니다. 세이(SEI)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**세이(SEI)** * 서비스 제한 범위 - 세이(SEI)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: SEI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: SEI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1649384 셀레스티아(TIA) 입출금 일시 중지 안내 (7/29 재개)

- Official: https://feed.bithumb.com/notice/1649384
- Published: 2025-07-29 00:49:55
- Asset scope: `TIA`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2025-07-29 00:50:00`
- Delta: `+5s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 대한민국 대표 거래소 빗썸입니다. 셀레스티아(TIA)지갑 시스템 점검에 따라, 안정적인 입출금 서비스 제공을 위해 아래와 같이 입출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. **[ 셀레스티아(TIA)입출금 일시 중지 안내 ]** * 대상 가상자산 -셀레스티아(TIA) * 입출금 중지 시점 **- 2025.07.29(화) 오전 12시 50분 (KST) 예정**
- Pre-detectability: `low`
- Expected lead time: 공개 신호만으로는 제한적
- Context: TIA 관련 네트워크/프로젝트
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 자산별 반복 중단 패턴과 프로젝트 공식 채널
- Practical rule: TIA 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다.
- Case note: 원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.
- Hard limit: 원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.

### 1649237 펀디에이아이(PUNDIAI) 입출금 일시 중지 안내 (7/25 출금 재개)

- Official: https://feed.bithumb.com/notice/1649237
- Published: 2025-07-12 19:30:05
- Asset scope: `PUNDIAI`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2025-07-12 19:30:00`
- Delta: `-5s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 펀디에이아이(PUNDIAI)컨트랙트 업그레이드로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**펀디에이아이(PUNDIAI)** * 서비스 제한 범위 - 펀디에이아이(PUNDIAI)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `low`
- Expected lead time: 공개 신호만으로는 제한적
- Context: PUNDIAI 관련 네트워크/프로젝트
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 자산별 반복 중단 패턴과 프로젝트 공식 채널
- Practical rule: PUNDIAI 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다.
- Case note: 원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.
- Hard limit: 원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.

### 1649062 플레어(FLR) 입출금 일시 중지 안내 (06/27 재개)

- Official: https://feed.bithumb.com/notice/1649062
- Published: 2025-06-26 14:04:45
- Asset scope: `FLR`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-06-26 14:05:00`
- Delta: `+15s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 플레어(FLR)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**플레어(FLR)** * 서비스 제한 범위 - 플레어(FLR)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Flare
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Flare에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Flare explorer, validator, status 계열 신호가 가장 중요한 선행 정보다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1648776 알렉스(ALEX) 유의촉구 및 알렉스(ALEX), 스택스(STX) 입출금 일시 중단 안내 (06/12 재개)

- Official: https://feed.bithumb.com/notice/1648776
- Published: 2025-06-06 20:15:05
- Asset scope: `ALEX,STX`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `implicit_on_notice`
- Trigger: `security_issue`
- Stated stop: `-`
- Delta: `-`
- Confidence: `medium`
- Inclusion reason: 원문 본문이 별도 미래 중지 시각 없이 공지와 함께 즉시형/무기한 중단 문구를 사용
- Evidence phrase: 이로 인해 알렉스(ALEX)의 가상자산의 시세 변동성 증대가 우려되어 알렉스(ALEX)에 대한 투자에 특히 유의하여 주시기 바랍니다. 또한 안정성 확보 시점까지 알렉스(ALEX)와 스택스(STX)에 대한 입출금 서비스가 일시 중단될 예정입니다
- Pre-detectability: `medium`
- Expected lead time: 수분~수시간 전 부분 선포착 가능
- Context: ALEX,STX 관련 네트워크/프로젝트
- Watch channels: 프로젝트 공식 X/Discord/GitHub 보안 공지; on-chain exploit alert, treasury/bridge 대량 이동 알림; 빗썸 공지 피드와 거래유의/유의촉구 공지
- Practical rule: ALEX,STX 관련 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하는 경우가 많아 exploit 알림과 공식 보안 채널을 먼저 봤어야 한다.
- Case note: 보안 이슈는 외부 신호는 먼저 보일 수 있지만 거래소 stop timing까지 맞히긴 어렵다.
- Hard limit: 거래소 내부 리스크 판단이 개입돼 exact stop time 예측은 어렵다.

### 1648710 레이(REI) 입출금 일시 중지 안내 (06/02 재개)

- Official: https://feed.bithumb.com/notice/1648710
- Published: 2025-05-31 11:43:30
- Asset scope: `REI`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-31 11:45:00`
- Delta: `+90s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 레이(REI)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**레이(REI)** * 서비스 제한 범위 - 레이(REI)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI Network
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: REI Network에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: REI 반복 장애 사례라 `재발 체인` 버킷에 올려두는 것이 맞았다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1648626 레이(REI) 입출금 일시 중지 안내 (5/27 재개)

- Official: https://feed.bithumb.com/notice/1648626
- Published: 2025-05-26 10:42:19
- Asset scope: `REI`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-26 10:42:00`
- Delta: `-19s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 레이(REI)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**레이(REI)** * 서비스 제한 범위 - 레이(REI)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: REI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648624 스택스(STX), 알렉스(ALEX) 입출금 일시 중지 안내 (05/26 재개)

- Official: https://feed.bithumb.com/notice/1648624
- Published: 2025-05-24 11:00:13
- Asset scope: `ALEX,STX`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-24 11:00:00`
- Delta: `-13s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 스택스(STX)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**스택스(STX), 알렉스(ALEX)** * 서비스 제한 범위 - 스택스(STX), 알렉스(ALEX)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: ALEX,STX 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: ALEX,STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648448 레이(REI) 입출금 일시 중지 안내 (5/20 재개)

- Official: https://feed.bithumb.com/notice/1648448
- Published: 2025-05-20 19:00:12
- Asset scope: `REI`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-20 19:00:00`
- Delta: `-12s`
- Confidence: `high`
- Inclusion reason: 공식 원문이 `오후 19시 00분`처럼 표기했지만, 정규화하면 공지 시각과 12초 차이의 near-immediate 케이스
- Evidence phrase: 레이(REI) 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지될 예정이며, 본문 중지 시점은 2025.05.20(화) 오후 19시 00분 예정으로 공지 시각과 사실상 동일하다.
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: REI 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: REI 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648435 스택스(STX), 알렉스(ALEX) 입출금 일시 중지 안내 (05/20 재개)

- Official: https://feed.bithumb.com/notice/1648435
- Published: 2025-05-20 08:29:21
- Asset scope: `ALEX,STX`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-20 08:30:00`
- Delta: `+39s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 스택스(STX)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**스택스(STX), 알렉스(ALEX)** * 서비스 제한 범위 - 스택스(STX), 알렉스(ALEX)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: ALEX,STX 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: ALEX,STX 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648422 멀티버스엑스(EGLD) 입출금 일시 중지 안내 (05/15 재개)

- Official: https://feed.bithumb.com/notice/1648422
- Published: 2025-05-14 23:05:44
- Asset scope: `EGLD`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-14 23:06:00`
- Delta: `+16s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 대한민국 대표 거래소 빗썸입니다. 멀티버스엑스(EGLD)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -**멀티버스엑스(EGLD)****** * 서비스 제한 범위 - 멀티버스엑스(EGLD) 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: EGLD 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: EGLD 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648414 바빌론(BABY) 입출금 일시 중지 안내 (05/13 재개)

- Official: https://feed.bithumb.com/notice/1648414
- Published: 2025-05-13 11:52:26
- Asset scope: `BABY`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2025-05-13 11:55:00`
- Delta: `+154s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 대한민국 대표 거래소 빗썸입니다. 바빌론(BABY) 네트워크(메인넷) 업그레이드 지원에 따라, 안정적인 입출금 서비스 제공을 위해 아래와 같이 입출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. **[ 바빌론(BABY) 입출금 일시 중지 안내 ]** * 대상 가상자산 - **바빌론(BABY)** * 입출금 중지 시점 - **2025.05.13(화) 오전 11시55분(KST) 예정**
- Pre-detectability: `low`
- Expected lead time: 공개 신호만으로는 제한적
- Context: BABY 관련 네트워크/프로젝트
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 자산별 반복 중단 패턴과 프로젝트 공식 채널
- Practical rule: BABY 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다.
- Case note: 원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.
- Hard limit: 원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.

### 1648402 쿠사마(KSM) 입출금 일시 중지 안내 (05/12 재개)

- Official: https://feed.bithumb.com/notice/1648402
- Published: 2025-05-10 08:15:01
- Asset scope: `KSM`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-05-10 08:15:00`
- Delta: `-1s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 대한민국 대표 거래소 빗썸입니다. 쿠사마(KSM) 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. **[ 쿠사마(KSM) 입출금 일시 중지 안내 ]** * 대상 가상자산 - 쿠사마**(KSM)** * 입출금 중지 시점 - **2025.05.10(토) 오전 08시 15분(KST)**
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: KSM 관련 네트워크/프로젝트
- Watch channels: 공식 explorer 최신 블록 시간, block lag, transaction failure; 공식 status/X/Discord/Telegram incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: KSM 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 `빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다.
- Case note: 체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.
- Hard limit: 정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.

### 1648132 코스모스(ATOM) 입출금 일시 중지 안내 (04/15 재개)

- Official: https://feed.bithumb.com/notice/1648132
- Published: 2025-04-15 00:53:21
- Asset scope: `ATOM`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-04-15 00:55:00`
- Delta: `+99s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 대한민국 대표 거래소 빗썸입니다. 코스모스(ATOM)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 -코스모스(ATOM) * 서비스 제한 범위 -코스모스(ATOM) 가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Cosmos Hub
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Cosmos Hub에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Cosmos Hub는 explorer, Mintscan, validator 공지, forum까지 같이 봐야 선포착 확률이 높다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1647090 월드코인(WLD) 입출금 일시 중지 안내 (02/27 재개)

- Official: https://feed.bithumb.com/notice/1647090
- Published: 2025-02-19 18:00:00
- Asset scope: `WLD`
- Scope: `deposit_withdrawal`
- Source coverage: `notice_scan_only`
- Classification: `explicit_near_immediate`
- Trigger: `unknown`
- Stated stop: `2025-02-19 18:00:00`
- Delta: `0s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 2024년 가입자 수 1위, 대한민국 대표 거래소 빗썸입니다. 월드코인(WLD)지갑 시스템점검에 따라, 안정적인 입출금 서비스 제공을 위해 아래와 같이 입출금이 일시 중지될 예정이오니 이용에 참고하여 주시기 바랍니다. **[ 월드코인(WLD) 입출금 일시 중지 안내 ]** * 대상 가상자산 - 월드코인(WLD) * 입출금 중지 시점 **- 2025.02.19(수) 오후 6시(KST) 예정***** Optimism, Ethereum 네트워크를 통한 입출금은 정상적으로 이용 가능**
- Pre-detectability: `low`
- Expected lead time: 공개 신호만으로는 제한적
- Context: WLD 관련 네트워크/프로젝트
- Watch channels: 빗썸 공지 피드; 빗썸 assetsstatus endpoint; 자산별 반복 중단 패턴과 프로젝트 공식 채널
- Practical rule: WLD 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다.
- Case note: 원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.
- Hard limit: 원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.

### 1647038 플로우(FLOW) 입출금 일시 중지 안내 (02/19 재개)

- Official: https://feed.bithumb.com/notice/1647038
- Published: 2025-02-18 20:00:19
- Asset scope: `FLOW`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-02-18 20:00:00`
- Delta: `-19s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안녕하세요. 2024년 가입자 수 1위, 대한민국 대표 거래소 빗썸입니다. 플로우(FLOW)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 - 플로우(FLOW) * 서비스 제한 범위 - 플로우(FLOW)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Flow
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Flow에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Flow 반복 사례라 network halt 재발 위험 체인으로 분류했어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1646858 아이오텍스(IOTX) 입출금 일시 중지 안내 (02/01 재개)

- Official: https://feed.bithumb.com/notice/1646858
- Published: 2025-01-31 18:42:09
- Asset scope: `IOTX`
- Scope: `deposit_withdrawal`
- Source coverage: `both`
- Classification: `explicit_near_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-01-31 18:45:00`
- Delta: `+171s`
- Confidence: `high`
- Inclusion reason: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류
- Evidence phrase: 안 녕하세요. 가장 많은 고객들이 선택한 1위 거래소 빗썸입니다! 아이오텍스(IOTX)네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지 될 예정입니다. * 대상 가상자산 - **아이오텍스(IOTX)** * 서비스 제한 범위 - 아이오텍스(IOTX)가상자산 입출금 * 입출금 중지 시점
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: IoTeX
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: IoTeX에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: IoTeX explorer, status, validator 채널이 조기 포착 포인트다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1646423 질리카(ZIL) 입출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1646423
- Published: 2025-01-16 02:20:40
- Asset scope: `ZIL`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2025-01-16 02:30:00`
- Delta: `+560s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Zilliqa
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Zilliqa에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: Zilliqa explorer, official status, validator 채널에서 halt를 먼저 잡을 수 있었다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1645260 스택스(STX), 알렉스(ALEX) 입출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1645260
- Published: 2024-11-27 11:12:24
- Asset scope: `STX,ALEX`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2024-11-27 11:13:00`
- Delta: `+36s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Stacks; ALEX는 STX 체인 의존
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Stacks; ALEX는 STX 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: ALEX 자체보다 STX 메인넷 halt를 먼저 감시했어야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1645244 수이(SUI), 루미웨이브(LWA) 입출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1645244
- Published: 2024-11-21 19:23:52
- Asset scope: `SUI,LWA`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `block_generation_stop`
- Stated stop: `2024-11-21 19:30:00`
- Delta: `+368s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Sui; LWA는 Sui 체인 의존
- Watch channels: 메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부; 공식 status/X/Discord/Telegram의 장애 공지; validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint
- Practical rule: Sui; LWA는 Sui 체인 의존에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, 공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다.
- Case note: LWA 자체보다 Sui 네트워크 블록 생성 중단을 감시해야 했다.
- Hard limit: 정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다.

### 1645183 제타체인(ZETA) 입출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1645183
- Published: 2024-11-01 11:55:09
- Asset scope: `ZETA`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `network_issue`
- Stated stop: `2024-11-01 11:55:00`
- Delta: `-9s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: ZetaChain
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: ZetaChain의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Case note: 네트워크 이슈형이라 ZetaScan, validator, status 공지가 선행 지표다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.

### 1645123 루나2(LUNA2) 입출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1645123
- Published: 2024-10-02 17:12:51
- Asset scope: `LUNA2`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `network_issue`
- Stated stop: `2024-10-02 17:13:00`
- Delta: `+9s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Terra 2.0
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: Terra 2.0의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Case note: Terra Finder와 validator 운영 채널에서 네트워크 이상을 먼저 볼 수 있었다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.

### 1645109 질리카(ZIL) 입출금 일시 중단 안내

- Official: https://feed.bithumb.com/notice/1645109
- Published: 2024-09-27 15:29:20
- Asset scope: `ZIL`
- Scope: `deposit_withdrawal`
- Source coverage: `legacy_only`
- Classification: `legacy_effective_immediate`
- Trigger: `network_issue`
- Stated stop: `2024-09-27 15:30:00`
- Delta: `+40s`
- Confidence: `medium`
- Inclusion reason: 기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스
- Evidence phrase: 기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스
- Pre-detectability: `high`
- Expected lead time: 수초~수시간 전 선포착 가능
- Context: Zilliqa
- Watch channels: 공식 explorer/RPC health, block lag, transaction failure rate; 공식 status/X/Discord/Telegram의 incident 공지; 빗썸 공지 피드와 assetsstatus endpoint
- Practical rule: Zilliqa의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 `빗썸 입출금 중단 가능성 높음`으로 봤어야 한다.
- Case note: 같은 체인 재발 사례라 ZIL은 반복 감시 우선순위가 높았어야 한다.
- Hard limit: 네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다.
