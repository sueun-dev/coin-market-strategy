#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CPP_DIR="$ROOT_DIR/cpp"
BIN_DIR="$ROOT_DIR/bin"
SRC="$CPP_DIR/bybit_ws_trade_path.cpp"
OUT="$BIN_DIR/bybit_ws_trade_path"
BOOST_PREFIX="${BOOST_PREFIX:-/opt/homebrew/opt/boost}"
OPENSSL_PREFIX="${OPENSSL_PREFIX:-/opt/homebrew/opt/openssl@3}"

mkdir -p "$BIN_DIR"

if [[ ! -f "$BOOST_PREFIX/include/boost/asio.hpp" ]]; then
  echo "Boost headers are required to build bybit_ws_trade_path." >&2
  echo "Set BOOST_PREFIX or install Boost. Current BOOST_PREFIX=$BOOST_PREFIX" >&2
  exit 1
fi

if [[ ! -f "$OPENSSL_PREFIX/include/openssl/hmac.h" ]]; then
  echo "OpenSSL headers are required to build bybit_ws_trade_path." >&2
  echo "Set OPENSSL_PREFIX or install OpenSSL development headers. Current OPENSSL_PREFIX=$OPENSSL_PREFIX" >&2
  exit 1
fi

c++ -O3 -std=c++20 \
  "$SRC" \
  -I"$BOOST_PREFIX/include" \
  -I"$OPENSSL_PREFIX/include" \
  -L"$OPENSSL_PREFIX/lib" \
  -lssl -lcrypto \
  -o "$OUT"

echo "Built $OUT"
