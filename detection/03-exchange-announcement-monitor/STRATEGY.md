# 03. 타 거래소 공지 선행 감지 전략서

## 목적
바이낸스/코인베이스/OKX 등 해외 거래소 공지를 크롤링하여 **업비트/빗썸보다 먼저** 입출금 정지 정보를 확보한다.
또한 업비트 공지를 빗썸보다 먼저 감지하는 교차 검증도 수행한다.
추가로 **업비트/빗썸 유의종목 지정, 투자경고, DAXA 거래위험 경고** 공지도 시그널로 포착한다.

## 검증된 리드타임
- **수시간 ~ 1일** (해외→국내)
- **수시간 ~ 6일** (업비트→빗썸)
- Ethereum Pectra: 바이낸스 5/7 09:45 UTC 공지 → 업비트 동일 시점 정지
- 썬더코어: 업비트 5/8 공지 → 빗썸 5/14 당일 공지 (6일 리드타임)
- FLOW 보안 사고: DAXA 거래위험 경고 → 업비트/빗썸 동시 입출금 정지

## 모니터링 소스

### 해외 거래소
| 거래소 | 소스 | 엔드포인트/방법 |
|--------|------|----------------|
| Binance | 공지 API | `GET /sapi/v1/announcement` 또는 공지 페이지 크롤링 |
| Coinbase | Status Page | status.coinbase.com RSS |
| OKX | 공지 센터 | okx.com/support/announcements 크롤링 |
| Bybit | 공지 센터 | bybit.com/announcements 크롤링 |
| Kraken | Status | status.kraken.com RSS |

### 국내 거래소 (교차 검증)
| 거래소 | 소스 | 엔드포인트/방법 |
|--------|------|----------------|
| 업비트 | 공지사항 API | `GET /v1/notices` 또는 공지 페이지 크롤링 |
| 빗썸 | 공지사항 | bithumb.com/notices 크롤링 |
| 코인원 | 공지사항 | coinone.co.kr/notices 크롤링 |
| 코빗 | 공지사항 | korbit.co.kr/announcements 크롤링 |

## 핵심 로직

### 1. 입출금 정지 공지 감지
```
매 5분마다 각 거래소 공지 크롤링:

키워드 필터 (다국어):
  영문: "suspend", "deposit", "withdrawal", "upgrade", "hardfork",
        "maintenance", "network upgrade", "wallet maintenance"
  한글: "입출금", "정지", "중단", "업그레이드", "하드포크",
        "점검", "지갑 점검", "네트워크 업그레이드"
```

### 2. 유의종목/투자경고 감지 (국내 거래소 전용)
```
키워드 필터:
  - "유의종목", "투자유의", "투자경고", "거래유의"
  - "상장폐지", "상장 심사", "거래지원 종료"
  - "DAXA", "거래위험", "투자위험"
  - "투자 유의 종목 지정", "유의 종목 해제"

유의종목 시그널은 별도 분류:
  - 유의종목 지정 → 패닉셀 가능성 → 해킹 시나리오와 유사하게 처리
  - 유의종목 + 입출금 정지 동시 → 최고 경계 시그널
```

### 3. 교차 검증 로직
```
Case 1: 해외 거래소 먼저 공지
  바이낸스에서 코인X 입출금 정지 공지
  → 업비트/빗썸에서도 곧 정지 예측
  → 즉시 시그널 발행

Case 2: 업비트 먼저 공지
  업비트에서 코인X 입출금 정지 공지
  → 빗썸에서도 곧 정지 예측
  → 빗썸에서 포지션 잡기 위한 시그널 발행
  (빗썸이 유동성 낮으면 프리미엄 더 큼)

Case 3: DAXA 공지
  DAXA 거래위험 경고 감지
  → 전 국내 거래소 동시 입출금 정지 예측
  → 패닉셀 시나리오로 분류
```

### 4. 시그널 발행
```
IF 해외 거래소에서 입출금 정지 공지 감지
  AND 해당 코인이 업비트/빗썸 상장
  AND 업비트/빗썸에서 아직 공지 안 나옴
THEN:
  시그널 발행 (lead_source: "overseas_exchange")

IF 업비트에서 입출금 정지 공지 감지
  AND 해당 코인이 빗썸에도 상장
  AND 빗썸에서 아직 공지 안 나옴
THEN:
  시그널 발행 (lead_source: "upbit_to_bithumb")

IF 유의종목/투자경고 공지 감지
THEN:
  시그널 발행 (signal_type: "caution_designation")
```

## 출력

### 입출금 정지 시그널
```json
{
  "signal_type": "exchange_announcement_suspension",
  "ticker": "TT",
  "source_exchange": "upbit",
  "announcement_url": "https://...",
  "suspension_reason": "network_upgrade",
  "suspension_start": "2024-05-08T00:00:00Z",
  "target_exchanges_not_yet_announced": ["bithumb"],
  "lead_time_estimate_hours": 144,
  "confidence": "high",
  "detected_at": "2024-05-08T01:00:00Z"
}
```

### 유의종목/경고 시그널
```json
{
  "signal_type": "caution_designation",
  "ticker": "FLOW",
  "source": "DAXA",
  "caution_type": "거래위험경고",
  "exchanges_affected": ["upbit", "bithumb"],
  "expected_impact": "panic_sell",
  "suspension_likely": true,
  "confidence": "high",
  "detected_at": "2025-12-27T03:00:00Z"
}
```

## 모니터링 주기
- 해외 거래소 공지: **5분 간격**
- 국내 거래소 공지: **3분 간격** (더 빈번하게)
- DAXA/금감원 공지: **10분 간격**

## 엣지 케이스
- 거래소 공지 페이지 구조 변경: 크롤러 자동 복구 불가 시 알림
- 동일 공지 중복 감지: 공지 ID/URL 기반 dedup
- 공지 내 코인 티커 파싱 실패: 본문 NLP 분석 또는 수동 확인 알림
- 거래소 서버 다운으로 크롤링 실패: 재시도 + 백업 소스 활용
