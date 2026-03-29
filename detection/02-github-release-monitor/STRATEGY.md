# 02. GitHub 릴리스 모니터 전략서

## 목적
업비트/빗썸 상장 코인 중 자체 메인넷 프로젝트의 공식 GitHub repo에서 하드포크/업그레이드 릴리스를 **거래소 공지보다 2일~2주 전에** 감지한다.
노드 업데이트 릴리스 → 거래소 노드 업데이트 필요 → 입출금 정지 → 폐쇄경제 프리미엄 발생.

## 검증된 리드타임
- **2일 ~ 2주**
- cosmos/gaia v25.0.0 릴리스 태그 → 이후 거래소 공지
- QTUM, 0G, Story Protocol 전부 GitHub 선행
- 썬더코어 아테나 하드포크: 공식 웹페이지에서 업그레이드 시간(5/14 오후 2:53) 사전 공개

## 모니터링 대상
업비트/빗썸 상장 코인 중 **자체 메인넷** 프로젝트 공식 repo (약 50~100개)

### 주요 대상 예시
| 코인 | GitHub Repo | 비고 |
|------|-------------|------|
| ATOM | cosmos/gaia | Cosmos Hub |
| SEI | sei-protocol/sei-chain | Sei Network |
| INJ | InjectiveLabs/injective-core | Injective |
| OSMO | osmosis-labs/osmosis | Osmosis |
| QTUM | qtumproject/qtum | Qtum |
| 0G | 0glabs/0g-chain | 0G Network |
| STORY | storyprotocol/protocol-core | Story Protocol |
| KAVA | Kava-Labs/kava | Kava |
| BAND | bandprotocol/chain | Band Protocol |
| POL | maticnetwork/bor | Polygon PoS |
| FLOW | onflow/flow-go | Flow |
| TT | thundercore/thunder | ThunderCore |

## 핵심 로직

### 1. GitHub Releases API 폴링
```
매 30분마다:
  각 repo → GET /repos/{owner}/{repo}/releases
  최신 릴리스 확인 → 이전 체크 이후 신규 릴리스 존재 여부
```

### 2. 키워드 필터링
```
릴리스 title/body에서 검색:
  - "upgrade" / "hardfork" / "hard fork" / "migration"
  - "breaking change" / "consensus" / "network upgrade"
  - "mandatory update" / "node update"
  - 버전 메이저 변경 (v1.x → v2.x)

태그명 패턴:
  - 시맨틱 버전 메이저/마이너 변경 감지
  - "rc" (release candidate) → 본 릴리스 임박 시그널
```

### 3. 공식 웹페이지/블로그 크롤링 (보조)
```
일부 프로젝트는 GitHub 대신 공식 채널에서 먼저 발표
  - 썬더코어: 공식 웹페이지에서 업그레이드 시간 공개
  - Medium/Mirror 블로그 포스트
키워드 동일하게 적용
```

### 4. 시그널 발행 조건
```
IF 신규 릴리스 감지
  AND 키워드 매칭 (upgrade/hardfork/migration 등)
  AND 해당 코인이 업비트/빗썸 상장
  AND pre-release가 아닌 정식 릴리스 (또는 RC → 임박 시그널)
THEN:
  시그널 발행 → 08-signal-direction-engine으로 전달
  포함 데이터: {
    chain, coin_ticker, repo, release_tag,
    release_title, release_url,
    is_breaking_change, is_mandatory,
    published_at
  }
```

### 5. RC(Release Candidate) 단계 추적
```
RC 릴리스 감지 시:
  - "사전 경고" 레벨 시그널 발행
  - 해당 repo 폴링 주기 30분 → 10분으로 상향
  - 정식 릴리스 나오면 본 시그널 발행
```

## 데이터 의존성
- `19-data-registry`: 상장 코인 ↔ GitHub repo URL 매핑 테이블
- `07-target-coin-filter`: 시그널 발행 전 타겟 적합성 체크

## 출력
```json
{
  "signal_type": "github_release",
  "chain": "thundercore",
  "ticker": "TT",
  "repo": "thundercore/thunder",
  "release_tag": "v4.0.0-athena",
  "release_title": "Athena Hard Fork",
  "keywords_matched": ["hardfork", "mandatory update"],
  "is_breaking": true,
  "upgrade_time_announced": "2024-05-14T05:53:00Z",
  "confidence": "high",
  "detected_at": "2024-05-08T02:00:00Z"
}
```

## 모니터링 주기
- 전체 repo: **30분 간격** 폴링
- RC 감지된 repo: **10분 간격**으로 상향
- GitHub API Rate Limit: 인증 토큰 사용 (5000 req/hr)

## 엣지 케이스
- GitHub API Rate Limit 초과: 토큰 로테이션 또는 GraphQL API 사용
- repo 이전/이름 변경: 리다이렉트 감지 후 매핑 테이블 자동 업데이트
- 릴리스 없이 태그만 생성: Tags API도 병행 폴링
- Draft 릴리스: 무시 (공개 릴리스만 대상)
