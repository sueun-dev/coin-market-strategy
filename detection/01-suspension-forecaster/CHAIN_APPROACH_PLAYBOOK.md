# 01 체인별 접근 플레이북

## 목적

이 문서는 `01`이 각 체인에 대해 어떤 upstream을 1순위로 봐야 거래소 입출금 정지 공지보다 빨라질 가능성이 가장 높은지 정리한 설계 문서다.

여기서 `Best`는 `가장 구현이 쉬운 방법`이 아니라 `가장 빨라질 가능성이 높은 공개 소스 조합`을 뜻한다.

## 읽는 법

- `1순위 소스`: 가장 먼저 봐야 하는 upstream
- `보조 소스`: 1순위 신호를 확증하거나 시간 정보를 보강하는 소스
- `01 베스트 구현`: 실제 `01`에서 가져가야 할 수집 방식
- `현재 갭`: 지금 구현 대비 부족한 점

## 공통 원칙

1. `거래소 텔레그램`과 `거래소 공지`는 알파 소스가 아니라 확인 소스다.
2. `GitHub release`만으로 끝내지 말고, 가능한 체인은 `거버넌스 / 업그레이드 문서 / status`까지 같이 봐야 한다.
3. `입출금 정지`는 업그레이드뿐 아니라 `브리지 이슈`, `주소 변경`, `토큰 스왑`, `인프라 장애`로도 나오므로 체인군별 접근이 달라야 한다.

## A. Cosmos / CometBFT 계열

이 그룹은 가장 좋은 방식이 비교적 명확하다.

- 1순위: `거버넌스 proposal submit / voting start` 이벤트
- 2순위: `GitHub release`
- 3순위: `validator upgrade docs`
- 베스트 구현: `CometBFT WebSocket + gov REST + GitHub conditional polling`

| 티커 | 체인 | 국내 거래소 | 1순위 소스 | 보조 소스 | 01 베스트 구현 | 현재 갭 |
|---|---|---|---|---|---|---|
| `ATOM` | Cosmos Hub | 업비트, 빗썸 | 온체인 gov proposal | `cosmos/gaia` release | `gov WebSocket + proposal detail fetch + release watcher` | WebSocket 미구현 |
| `SEI` | Sei Network | 업비트, 빗썸 | 온체인 gov proposal | `sei-protocol/sei-chain` release | `gov WebSocket + v1beta1 fallback + release watcher` | WebSocket 미구현 |
| `INJ` | Injective | 업비트, 빗썸 | `GitHub release`와 gov를 동시에 봐야 함 | validator docs | `release fast poll + gov WebSocket` | validator docs 미연결 |
| `KAVA` | Kava | 업비트, 빗썸 | 온체인 gov proposal | `Kava-Labs/kava` release | `gov WebSocket + release watcher` | WebSocket 미구현 |
| `AKT` | Akash | 업비트 | 온체인 gov proposal | validator docs | `gov WebSocket + upgrade-doc watcher` | GitHub/doc 보강 필요 |
| `AXL` | Axelar | 업비트 | 온체인 gov proposal | `axelarnetwork/axelar-core` release | `gov WebSocket + release watcher` | docs/status 미연결 |
| `TIA` | Celestia | 업비트 | 온체인 gov proposal | `celestiaorg/celestia-app` release | `gov WebSocket + release watcher + rc noise filter` | release 노이즈 필터 강화 필요 |
| `CRO` | Crypto.com Chain | 업비트 | 온체인 gov proposal | `crypto-org-chain/chain-main` release | `gov WebSocket + release watcher` | docs/status 미연결 |
| `MED` | MediBloc | 업비트 | 온체인 gov proposal | `medibloc/panacea-core` release | `gov WebSocket + release watcher` | docs 미연결 |
| `OSMO` | Osmosis | 빗썸 | 온체인 gov proposal | `osmosis-labs/osmosis` release | `gov WebSocket + release watcher` | WebSocket 미구현 |
| `BAND` | Band Protocol | 빗썸 | 온체인 gov proposal | `bandprotocol/chain` release | `gov WebSocket + release watcher` | WebSocket 미구현 |
| `STRD` | Stride | 빗썸 | 온체인 gov proposal | validator docs | `gov WebSocket + upgrade-doc watcher` | GitHub/doc 보강 필요 |
| `STARS` | Stargaze | 빗썸 | 온체인 gov proposal | validator docs | `gov WebSocket + upgrade-doc watcher` | GitHub/doc 보강 필요 |
| `IRIS` | IRISnet | 미검증 | 온체인 gov proposal | `irisnet/irishub` release | `gov WebSocket + release watcher` | 지금은 GitHub만 연결됨 |

