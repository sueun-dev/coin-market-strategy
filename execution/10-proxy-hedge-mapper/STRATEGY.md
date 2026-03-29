# 10. Proxy Hedge 매핑 전략서

## 목적
해외 선물 시장에 해당 코인이 **상장되지 않은 경우**, 같은 네트워크의 메이저 토큰으로 대체 헤지(proxy hedge)를 수행하기 위한 매핑 테이블과 로직을 관리한다.

## 왜 필요한가
- 소형 알트일수록 알파가 큼 (07번 필터 기준)
- 하지만 소형 알트일수록 해외 선물이 없을 확률 높음
- 선물 없이 현물만 잡으면 글로벌 가격 변동 리스크에 노출
- Proxy hedge로 **불완전하지만 유의미한** 방향성 헤지 가능

## 매핑 테이블

### Cosmos SDK 생태계
| 코인 (선물 없음) | Proxy Hedge 대상 | 상관계수 (예상) | 비고 |
|-----------------|------------------|---------------|------|
| OSMO | ATOM | 0.75~0.85 | 같은 Cosmos 생태계 |
| BAND | ATOM | 0.60~0.75 | Cosmos SDK 기반 |
| KAVA | ATOM | 0.65~0.80 | Cosmos SDK 기반 |
| AKT | ATOM | 0.70~0.80 | Cosmos SDK 기반 |
| SCRT | ATOM | 0.55~0.70 | Cosmos SDK 기반 |

### 독립 체인
| 코인 (선물 없음) | Proxy Hedge 대상 | 상관계수 (예상) | 비고 |
|-----------------|------------------|---------------|------|
| TT (ThunderCore) | ETH 또는 BTC | 0.40~0.60 | 독립 체인, 약한 상관 |
| FLOW | ETH | 0.50~0.65 | L1 체인 |
| QTUM | BTC | 0.55~0.70 | PoS/PoW 하이브리드 |
| HBAR | BTC | 0.50~0.65 | 독립 DLT |

### EVM 호환 체인
| 코인 (선물 없음) | Proxy Hedge 대상 | 상관계수 (예상) | 비고 |
|-----------------|------------------|---------------|------|
| KAIA | ETH | 0.60~0.75 | EVM 호환 |
| 0G | ETH | 0.50~0.65 | AI+블록체인 |
| STORY | ETH | 0.45~0.60 | IP 체인 |

## 핵심 로직

### 1. 선물 존재 여부 확인
```
해당 코인이 아래 거래소에 선물 상장되어 있는지 확인:
  1. 바이낸스 USDT 무기한
  2. OKX USDT 무기한
  3. Bybit USDT 무기한

하나라도 있으면 → 직접 헤지 (proxy 불필요)
모두 없으면 → proxy hedge 매핑 참조
```

### 2. Proxy 토큰 선택 기준
```
우선순위:
  1. 같은 네트워크/생태계 메이저 토큰 (ATOM for Cosmos, ETH for EVM)
  2. 같은 섹터 메이저 토큰 (DeFi→DeFi, L1→L1)
  3. BTC (최후 수단, 시장 전체 방향성 헤지)

선택 기준:
  - 상관계수 > 0.5 (최소 기준)
  - 선물 유동성 충분 (OI > $10M)
  - 스프레드 작음
```

### 3. 베타 조정 사이즈
```
proxy hedge는 1:1 대응이 아니므로 베타 조정 필요:

hedge_qty = domestic_qty × (coin_beta / proxy_beta) × correlation

예시:
  TT 국내 롱 $1000
  TT-ETH 상관계수: 0.55
  TT 베타: 1.8, ETH 베타: 1.0
  hedge_qty = $1000 × (1.8/1.0) × 0.55 = $990 ETH 숏

→ 과소 헤지보다 과대 헤지가 안전 (프리미엄 캡처 목적이므로)
```

### 4. 상관계수 실시간 갱신
```
7일/30일/90일 롤링 상관계수 계산
매일 갱신

상관계수 급락 시 (< 0.3):
  → proxy hedge 신뢰도 "low"로 하향
  → 포지션 사이즈 축소 권고
  → 대체 proxy 토큰 제안
```

## 출력
```json
{
  "ticker": "TT",
  "futures_available": false,
  "proxy_hedge": {
    "proxy_ticker": "ETH",
    "proxy_exchange": "binance",
    "correlation_7d": 0.58,
    "correlation_30d": 0.52,
    "beta_ratio": 1.8,
    "recommended_hedge_ratio": 0.99,
    "confidence": "medium",
    "alternatives": [
      {"ticker": "BTC", "correlation_30d": 0.45}
    ]
  }
}
```

## 데이터 의존성
- `19-data-registry`: 해외 선물 목록, 코인 가격 히스토리 (상관계수 계산용)
- `09-delta-neutral-position`: proxy hedge 정보 요청

## 갱신 주기
- 선물 상장 여부: **일 1회** 체크
- 상관계수: **일 1회** 갱신
- 매핑 테이블: **수동 관리** + 신규 상장 시 자동 탐색

## 리스크
- proxy hedge는 완벽한 헤지가 아님 → 잔여 리스크 존재
- 상관계수가 비선형적으로 변할 수 있음 (급등/급락 시)
- 포지션 사이즈를 작게 유지하여 리스크 관리
