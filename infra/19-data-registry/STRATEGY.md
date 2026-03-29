# 19. Data Registry System Strategy

## Purpose
**Centrally manage static/semi-static data** that the entire pipeline depends on.
All systems (01~18) reference this registry. Without data, no detection, filtering, or execution is possible.

## 6 Types of Managed Data

### 1. Listed Coin List + GitHub Repo Mapping
```
Coins listed on Upbit/Bithumb with their own mainnet projects (~50-100)

Schema:
{
  "ticker": "ATOM",
  "coin_name": "Cosmos Hub",
  "network": "cosmos",
  "network_type": "own_mainnet",  // own_mainnet | erc20 | bep20 | spl | ...
  "github_repo": "cosmos/gaia",
  "governance_type": "cosmos_sdk",  // cosmos_sdk | evm_governor | custom | none
  "governance_endpoint": "https://cosmos-rpc.example.com/cosmos/gov/v1/proposals",
  "listed_exchanges": {
    "upbit": {"market": "KRW-ATOM", "listed_at": "2019-10-01"},
    "bithumb": {"market": "ATOM_KRW", "listed_at": "2019-08-01"}
  },
  "upbit_exclusive": false,
  "bithumb_exclusive": false,
  "caution_status": null  // null | "caution" | "investment_warning"
}

Update frequency: Once daily (reflect listings/delistings)
Source: Upbit API, Bithumb API, manual management
```

### 2. Per-chain RPC Endpoints + Average Block Time
```
Schema:
{
  "chain": "cosmos",
  "rpc_endpoints": [
    {"url": "https://rpc.cosmos.network", "priority": 1, "status": "active"},
    {"url": "https://cosmos-rpc.publicnode.com", "priority": 2, "status": "active"}
  ],
  "rpc_type": "tendermint",  // tendermint | evm | solana | sui | aptos | flow | custom
  "avg_block_time_seconds": 6.5,
  "block_time_stddev": 0.8,
  "affected_tickers": ["ATOM"],
  "last_updated": "2026-03-29"
}

Update frequency:
  - RPC status: Health check every hour
  - Block time statistics: Recalculated once daily
  - Endpoint additions/removals: Manual
```

### 3. Exchange Hot Wallet + Cold Wallet Address Labeling
```
Schema:
{
  "exchange": "upbit",
  "chain": "ethereum",
  "wallets": {
    "hot": [
      {"address": "0xabc...", "label": "Upbit Hot Wallet 1", "source": "arkham"},
      {"address": "0xdef...", "label": "Upbit Hot Wallet 2", "source": "etherscan"}
    ],
    "cold": [
      {"address": "0x123...", "label": "Upbit Cold Wallet", "source": "arkham"}
    ]
  },
  "avg_daily_outflow_usd": 5000000,
  "last_verified": "2026-03-15"
}

Target chains:
  Ethereum, Solana, Bitcoin, Tron, Polygon, Cosmos,
  + All own-mainnet chains listed on Upbit/Bithumb

Update frequency:
  - Address labeling: Monthly manual verification + Arkham cross-check
  - Average outflow: Recalculated weekly
Source: Arkham Intelligence, Etherscan Labels, Solscan, respective Explorers
```

### 4. Per-coin Market Cap, Volume, Korean Trading Ratio
```
Schema:
{
  "ticker": "TT",
  "market_cap_krw": 84000000000,
  "market_cap_usd": 62000000,
  "daily_volume": {
    "upbit_krw": 3500000000,
    "bithumb_krw": 800000000,
    "global_usd": 5000000
  },
  "kr_volume_ratio": 0.63,  // (upbit + bithumb) / global
  "rank_by_market_cap": 350,
  "last_updated": "2026-03-29T06:00:00Z"
}

Update frequency: Real-time at 5-minute intervals
Source: CoinGecko API, CoinMarketCap API, Upbit/Bithumb API
```