## B. 거버넌스 / 프로토콜 업그레이드 체인

이 그룹은 GitHub보다 `체인 자체의 업그레이드 결정 프로세스`가 더 중요하다.

| 티커 | 체인 | 국내 거래소 | 1순위 소스 | 보조 소스 | 01 베스트 구현 | 현재 갭 |
|---|---|---|---|---|---|---|
| `DOT` | Polkadot | 업비트, 빗썸 | OpenGov runtime upgrade referendum | `paritytech/polkadot-sdk` release | `referendum feed poll + release watcher` | 지금은 GitHub만 봄 |
| `XTZ` | Tezos | 업비트, 빗썸 | amendment voting stage | `tezos/tezos` release | `TzKT stage watcher + release watcher` | 지금은 GitHub만 봄 |
| `APT` | Aptos | 업비트, 빗썸 | governance proposal / upgrade schedule | `aptos-labs/aptos-core` release | `proposal watcher + release watcher` | 지금은 GitHub만 봄 |
| `SUI` | Sui | 업비트, 빗썸 | protocol version / epoch transition signal | `MystenLabs/sui` release | `protocol-version watcher + release watcher` | 지금은 GitHub만 봄 |
| `ALGO` | Algorand | 업비트 | consensus next-version fields | `algorand/go-algorand` release | `algod consensus field watcher + release watcher` | 지금은 GitHub만 봄 |
| `ADA` | Cardano | 업비트, 빗썸 | hard fork / governance transition signal | `IntersectMBO/cardano-node` release | `governance/hard-fork watcher + SPO release watcher` | 지금은 GitHub만 봄 |
| `ICX` | ICON | 업비트, 빗썸 | network proposal | `icon-project/goloop` release | `proposal watcher + release watcher` | 지금은 GitHub만 봄 |
| `CELO` | Celo | 업비트 | governance contract proposal | `celo-org/celo-blockchain` release | `governance contract watcher + release watcher` | 지금은 GitHub만 봄 |
| `XRP` | XRP Ledger | 미검증 | amendment activation state | `ripple/rippled` release | `amendment-state watcher + release watcher` | 지금은 GitHub만 봄 |
| `XLM` | Stellar | 미검증 | protocol vote / upgrade activation | `stellar/stellar-core` release | `protocol-upgrade watcher + release watcher` | 지금은 GitHub만 봄 |

## C. L2 / 브리지 민감 체인

이 그룹은 단순 release보다 `bridge`, `sequencer`, `status page`, `governance forum`이 더 중요하다.

| 티커 | 체인 | 국내 거래소 | 1순위 소스 | 보조 소스 | 01 베스트 구현 | 현재 갭 |
|---|---|---|---|---|---|---|
| `POL` | Polygon PoS | 미검증 | official upgrade forum / validator notice | `maticnetwork/bor` release, status page | `forum watcher + release watcher + status watcher` | 지금은 GitHub만 봄 |
| `ARB` | Arbitrum | 미검증 | governance forum / upgrade notice | `OffchainLabs/nitro` release, bridge status | `forum watcher + bridge status + release watcher` | 지금은 GitHub만 봄 |
| `OP` | Optimism | 미검증 | governance forum / chain upgrade notice | `ethereum-optimism/optimism` release, status page | `forum watcher + status watcher + release watcher` | 지금은 GitHub만 봄 |

## D. Release-first / Validator-docs-first 체인

이 그룹은 온체인 거버넌스보다 `node release`, `validator docs`, `official status`가 더 빠른 편이다.

