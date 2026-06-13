# 02. Exchange Listing Sniper

업비트와 빗썸의 공식 텔레그램 채널을 감시해 상장/마켓 추가 공지를 빠르게 감지하는 모듈입니다.

지금은 공개 HTML 폴링과 여러 실시간 소스 백엔드를 지원합니다.

- 기본 fallback: 공개 채널 HTML 폴링
- 실시간 백엔드: Telethon 유저 세션 기반 MTProto 수신 (`cryptg` 가속 권장)
- 최속 백엔드: TDLib(C++) 기반 실시간 수신
- 현재 실전 최속 모드: `race` first-wins 수신

현재 범위:

- 업비트 공식 텔레그램 `@upbit_news`
- 빗썸 공식 텔레그램 `@BithumbExchange`
- KRW/원화 상장 공지 감지
- Bybit spot/perp 존재 여부 확인
- 감지 직후 Bybit spot 시장가 자동매수
- 주문 fast path는 C++ 프로세스로 실행 가능
- 공지 분류기는 Python/C++/Rust 비교 후 더 빠른 네이티브 경로 사용 가능
- 텔레그램 알림 전송

분류 정확도 기준:

- 업비트는 `[거래] ... KRW 마켓 디지털 자산 추가` 또는 `[거래] ... 신규 거래지원 안내 (KRW 마켓)` 형식만 actionable KRW 신규 상장으로 봅니다.
- 업비트 BTC/USDT 단독 마켓 추가, 입출금, 유통량, 유의종목, 이벤트, 종료, 변경 안내는 매수 대상에서 제외합니다.
- 빗썸은 `[마켓 추가] 코인명(TICKER) 원화 마켓 추가` 와 `[마켓 추가/수수료 이벤트] 코인명(TICKER) 원화 마켓 추가 (거래 수수료 무료)` 계열을 actionable 원화 마켓 추가로 봅니다.
- 빗썸 최초 마켓 추가 공지에는 `거래 오픈 오후 ... 예정` 또는 `거래 개시 ...` 문구가 붙을 수 있으므로 이 문구만으로는 제외하지 않습니다.
- 빗썸의 후속 업데이트인 `시간 변경`, `연기`, `재거래지원`, `유의`, `중단`, `종료` 문구는 제외합니다.
- 같은 채널에서 같은 티커의 마켓 추가 공지가 제목 보강 형태로 다시 올라오면, Python poller 경로와 C++ ultra engine은 티커 단위 중복 guard로 두 번째 매수 시도를 막습니다.
- 복수 티커 공지에 이미 처리한 티커와 새 티커가 섞여 있으면 Python poller와 C++ ultra engine은 이미 처리한 티커만 제외하고 새 티커는 계속 처리합니다.
- 실시간 backend에서 높은 message id의 일반 공지가 먼저 도착하고 낮은 message id의 상장 공지가 늦게 도착해도, Python poller와 hot memory-state 경로는 최근 처리 message id window로 중복만 막고 낮은 id의 신규 상장 공지는 처리합니다.
- `H`, `M` 같은 1글자 티커도 유효한 티커로 파싱합니다.
- Python/C++/Rust/TDLib native 경로는 같은 판정 의미를 유지해야 합니다. 특히 C++ 계열은 UTF-8 한글 자산명 끝글자를 ASCII trim으로 잘라내면 안 됩니다.

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
- 상태 파일 `data/detected_listing_posts.json` 은 채널별 `last_seen_message_id`, 최근 처리한 message id window, 이미 처리한 상장 티커를 보관합니다.
- `race` backend의 first-arrival gate도 채널별 마지막 id가 아니라 `(channel_handle, message_id)` 단위로 중복만 제거합니다. 그래서 일반 공지의 높은 message id가 먼저 도착해도, 아직 처리하지 않은 낮은 message id의 상장 공지는 버리지 않습니다. 같은 메시지를 다른 backend가 다시 보내면 일반 중복은 버리지만, TDLib native trade proof가 붙은 payload는 주문 증거 보존을 위해 후속 처리로 넘길 수 있습니다.
- race 시작 조건을 더 엄격하게 걸고 싶으면 `LISTING_RACE_MIN_READY_BACKENDS=2`처럼 최소 세션 수를 올리거나 `LISTING_RACE_REQUIRED_BACKENDS=tdlib,telethon`처럼 필수 backend를 지정할 수 있습니다. 조건을 만족하지 못하면 감시를 시작하지 않습니다.
- TDLib relay child process에는 `.env`에서 읽은 Bybit/native-buy 관련 설정을 명시적으로 넘깁니다. `LISTING_TDLIB_NATIVE_BUY_ACTIVE=1`일 때 native-buy status가 `ready`가 아니면 감시를 시작하지 않습니다.
- TDLib watch chat id는 `LISTING_TDLIB_WATCH_CHATS` 또는 `data/tdlib_watch_chats.json` cache로 재사용할 수 있습니다. cache가 없을 때만 `searchPublicChat`으로 resolve하고, resolve 결과는 다음 재시작을 위해 저장합니다.
- TDLib clock calibration이 timeout되면 relay timestamp를 raw 기준으로 사용하고 경고를 남깁니다. hot path에서는 `LISTING_TDLIB_SKIP_CLOCK_CALIBRATION=1` 또는 `trade_post` 기본값으로 calibration을 생략할 수 있습니다.
- native/relay payload에서 `tickers` 또는 `markets`가 배열이 아니라 문자열로 들어와도 poller는 문자 단위로 쪼개지 않고 단일 값 리스트로 정규화합니다. 예를 들어 `tickers: "WLFI"`는 `["WLFI"]`, `markets: "KRW"`는 `["KRW"]`가 되어 잘못된 다중 매수로 확장되지 않습니다.
- `native_trades` proof는 fresh listing 순서로 무조건 앞에서 자르지 않고 `trade.ticker` 기준으로 매칭합니다. 이미 처리한 티커가 앞에 섞인 복수 티커 payload에서도 새 티커의 proof/orderLinkId가 잘못 붙지 않고, 새 티커 proof가 없을 때만 해당 티커를 Python buyer fallback으로 채웁니다.
- Python buyer가 disabled/unavailable 상태이거나 bulk buy 결과가 누락되어도 각 trade payload에는 해당 `ticker`와 예정 `order_link_id`가 남습니다. bulk buy 결과가 입력 순서와 다르게 돌아와도 `trade.ticker` 기준으로 다시 맞추고, ticker가 없는 legacy 결과만 위치 기반 fallback으로 처리합니다. 그래서 proof/signal만 봐도 어느 티커가 실제 주문 미시도였는지 구분할 수 있습니다.
- 이미 처리한 message id가 뒤늦게 `native_trade` 또는 `native_trades` proof와 함께 다시 들어오면 poller는 매수를 반복하지 않고 proof 후처리만 수행합니다. 주문 증거는 느린 Bybit snapshot 조회보다 먼저 `data/trade_proofs/YYYYMMDD_native_trades.jsonl`에 JSONL로 남깁니다. 잘못된 타입의 `native_listing` payload는 무시하고 제목 classifier로 fallback합니다.
- latency payload는 native relay 수신 시각(`received_monotonic_ns`)과 Python trace 시작 시각(`received_python_monotonic_ns`)을 분리합니다. 주문 전송 시작/완료 지연은 relay 수신 기준으로, Python 후처리 trace 지연은 Python 수신 기준으로 계산합니다.
- C++ ultra no-ack raw path가 `multi_ticker`로 단일 fast path 처리를 거절하면 poller는 Python/native listing multi-ticker 경로로 fallback합니다. 그래서 native payload에 복수 티커가 들어온 경우 한 티커만 처리하고 끝나지 않습니다.
- Python C++ ultra bridge는 old single-trade ABI와 newer multi-trade ABI를 모두 감지합니다. `get_listing_trades` 심볼이 있는 dylib에서는 trade 배열을 읽어 복수 티커의 주문 증거를 모두 후처리하고, 오래된 dylib에서는 기존 single-trade 구조체로 안전하게 읽습니다.

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

