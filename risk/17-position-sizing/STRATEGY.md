# 17. 포지션 사이징 전략서

## 목적
개별 포지션과 전체 포트폴리오의 **자본 배분을 제한**하여 리스크를 관리한다.
소형 알트 선물의 유동성(OI) 확인 및 슬리피지 경고도 담당.

## 기본 규칙
```
1. 단일 포지션: 전체 자본의 5~10% 이내
2. 동시 활성 포지션 합계: 전체 자본의 30% 이내
3. 숏 마진 포함 총 투입: 전체 자본의 50% 이내
```

## 핵심 로직

### 1. 단일 포지션 사이즈 산출
```
기본 사이즈 = total_capital × base_allocation_pct

base_allocation_pct는 타겟 등급별:
  S등급: 10% (최고 확신)
  A등급: 7%
  B등급: 5%
  C등급: 3%

시그널 강도 보정:
  confidence == "high": × 1.0
  confidence == "medium": × 0.7
  confidence == "low": × 0.5

최종 사이즈:
  position_size = total_capital × base_allocation_pct × confidence_multiplier

예시:
  자본 1억원, S등급, high confidence
  position_size = 1억 × 10% × 1.0 = 1000만원
  → 국내 현물 500만원 + 해외 숏 마진 500만원 (1x, 추가 마진 포함)
```

### 2. 포트폴리오 한도 관리
```
동시 활성 포지션 합산:
  total_allocated = Σ position_sizes

  IF total_allocated + new_position > total_capital × 0.30:
    → 신규 진입 거부
    → 또는 기존 포지션 중 수익 확정 가능한 것 먼저 청산

유동성 예비:
  최소 현금 보유: total_capital × 0.40
  역프리미엄 추매용 예비 자금
```

### 3. 해외 선물 유동성(OI) 확인
```
포지션 사이즈 vs 해당 코인 선물 OI(미결제약정):

  position_notional / total_OI 비율:

  < 0.5%: 안전 (슬리피지 무시 가능)
  0.5~2%: 주의 (분할 진입/청산 권고)
  2~5%: 경고 (유동성 부족, 사이즈 축소)
  > 5%: 위험 (진입 금지, proxy hedge 검토)

OI 확인:
  - 바이낸스: GET /fapi/v1/openInterest
  - OKX, Bybit: 각 API
```

### 4. 슬리피지 예상
```
소형 알트 선물:
  OI < $1M: 예상 슬리피지 1~3%
  OI $1~5M: 예상 슬리피지 0.5~1%
  OI $5~20M: 예상 슬리피지 0.1~0.5%
  OI > $20M: 예상 슬리피지 < 0.1%

국내 현물:
  24h volume < 1억원: 예상 슬리피지 2~5%
  24h volume 1~10억원: 예상 슬리피지 0.5~2%
  24h volume > 10억원: 예상 슬리피지 < 0.5%

총 예상 슬리피지가 목표 수익의 20% 초과 시:
  → 사이즈 축소 권고
  → 또는 진입 비추천
```

### 5. 동시 다중 시그널 시 자본 배분
```
여러 코인 시그널 동시 발생 시:
  1. 등급 높은 순 우선 배분
  2. 시그널 신뢰도 높은 순
  3. 리드타임 짧은 순 (긴급도)

배분 예시:
  자본 1억원, 3개 시그널 동시
  TT (S등급, high): 10% = 1000만원
  ATOM (A등급, high): 7% = 700만원
  FLOW (B등급, medium): 5% × 0.7 = 350만원
  총 투입: 2050만원 (20.5% < 30% 한도 OK)
```

## 출력
```json
{
  "decision_id": "uuid",
  "ticker": "TT",
  "total_capital_krw": 100000000,
  "allocation": {
    "base_pct": 10,
    "confidence_multiplier": 1.0,
    "final_pct": 10,
    "position_size_krw": 10000000,
    "domestic_allocation_krw": 5000000,
    "overseas_margin_krw": 5000000
  },
  "portfolio_check": {
    "current_total_allocated_pct": 7,
    "after_this_position_pct": 17,
    "within_limit": true
  },
  "liquidity_check": {
    "futures_oi_usd": 5000000,
    "position_vs_oi_pct": 0.7,
    "estimated_slippage_pct": 0.8,
    "grade": "caution"
  },
  "approved": true,
  "warnings": ["futures OI 낮음, 분할 진입 권고"]
}
```

## 데이터 의존성
- `07-target-coin-filter`: 타겟 등급
- `08-signal-direction-engine`: 시그널 신뢰도, 사이즈 비율
- `09-delta-neutral-position`: 현재 활성 포지션 목록
- `10-proxy-hedge-mapper`: proxy hedge 시 OI 확인

## 갱신 주기
- 총 자본 갱신: **일 1회** (또는 입출금 시)
- OI 확인: **시그널 발생 시** 즉시
- 포트폴리오 한도 체크: **포지션 변경 시** 즉시