| 티커 | 체인 | 국내 거래소 | 1순위 소스 | 보조 소스 | 01 베스트 구현 | 현재 갭 |
|---|---|---|---|---|---|---|
| `SOL` | Solana | 미검증 | validator upgrade docs | `anza-xyz/agave` release, status | `validator-doc watcher + release watcher + status watcher` | 지금은 GitHub만 봄 |
| `AVAX` | Avalanche | 미검증 | validator upgrade docs / ACP | `ava-labs/avalanchego` release, status | `docs/forum watcher + release watcher` | 지금은 GitHub만 봄 |
| `FLOW` | Flow | 미검증 | spork / upgrade schedule docs | `onflow/flow-go` release, status | `schedule watcher + release watcher + status watcher` | 지금은 GitHub만 봄 |
| `QTUM` | Qtum | 미검증 | official upgrade announcement | `qtumproject/qtum` release | `announcement/doc watcher + release watcher` | 지금은 GitHub만 봄 |
| `IP` | Story Protocol | 미검증 | validator upgrade docs | `piplabs/story` release | `validator-doc watcher + release watcher` | 지금은 GitHub만 봄 |
| `NEAR` | NEAR | 미검증 | governance / RFC forum | `near/nearcore` release, status | `forum watcher + release watcher + status watcher` | 지금은 GitHub만 봄 |
| `STX` | Stacks | 미검증 | SIP / protocol upgrade notice | `stacks-network/stacks-core` release | `SIP watcher + release watcher` | 지금은 GitHub만 봄 |
| `IOTA` | IOTA | 미검증 | upgrade docs / network status | node release | `status/doc watcher + release watcher` | 현재 repo 선택이 약함 |
| `ZIL` | Zilliqa | 미검증 | validator upgrade notice | `Zilliqa/Zilliqa` release, status | `doc watcher + release watcher + status watcher` | 지금은 GitHub만 봄 |
| `CKB` | Nervos CKB | 미검증 | RFC / hardfork notice | `nervosnetwork/ckb` release | `RFC watcher + release watcher` | 지금은 GitHub만 봄 |
| `VET` | VeChain | 미검증 | official upgrade docs | `vechain/thor` release, status | `doc watcher + release watcher + status watcher` | 지금은 GitHub만 봄 |

## E. 현재 01 우선순위

문서상 `Best`와 별개로, 실제 구현 우선순위는 아래가 맞다.

### P0

바로 강화해야 하는 체인들.

- `ATOM`
- `SEI`
- `INJ`
- `KAVA`
- `AXL`
- `TIA`
- `OSMO`
- `BAND`
- `DOT`
- `XTZ`
- `APT`
- `SUI`
- `ADA`

이유:

1. 국내 상장 relevance가 높다
2. 공개 upstream이 비교적 명확하다
3. 거래소보다 앞설 확률이 높다

### P1

다음으로 붙일 체인들.

- `AKT`
- `CRO`
- `MED`
- `STRD`
- `STARS`
- `ALGO`
- `ICX`
- `CELO`
- `SOL`
- `POL`
- `ARB`
- `OP`
- `AVAX`

### P2

문서/상태페이지/별도 포럼 연결이 필요한 체인들.

- `FLOW`
- `QTUM`
- `IP`
- `XRP`
- `XLM`
- `NEAR`
- `STX`
- `IOTA`
- `IRIS`
- `ZIL`
- `CKB`
- `VET`

## 01이 지금 당장 버려야 하는 접근

1. `모든 체인을 GitHub release 하나로 퉁치는 방식`
2. `거래소 텔레그램을 선행 소스로 쓰는 방식`
3. `거버넌스 PASSED`만 보고 늦게 보내는 방식

## 최종 결론

체인별 베스트 접근은 하나로 통일되지 않는다.

- Cosmos 계열은 `거버넌스 이벤트`
- 거버넌스 체인은 `업그레이드 결정 프로세스`
- L2는 `forum + bridge/status`
- 나머지는 `validator docs + release + status`

즉 `01`의 정답은 단일 폴러가 아니라 `체인군별 멀티소스 플레이북`이다.