### 5. Overseas Futures Availability + Proxy Hedge Mapping
```
Schema:
{
  "ticker": "TT",
  "futures": {
    "binance": null,
    "okx": null,
    "bybit": null
  },
  "futures_available": false,
  "proxy_hedge": {
    "recommended": "ETH",
    "correlation_30d": 0.52,
    "beta_ratio": 1.8,
    "alternatives": ["BTC"]
  }
}

Update frequency:
  - Futures listing status: Once daily
  - Correlation coefficients: Once daily
Source: Binance/OKX/Bybit futures listing APIs
```

### 6. Exchange Announcement API/RSS Endpoints
```
Schema:
{
  "exchange": "binance",
  "type": "overseas",
  "announcement_sources": [
    {
      "type": "api",
      "url": "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
      "method": "POST",
      "polling_interval_min": 5
    },
    {
      "type": "rss",
      "url": "https://www.binance.com/en/support/announcement/rss",
      "polling_interval_min": 5
    }
  ],
  "keywords": {
    "suspension": ["suspend", "deposit", "withdrawal", "maintenance"],
    "upgrade": ["upgrade", "hardfork", "network update"],
    "caution": ["delist", "remove", "trading pair"]
  }
}

Additional domestic exchanges:
  - Upbit: Announcement API + investment caution notices
  - Bithumb: Announcement page crawling
  - DAXA: Announcement page crawling

Update frequency: Manual management (when API changes)
```

## Initial Data Construction Plan

### Phase 1 (Essential, Immediate)
```
1. Collect Upbit/Bithumb listed coin list (API)
2. Identify own-mainnet coins + GitHub repo mapping (manual)
3. Major chain RPC endpoints (10 chains)
4. Collect overseas futures listing (API)
```

### Phase 2 (Important, Within 1 Week)
```
5. Hot wallet/cold wallet address labeling (Arkham-based)
6. Expand full chain RPC endpoints (30~50 chains)
7. Set up exchange announcement crawling endpoints
8. Collect price history for correlation calculation
```

### Phase 3 (Operations, Ongoing)
```
9. Real-time market cap/volume/Korean ratio pipeline
10. Periodic address labeling verification
11. Auto-detect and reflect new listings/delistings
```

## Data Storage
```
Storage: PostgreSQL or JSON file-based
Cache: Redis (real-time data)
Backup: Once daily

Directory structure:
  19-data-registry/
  ├── data/
  │   ├── coins.json          # Listed coins + GitHub repo
  │   ├── chains.json         # RPC + block time
  │   ├── wallets.json        # Hot/cold wallet addresses
  │   ├── market_data.json    # Market cap/volume (real-time updates)
  │   ├── futures.json        # Futures + proxy hedge
  │   └── announcements.json  # Announcement endpoints
  ├── scripts/
  │   ├── fetch_coins.py      # Listed coin collection
  │   ├── fetch_market.py     # Real-time market cap/volume
  │   ├── fetch_futures.py    # Futures list update
  │   └── verify_wallets.py   # Wallet address verification
  └── STRATEGY.md
```

## Dependency Map (Systems that reference this registry)
- `01`: Per-chain RPC, governance endpoints, listed coins
- `02`: GitHub repo mapping
- `03`: Exchange announcement endpoints, listed coins
- `04`: Per-chain RPC, average block time
- `05`: Hot wallet address labeling
- `06`: Hot wallet + cold wallet address labeling
- `07`: Market cap, volume, Korean ratio, network type, futures availability
- `10`: Futures list, proxy hedge mapping, correlation coefficients
- `11`: Upbit/Bithumb API endpoints
- `12`: Price data sources

---

# 19. 데이터 사전 구축 시스템 전략서

## 목적
전체 파이프라인이 의존하는 **정적/반정적 데이터를 중앙 관리**한다.
모든 시스템(01~18)이 이 레지스트리를 참조. 데이터가 없으면 감지도, 필터링도, 실행도 불가.

