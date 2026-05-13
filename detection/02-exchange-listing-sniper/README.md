# 02. Exchange Listing Sniper

업비트와 빗썸의 공식 텔레그램 채널을 감시해 상장/마켓 추가 공지를 빠르게 감지하는 모듈입니다.

지금은 두 가지 실시간 소스 백엔드를 지원합니다.

- 기본 fallback: 공개 채널 HTML 폴링
- 실시간 백엔드: Telethon 유저 세션 기반 MTProto 수신 (`cryptg` 가속 권장)
- 최속 백엔드: TDLib(C++) 기반 실시간 수신
- 현재 실전 최속 모드: `race` first-wins 수신

현재 범위:

- 업비트 공식 텔레그램 `@upbit_news`
- 빗썸 공식 텔레그램 `@BithumbExchange`
- 상장 공지 감지
- Bybit spot/perp 존재 여부 확인
- 감지 직후 Bybit spot 시장가 자동매수
- 주문 fast path는 C++ 프로세스로 실행 가능
- 공지 분류기는 Python/C++/Rust 비교 후 더 빠른 네이티브 경로 사용 가능
- 텔레그램 알림 전송

사용 예시:

```bash
cd detection/02-exchange-listing-sniper
../../.venv/bin/python main.py --exchange bithumb --no-telegram
../../.venv/bin/python main.py --exchange bithumb --no-trade
../../.venv/bin/python main.py --loop
../../.venv/bin/python main.py --realtime
../../.venv/bin/python main.py --realtime --realtime-backend race
../../.venv/bin/python main.py --realtime --realtime-backend telethon
../../.venv/bin/python main.py --realtime --realtime-backend tdlib
../../.venv/bin/python main.py --login-source-telegram
../../.venv/bin/python main.py --login-source-telegram --realtime-backend race
../../.venv/bin/python main.py --test-telegram
```

02 전용 텔레그램 env 키:

- `LISTING_TELEGRAM_BOT_TOKEN`
- `LISTING_TELEGRAM_CHAT_ID`