즉 이 경로는 **KRW/원화 신규 상장 감지 직후 Bybit spot 시장가 매수 발사**를 최우선으로 두고, `감지 -> 매수 -> 즉시 리턴` 핫패스만 남깁니다. 주문 전송은 설정 기본값상 **C++ REST fast executor**를 우선 사용하고, C++ trade WebSocket 및 Python trade WebSocket은 비교용/폴백으로 남겨둡니다. 주문 이후의 Bybit snapshot 조회, signal build, persistence, 로그는 백그라운드로 미뤄서 반환 경로를 더 얇게 유지합니다.

`--memory-state` 는 dedup/state를 **copy-on-write 메모리 last-seen 맵**으로 처리하고, 디스크 flush는 뒤로 미룹니다. 즉 실시간 핫패스에서는 `StateStore` 락과 파일 동기화를 건드리지 않고, close 또는 주기 flush 때만 상태 파일을 맞춥니다.

네이티브 분류기:

```bash
cd detection/02-exchange-listing-sniper
bash ./cpp/build_listing_classifier.sh
python -m pytest tests/test_announcement_filter.py -q
```

- `LISTING_CLASSIFIER_BACKEND=cpp|rust|auto|python` 으로 강제 가능
- 실전 스크립트 기본값은 `cpp`
- `auto` 는 저장된 winner 캐시가 있으면 그 값을 쓰고, 없으면 C++/Rust 중 더 빠른 쪽을 한 번 측정해서 고릅니다
- C++/Rust native backend는 로드 직후 빗썸 수수료 이벤트, 1글자 티커, 거래 오픈 시간 변경 negative canary를 통과해야 선택됩니다. 소스는 최신인데 오래된 `.dylib`가 남아 있으면 해당 backend를 무시하고 Python 또는 다른 native backend로 fallback합니다.
- Python classifier가 정확도 기준입니다. 일반 poller와 `make_listing_title_classifier()` 경로는 native backend가 예외를 내거나 제목을 못 잡으면 같은 제목을 Python classifier로 다시 확인합니다. 즉 native는 가속 경로이지, Python이 잡을 수 있는 상장 공지를 놓치게 하는 단일 판정 지점이 아닙니다.
- 실전 매수 스크립트는 시작 전에 `bin/verify_listing_classifiers.py --require-tdlib-relay`를 실행해 Python 기준 classifier, 기본 `make_listing_title_classifier()` 경로, TDLib relay `--classify-title` 경로가 같은 golden fixture를 통과하는지 확인합니다. 실패하면 감시를 시작하지 않습니다. 진단용으로만 `LISTING_CLASSIFIER_VERIFY=0`으로 끌 수 있습니다. `run_source_first_realtime.sh`는 분류/매수 없이 소스 수신만 보는 모드라 이 classifier gate를 실행하지 않습니다.