## 관리 데이터 6종

### 1. 상장 코인 목록 + GitHub Repo 매핑
```
업비트/빗썸 상장 코인 중 자체 메인넷 프로젝트 (~50-100개)

스키마:
{
  "ticker": "ATOM",
  "coin_name": "Cosmos Hub",
  "network": "cosmos",
  "network_type": "own_mainnet",  // own_mainnet | erc20 | bep20 | spl | ...
  "github_repo": "cosmos/gaia",
  "governance_type": "cosmos_sdk",  // cosmos_sdk | evm_governor | custom | none
  "governance_endpoint": "https://cosmos-rpc.example.com/cosmos/gov/v1/proposals",
  "listed_exchanges": {
    "upbit": {"market": "KRW-ATOM", "listed_at": "2019-10-01"},
    "bithumb": {"market": "ATOM_KRW", "listed_at": "2019-08-01"}
  },
  "upbit_exclusive": false,
  "bithumb_exclusive": false,
  "caution_status": null  // null | "유의종목" | "투자경고"
}

갱신 주기: 일 1회 (상장/상폐 반영)
소스: 업비트 API, 빗썸 API, 수동 관리
```

### 2. 체인별 RPC 엔드포인트 + 평균 블록타임
```
스키마:
{
  "chain": "cosmos",
  "rpc_endpoints": [
    {"url": "https://rpc.cosmos.network", "priority": 1, "status": "active"},
    {"url": "https://cosmos-rpc.publicnode.com", "priority": 2, "status": "active"}
  ],
  "rpc_type": "tendermint",  // tendermint | evm | solana | sui | aptos | flow | custom
  "avg_block_time_seconds": 6.5,
  "block_time_stddev": 0.8,
  "affected_tickers": ["ATOM"],
  "last_updated": "2026-03-29"
}

갱신 주기:
  - RPC 상태: 1시간마다 health check
  - 블록타임 통계: 일 1회 재계산
  - 엔드포인트 추가/제거: 수동
```

### 3. 거래소 핫월렛 + 콜드월렛 주소 라벨링
```
스키마:
{
  "exchange": "upbit",
  "chain": "ethereum",
  "wallets": {
    "hot": [
      {"address": "0xabc...", "label": "Upbit Hot Wallet 1", "source": "arkham"},
      {"address": "0xdef...", "label": "Upbit Hot Wallet 2", "source": "etherscan"}
    ],
    "cold": [
      {"address": "0x123...", "label": "Upbit Cold Wallet", "source": "arkham"}
    ]
  },
  "avg_daily_outflow_usd": 5000000,
  "last_verified": "2026-03-15"
}

대상 체인:
  Ethereum, Solana, Bitcoin, Tron, Polygon, Cosmos,
  + 업비트/빗썸 상장 자체 메인넷 전체

갱신 주기:
  - 주소 라벨링: 월 1회 수동 검증 + Arkham 크로스체크
  - 평균 유출량: 주 1회 재계산
소스: Arkham Intelligence, Etherscan Labels, Solscan, 각 Explorer
```

### 4. 코인별 시총, 거래량, 한국 거래 비중
```
스키마:
{
  "ticker": "TT",
  "market_cap_krw": 84000000000,
  "market_cap_usd": 62000000,
  "daily_volume": {
    "upbit_krw": 3500000000,
    "bithumb_krw": 800000000,
    "global_usd": 5000000
  },
  "kr_volume_ratio": 0.63,  // (upbit + bithumb) / global
  "rank_by_market_cap": 350,
  "last_updated": "2026-03-29T06:00:00Z"
}

갱신 주기: 5분 간격 실시간
소스: CoinGecko API, CoinMarketCap API, 업비트/빗썸 API
```

