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

c++ -O3 -std=c++20 \
  "$SRC" \
  -I"$BOOST_PREFIX/include" \
  -I"$OPENSSL_PREFIX/include" \
  -L"$OPENSSL_PREFIX/lib" \
  -lssl -lcrypto \
  -o "$OUT"

echo "Built $OUT"