네이티브 실행 경로 빌드:

```bash
cd detection/02-exchange-listing-sniper
bash ./cpp/build_fast_path.sh
bash ./cpp/build_listing_ultra_engine.sh
bash ./cpp/build_tdlib_relay.sh
python bin/verify_listing_classifiers.py --require-tdlib-relay
python -m pytest tests/test_native_runtime_paths.py -q
```

- C++ REST fast path와 C++ ultra engine은 서명 예열, timestamp bias, bulk 주문 worker를 위해 OpenSSL 헤더/라이브러리를 사용합니다. `pkg-config`가 있으면 `libcurl`/`openssl` flags를 자동 사용하고, 없으면 `OPENSSL_PREFIX`를 사용합니다. 공통 macOS rpath/local OpenSSL 처리는 `cpp/build_support.sh`가 담당합니다.
- `BYBIT_TIMESTAMP_BIAS_MS`는 C++ ultra order header timestamp에도 적용됩니다. `LISTING_CPP_ULTRA_ORDER_ON_CACHE_MISS=0`이면 로컬 Bybit spot-symbol cache에서 `TICKERUSDT`가 확인될 때만 주문하고, `LISTING_CPP_ULTRA_ORDER_PREFLIGHT_ONLY=1`은 주문 전송 없이 libcurl order request 준비까지만 하는 벤치마크/테스트용입니다.
- `bash ./bin/build_native_classifiers.sh` 는 C++ classifier, C++ ultra engine, Rust classifier를 모두 빌드합니다. Rust classifier까지 빌드하려면 Cargo가 필요합니다.
- C++ trade WebSocket path는 Boost.Asio SSL 기반이라 macOS에서도 Boost와 OpenSSL 개발 헤더가 필요합니다.
- TDLib relay는 TDLib 설치 또는 `vendor/tdlib-latest/build/libtdjson.dylib`가 필요합니다. repo 밖의 TDLib/OpenSSL을 재사용할 때는 `TDLIB_SOURCE_DIR`, `TDLIB_BUILD_DIR`, `OPENSSL_PREFIX`를 명시합니다.
- `bin/tdlib_json_relay --classify-title bithumb "[마켓 추가] 밈코어(M) 원화 마켓 추가"` 는 TDLib relay 내부 분류기만 실행해 JSON을 출력합니다. 이 경로는 `tests/test_native_runtime_paths.py`에서 golden fixture와 비교합니다.