### 5. 해외 선물 존재 여부 + Proxy Hedge 매핑
```
스키마:
{
  "ticker": "TT",
  "futures": {
    "binance": null,
    "okx": null,
    "bybit": null
  },
  "futures_available": false,
  "proxy_hedge": {
    "recommended": "ETH",
    "correlation_30d": 0.52,
    "beta_ratio": 1.8,
    "alternatives": ["BTC"]
  }
}

갱신 주기:
  - 선물 상장 여부: 일 1회
  - 상관계수: 일 1회
소스: 바이낸스/OKX/Bybit 선물 목록 API
```

### 6. 거래소 공지 API/RSS 엔드포인트
```
스키마:
{
  "exchange": "binance",
  "type": "overseas",
  "announcement_sources": [
    {
      "type": "api",
      "url": "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
      "method": "POST",
      "polling_interval_min": 5
    },
    {
      "type": "rss",
      "url": "https://www.binance.com/en/support/announcement/rss",
      "polling_interval_min": 5
    }
  ],
  "keywords": {
    "suspension": ["suspend", "deposit", "withdrawal", "maintenance"],
    "upgrade": ["upgrade", "hardfork", "network update"],
    "caution": ["delist", "remove", "trading pair"]
  }
}

국내 거래소 추가:
  - 업비트: 공지사항 API + 투자유의 공지
  - 빗썸: 공지사항 페이지 크롤링
  - DAXA: 공지 페이지 크롤링

갱신 주기: 수동 관리 (API 변경 시)
```

## 데이터 초기 구축 계획

### Phase 1 (필수, 즉시)
```
1. 업비트/빗썸 상장 코인 목록 수집 (API)
2. 자체 메인넷 코인 식별 + GitHub repo 매핑 (수동)
3. 주요 체인 RPC 엔드포인트 (10개 체인)
4. 해외 선물 목록 수집 (API)
```

### Phase 2 (중요, 1주 내)
```
5. 핫월렛/콜드월렛 주소 라벨링 (Arkham 기반)
6. 전체 체인 RPC 엔드포인트 확장 (30~50개)
7. 거래소 공지 크롤링 엔드포인트 세팅
8. 상관계수 계산용 가격 히스토리 수집
```

### Phase 3 (운영, 지속)
```
9. 실시간 시총/거래량/한국비중 파이프라인
10. 주소 라벨링 주기적 검증
11. 신규 상장/상폐 자동 감지 및 반영
```

## 데이터 저장
```
저장소: PostgreSQL 또는 JSON 파일 기반
캐시: Redis (실시간 데이터)
백업: 일 1회

디렉토리 구조:
  19-data-registry/
  ├── data/
  │   ├── coins.json          # 상장 코인 + GitHub repo
  │   ├── chains.json         # RPC + 블록타임
  │   ├── wallets.json        # 핫/콜드 월렛 주소
  │   ├── market_data.json    # 시총/거래량 (실시간 갱신)
  │   ├── futures.json        # 선물 + proxy hedge
  │   └── announcements.json  # 공지 엔드포인트
  ├── scripts/
  │   ├── fetch_coins.py      # 상장 코인 수집
  │   ├── fetch_market.py     # 시총/거래량 실시간
  │   ├── fetch_futures.py    # 선물 목록 갱신
  │   └── verify_wallets.py   # 월렛 주소 검증
  └── STRATEGY.md
```

## 의존 관계 (이 레지스트리를 참조하는 시스템)
- `01`: 체인별 RPC, 거버넌스 엔드포인트, 상장 코인
- `02`: GitHub repo 매핑
- `03`: 거래소 공지 엔드포인트, 상장 코인
- `04`: 체인별 RPC, 평균 블록타임
- `05`: 핫월렛 주소 라벨링
- `06`: 핫월렛 + 콜드월렛 주소 라벨링
- `07`: 시총, 거래량, 한국 비중, 네트워크 타입, 선물 존재
- `10`: 선물 목록, proxy hedge 매핑, 상관계수
- `11`: 업비트/빗썸 API 엔드포인트
- `12`: 가격 데이터 소스