없으면 루트의 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`를 fallback으로 사용합니다.

실시간 소스 텔레그램 env 키:

- `LISTING_SOURCE_TELEGRAM_API_ID`
- `LISTING_SOURCE_TELEGRAM_API_HASH`
- `LISTING_SOURCE_TELEGRAM_PHONE`
- `LISTING_SOURCE_TELEGRAM_SESSION`

중요:

- 실시간 소스 수신에는 `BotFather`가 아니라 **텔레그램 유저 API (`API_ID`, `API_HASH`)** 가 필요
- 즉 Bot token은 소스 수신용이 아니라 **알림 발송용**
- 실시간 소스 테스트를 하려면 `my.telegram.org` 에서 `API_ID`, `API_HASH`를 만든 뒤 유저 세션 로그인을 해야 함

실시간 모드 사용 순서:

1. `.env`에 위 4개 중 최소 `API_ID`, `API_HASH`, `PHONE` 입력
2. `python main.py --login-source-telegram` 으로 유저 세션 로그인
3. `python main.py --realtime` 또는 `python main.py --loop` 실행

현재 기본 실시간 백엔드는 `race` 입니다. `telethon` 과 `tdlib` 는 단일 비교용/폴백으로 남겨둡니다.

실시간 저지연 경로:

- `--realtime` 또는 실시간 세션이 설정된 `--loop` 는 저지연 모드로 동작
- 핫패스 순서: `message event -> classify -> buy -> build signal`
- `detected_listing_posts.json` 저장과 시그널 JSON 저장은 백그라운드로 지연
- 02 전용 텔레그램 알림도 별도 워커에서 전송
- Bybit 정보는 네트워크 refresh 대신 cache-only snapshot 우선 사용
- 백그라운드 keep-warm 스레드가 Bybit 캐시와 fast executor를 주기적으로 유지

실전 실행 스크립트:

```bash
cd detection/02-exchange-listing-sniper
./bin/run_low_latency_realtime.sh
./bin/run_source_first_realtime.sh
./bin/run_fast_buy_realtime.sh
```

이 스크립트는 다음을 강제합니다.

- `--realtime`
- `--strict-realtime`
- `BYBIT_FAST_EXECUTOR_ENABLED=1`
- `BYBIT_FAST_EXECUTOR_AUTO_BUILD=1`

소스 선점 최우선 스크립트 `run_source_first_realtime.sh` 는 다음을 강제합니다.

- `--realtime`
- `--strict-realtime`
- `--memory-state`
- `--source-only`
- `--no-telegram`
- `--state-flush-interval 0`
- raw source 이벤트 파일 저장은 기본적으로 하지 않음

즉 이 경로는 **텔레그램에서 새 글을 가장 빨리 잡는 것만 우선**하고, 분류/매수/알림은 뒤로 미루는 모드입니다.

실전 매수 스크립트 `run_fast_buy_realtime.sh` 는 다음을 강제합니다.

- `--realtime`
- `--realtime-backend race`
- `--strict-realtime`
- `--memory-state`
- `--ultra-buy`
- `--no-telegram`
- `BYBIT_SPOT_BUY_ENABLED=1`
- `BYBIT_WS_ORDER_ENABLED=1`
- `BYBIT_FAST_EXECUTOR_ENABLED=1`
- `BYBIT_QUERY_FILL_AFTER_BUY=0`
- `LISTING_CLASSIFIER_BACKEND=cpp` 기본값

즉 이 경로는 **KRW/원화 신규 상장 감지 직후 Bybit spot 시장가 매수 발사**를 최우선으로 두고, `감지 -> 매수 -> 즉시 리턴` 핫패스만 남깁니다. 주문 전송은 최신 실측 기준 winner인 **C++ REST fast executor**를 기본 우선 사용하고, C++ trade WebSocket 및 Python trade WebSocket은 비교용/폴백으로 남겨둡니다. 주문 이후의 Bybit snapshot 조회, signal build, persistence, 로그는 백그라운드로 미뤄서 반환 경로를 더 얇게 유지합니다.

`--memory-state` 는 dedup/state를 **copy-on-write 메모리 last-seen 맵**으로 처리하고, 디스크 flush는 뒤로 미룹니다. 즉 실시간 핫패스에서는 `StateStore` 락과 파일 동기화를 건드리지 않고, close 또는 주기 flush 때만 상태 파일을 맞춥니다.

벤치마크:

```bash
cd detection/02-exchange-listing-sniper
../../.venv/bin/python bin/benchmark_latency.py --iterations 2000
```

출력 항목:

- `build_post_full`: 실시간 full post 변환 비용
- `build_post_trade`: ultra-buy용 title-only trade post 변환 비용
- `build_post_minimal`: 실시간 minimal post 변환 비용
- `source_only_rt_mem`: source-only 메모리 수신 경로
- `source_only_rt_trace`: source-only + latency trace
- `source_only_rt_noflush`: source-only + deferred flush 완전 제거
- `source_only_rt_persist`: source-only + raw source 파일 저장
- `process_post_sync`: 동기 저장 경로
- `process_post_rt_cached`: 실시간 저지연 경로, 감지만 수행
- `process_post_rt_buy`: 실시간 저지연 경로, 매수 호출 포함
- `receive_to_trade_rt_buy`: 수신 시점부터 주문 호출 완료까지
- `process_post_rt_ultra`: ultra-buy 핫패스, 주문 이후 작업 deferred
- `receive_to_trade_ultra`: ultra-buy 기준 수신 시점부터 주문 호출 완료까지
- `process_post_rt_ultra_mem`: ultra-buy + memory-state 핫패스
- `receive_to_trade_ultra_mem`: ultra-buy + memory-state 기준 수신부터 주문 호출 완료까지
- `cpp_bridge_ping`: C++ fast executor IPC round-trip

최근 로컬 실측 (`--iterations 2000`) 기준:

- `build_post_full` p50 `1.67us`
- `build_post_trade` p50 `1.04us`
- `process_post_rt_buy` p50 `21.31us`
- `process_post_rt_ultra` p50 `14.46us`
- `process_post_rt_ultra_mem` p50 `13.83us`
- `process_post_rt_ultra_fire` p50 `10.12us`
- `receive_to_trade_rt_buy` p50 `8.25us`
- `receive_to_trade_ultra` p50 `7.71us`
- `receive_to_trade_ultra_mem` p50 `7.25us`

즉 ultra-buy + trade-post + memory-state 적용 후 **핫패스 전체 반환 시간은 일반 realtime buy 대비 약 27% 감소**했고, 실제로 줄어든 구간은 주문 뒤에 남아 있던 동기 후처리, 불필요한 post payload 변환, 그리고 state/dedup 경로입니다.

네이티브 분류기:

```bash
cd detection/02-exchange-listing-sniper
bash ./bin/build_native_classifiers.sh
../../.venv/bin/python ./bin/benchmark_native_classifier.py --iterations 100000 --skip-build
```

- `LISTING_CLASSIFIER_BACKEND=cpp|rust|auto|python` 으로 강제 가능
- 실전 스크립트 기본값은 최신 벤치 winner인 `cpp`
- `auto` 는 저장된 winner 캐시가 있으면 그 값을 쓰고, 없으면 C++/Rust 중 더 빠른 쪽을 한 번 측정해서 고릅니다

최근 네이티브 분류기 실측 (`benchmark_native_classifier.py --iterations 100000`) 기준:

- `python_classifier` p50 `4.04us`
- `cpp_classifier` p50 `1.67us`
- `rust_classifier` p50 `2.08us`
- native winner: `cpp`
- overall winner: `cpp`

즉 이 머신에서는 **괄호 안 티커 추출 + KRW/원화 상장 판정**까지 포함한 분류기 자체는 C++가 Rust보다 더 빨랐고, 실전 스크립트도 그 winner를 기본값으로 사용합니다.

실제 Telegram ingest 비교:

```bash
cd detection/02-exchange-listing-sniper
../../.venv/bin/python bin/benchmark_live_ingest.py bench --iterations 24 --timeout 20 --pause-sec 0.75
```

최근 실측 기준:

- `telethon_live` p50 `352.089ms`
- `pyrogram_live` p50 `351.724ms`
- `race_tp_live` p50 `351.724ms`
- `pyrogram_wins=10`
- `telethon_wins=6`
- winner: `pyrogram`

즉 이 머신의 최신 반복 측정에서는 **Pyrogram이 Telethon보다 근소하게 더 빨랐고**, 실전 런타임은 **Telethon + TDLib + Pyrogram을 동시에 붙여 먼저 도착한 쪽을 채택하는 `race` 모드가 최선**입니다. 이렇게 하면 단일 백엔드보다 흔들림이 적고, 드물게 다른 레이서가 먼저 들어오는 케이스도 놓치지 않습니다.

실제 Bybit 주문 transport 비교 (`BTCUSDT`, `10 USDT`, 메인넷 왕복 정리) 기준:

- `python_ws` buy ACK `304.668ms`
- `cpp_ws_trade` buy ACK `296.122ms`
- `cpp_fast_path` buy ACK `292.275ms`
- current winner: `cpp_fast_path`

즉 최신 실거래 비교에서는 **C++ REST fast executor가 Python WebSocket, C++ WebSocket보다 조금 더 빨랐고**, 현재 본선 매수 경로도 그 winner를 기본값으로 사용합니다.

Linux VPS 배포:

- 가이드: [deploy/linux/README.md](/Users/sueuncho/Documents/coin-market-strategy/detection/02-exchange-listing-sniper/deploy/linux/README.md)
- 서비스 파일: [02-exchange-listing-sniper.service](/Users/sueuncho/Documents/coin-market-strategy/detection/02-exchange-listing-sniper/deploy/linux/02-exchange-listing-sniper.service)

Bybit 자동매수 env 키:

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_API_BASE_URL`
- `BYBIT_FAST_EXECUTOR_ENABLED`
- `BYBIT_FAST_EXECUTOR_AUTO_BUILD`
- `BYBIT_FAST_EXECUTOR_PATH`
- `BYBIT_FAST_EXECUTOR_BUILD_SCRIPT`
- `BYBIT_WS_ORDER_ENABLED`
- `BYBIT_WS_TRADE_URL`
- `BYBIT_SPOT_BUY_ENABLED`
- `BYBIT_SPOT_BUY_USDT_AMOUNT`
- `BYBIT_SPOT_BUY_MODE`
- `BYBIT_QUERY_FILL_AFTER_BUY`
- `BYBIT_RECV_WINDOW`