테스트:

```bash
cd detection/02-exchange-listing-sniper
python -m pytest -q
python -m pytest tests/test_announcement_filter.py -q
```

`tests/fixtures/listing_title_cases.json` 이 상장 제목 판정의 golden source입니다. `tests/test_announcement_filter.py` 는 이 fixture로 Python, 기본 classifier, C++ native classifier가 같은 KRW/원화 상장/비상장 판정을 내리는지 확인하고, native miss/exception 때 기본 classifier가 Python으로 fallback하는지도 고정합니다. `tests/test_native_runtime_paths.py` 는 같은 fixture로 빌드된 C++ ultra engine과 TDLib relay CLI classifier를 실제로 실행해 같은 ticker/tickers/asset/market 판정을 내리는지 확인하고, fast executor bridge 핑과 C++ ultra의 단일/복수 티커 duplicate guard도 확인합니다. `tests/test_bybit_spot_buyer.py` 는 Python `BybitSpotBuyer.buy_markets()`가 disabled 상태에서도 주문별 payload를 남기고, C++ fast-only bulk 경로가 `BUYBULK` bridge를 쓰며, 짧은 bulk 응답을 누락 trade로 padding하는지 확인합니다. `tests/test_cpp_ultra_engine.py` 는 Python C++ ultra bridge가 old single-trade ABI와 newer multi-trade ABI payload를 둘 다 안전하게 읽는지, C++ native runtime env가 `.env`에서 process env로 올라가는지 확인합니다. `tests/test_order_link_id.py` 는 Python poller와 C++ ultra engine이 같은 `orderLinkId=ls-<exchange>-<message_id>-<ticker>` 형식과 36자 제한을 공유하는지 고정합니다. `tests/test_tdlib_realtime_client.py` 는 relay child env 전달, clock calibration timeout 처리, native-buy status gate, relay의 `listingMatched` payload가 Python post의 `native_listing.tickers`로 보존되는지, relay가 `markets`를 생략한 경우 KRW로 보강되는지, native trade proof payload가 손실되지 않는지 확인합니다. `tests/test_listing_dedup.py` 는 빗썸이 같은 티커의 마켓 추가 공지를 기본형과 거래 오픈 시간 보강형으로 연속 게시해도 Python poller가 두 번째 매수를 보내지 않는지, 높은 message id의 일반 공지 뒤에 낮은 message id의 상장 공지가 늦게 들어와도 놓치지 않는지, `native_listing.tickers`가 복수 매수 호출로 확장되는지, 문자열 형태의 `tickers`/`markets` payload가 문자 단위로 쪼개지지 않는지, Python bulk buy 결과가 누락되거나 순서가 뒤섞여도 티커/orderLinkId 정렬이 깨지지 않는지, 중복 message id의 native trade proof가 재매수 없이 후처리되는지, proof 저장이 느린 signal 후처리보다 먼저 실행되는지, latency payload가 relay 수신 기준과 Python trace 기준을 분리하는지, C++ ultra no-ack raw path의 `multi_ticker` 거절이 Python multi-ticker 처리로 fallback되는지, multi-trade raw payload가 복수 티커 proof로 보존되는지, 잘못된 native listing payload가 제목 classifier로 fallback되는지, 그리고 `emit_ultra_ack=false` raw ultra 경로도 상장 티커 state를 남기는지 확인합니다. `tests/test_signal_emitter.py` 는 trade proof JSONL 파일 형식과 수신→주문 타이밍 계산을 확인합니다. `tests/test_state_store.py` 는 상태 파일의 replay floor, 최근 message id window, 상장 티커 보존, legacy/malformed state file 호환성을 확인합니다. `tests/test_post_text.py` 는 공개 텔레그램 HTML 파싱, `<br>` 줄바꿈, 링크 제거, HTML entity 복원, 실시간 클라이언트의 제목 추출 헬퍼가 같은 텍스트 기준을 쓰는지 확인합니다.

