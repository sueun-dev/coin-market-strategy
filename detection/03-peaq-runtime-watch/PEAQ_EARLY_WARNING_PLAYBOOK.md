# PEAQ Early Warning Playbook

이 문서는 `PEAQ` 체인에서 거래소 공지보다 먼저 이상 신호를 잡기 위한 별도 감시 설계다.
이 감시기는 `정량 신호만` 사용한다.

핵심 결론:

- `01`에 붙이지 않는다.
- `PEAQ 전용 감시기`로 분리한다.
- 현재 구현은 `HTTP 다중 endpoint latest/finalized quorum` 기준이다.
- 언어 신호는 자동 경보 조건에서 제외한다.

## 왜 별도 감시기로 빼야 하나

- PEAQ는 `거버넌스/release`보다 `runtime stall`이 핵심이다.
- `01`의 일반 체인 업그레이드 forecaster와 성격이 다르다.
- 알림 임계값과 상태 머신도 별도다.

## 연구 근거

- 빗썸 PEAQ 공지: [1652398](https://feed.bithumb.com/notice/1652398)
- Bitget PEAQ 공지: [Suspension of Deposit and Withdrawal Services of PEAQ Network](https://www.bitget.com/support/articles/12560603881252)
- 공식 문서: [Connecting to peaq](https://docs.peaq.xyz/build/getting-started/connecting-to-peaq)

로컬 정리 기준:

- 빗썸 `high` 사례 36건의 공지-중지 차이 중앙값은 `4.5초`
- PEAQ public RPC live 샘플 기준 latest lag 중앙값은 `1.72초`, p90은 `16.25초`
- 따라서 `lag 단독`이 아니라 `quorum + no-advance`가 핵심

## 봐야 하는 것

1. `newHeads quorum`
현재 구현에선 `latest block`이 실제로 전진하는지

2. `finalized head`
finality가 비정상적으로 밀리는지

3. `HTTP latest/finalized`
다중 public RPC에서 동일하게 멈추는지

4. `endpoint divergence`
서로 다른 public endpoint가 같은 높이를 보고 있는지

5. `RPC health`
timeout, stale response, endpoint failure가 다수로 발생하는지

6. `block interval anomaly`
완전 halt는 아니더라도 블록 간격이 평소보다 비정상적으로 길어지는지

## 상태 기준

- `observe`
과반 endpoint가 `2회 연속` no-advance
또는 endpoint spread가 임계치를 초과

- `warning`
과반 endpoint가 `3회 연속` no-advance
그리고 quorum head age가 `24초 이상`

- `critical`
과반 endpoint가 `5회 연속` no-advance
그리고 quorum head age가 `45초 이상`

## 텔레그램

- `observe`는 내부 상태만 저장
- `warning`부터 텔레그램 발송
- `critical`은 즉시 승격 발송
- 같은 단계는 `10~15분 cooldown` 권장
- 언어 신호나 거래소 공지는 자동 발송 트리거로 사용하지 않음

## 남은 확장점

- `system_health`
- `system_syncState`
- `block interval anomaly`
- explorer cross-check
- `WSS newHeads/finalized`
- 복구 알림 자동화