주문 방식:

- Bybit spot `Market Buy`
- 기본값은 `marketUnit=quoteCoin`
- 즉 주문 전에 ask 조회/수량 계산을 하지 않고, 설정한 USDT 금액으로 바로 주문
- `BYBIT_QUERY_FILL_AFTER_BUY=false` 기본값이라 주문 직후 추가 fill 조회도 생략
- 중복 방지를 위해 `orderLinkId=ls-거래소-message_id-ticker` 형식 사용

C++ fast path:

- 소스: [bybit_fast_path.cpp](/Users/sueuncho/Documents/coin-market-strategy/detection/02-exchange-listing-sniper/cpp/bybit_fast_path.cpp)
- 빌드: [build_fast_path.sh](/Users/sueuncho/Documents/coin-market-strategy/detection/02-exchange-listing-sniper/cpp/build_fast_path.sh)
- 역할: Bybit spot 심볼 캐시 + keep-alive HTTP + `order/create` 직접 호출
- Python 쪽은 감지 후 C++ 프로세스에 `BUY` 명령만 전달

C++ trade WebSocket path:

- 소스: [bybit_ws_trade_path.cpp](/Users/sueuncho/Documents/coin-market-strategy/detection/02-exchange-listing-sniper/cpp/bybit_ws_trade_path.cpp)
- 빌드: [build_ws_trade_path.sh](/Users/sueuncho/Documents/coin-market-strategy/detection/02-exchange-listing-sniper/cpp/build_ws_trade_path.sh)
- 역할: Bybit trade WebSocket order entry를 C++ 프로세스로 유지
- 현재 용도: 최신 실거래 비교용 및 fallback transport

공지 형식 메모:

- 업비트 신규 상장형 제목은 최근 확인분 기준 `코인명(TICKER)` 패턴을 포함
- 빗썸 마켓 추가형 제목도 최근 확인분 기준 `코인명(TICKER)` 패턴을 포함
- 다만 업비트 `[거래]` 카테고리 안에는 `유의 촉구`, `거래 유의 종목`도 있어서, 괄호만 보고 매수하면 안 되고 현재처럼 키워드 필터가 필요