Linux VPS 배포:

- 가이드: [deploy/linux/README.md](deploy/linux/README.md)
- 서비스 파일: [02-exchange-listing-sniper.service](deploy/linux/02-exchange-listing-sniper.service)

Bybit 자동매수 env 키:

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_API_BASE_URL`
- `BYBIT_FAST_EXECUTOR_ENABLED`
- `BYBIT_FAST_EXECUTOR_AUTO_BUILD`
- `BYBIT_FAST_EXECUTOR_PATH`
- `BYBIT_FAST_EXECUTOR_BUILD_SCRIPT`
- `BYBIT_FAST_ORDER_ON_CACHE_MISS`
- `BYBIT_REQUIRE_FAST_EXECUTOR_WARMUP`
- `BYBIT_RESOLVE_DUPLICATE_ORDER_LINK_ID`
- `BYBIT_TIMESTAMP_BIAS_MS`
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

- 소스: [bybit_fast_path.cpp](cpp/bybit_fast_path.cpp)
- 빌드: [build_fast_path.sh](cpp/build_fast_path.sh)
- 역할: Bybit spot 심볼 캐시 + keep-alive HTTP + `order/create` 직접 호출
- Python 쪽은 단일 티커에는 `BUY`, 복수 티커 fast-only 경로에는 `BUYBULK` 명령을 전달합니다. `KEEPWARM`은 order client와 bulk worker를 미리 예열합니다.

C++ trade WebSocket path:

- 소스: [bybit_ws_trade_path.cpp](cpp/bybit_ws_trade_path.cpp)
- 빌드: [build_ws_trade_path.sh](cpp/build_ws_trade_path.sh)
- 역할: Bybit trade WebSocket order entry를 C++ 프로세스로 유지
- 현재 용도: 비교용 및 fallback transport

공지 형식 메모:

- 업비트 신규 상장형 제목은 2026-06-11 공식 텔레그램 공개 페이지 확인 기준 `코인명(TICKER)` 패턴을 포함
- 빗썸 마켓 추가형 제목도 2026-06-11 공식 텔레그램 공개 페이지 확인 기준 `코인명(TICKER)` 패턴을 포함
- 다만 업비트 `[거래]` 카테고리 안에는 `유의 촉구`, `거래 유의 종목`도 있어서, 괄호만 보고 매수하면 안 되고 현재처럼 키워드 필터가 필요
