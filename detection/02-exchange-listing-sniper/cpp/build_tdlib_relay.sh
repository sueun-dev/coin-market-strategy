#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CPP_DIR="$ROOT_DIR/cpp"
BIN_DIR="$ROOT_DIR/bin"
SRC="$CPP_DIR/tdlib_json_relay.cpp"
OUT="$BIN_DIR/tdlib_json_relay"
TDLIB_PREFIX="${TDLIB_PREFIX:-/opt/homebrew/opt/tdlib}"
TDLIB_SOURCE_DIR="${TDLIB_SOURCE_DIR:-}"
TDLIB_BUILD_DIR="${TDLIB_BUILD_DIR:-}"
OPENSSL_PREFIX="${OPENSSL_PREFIX:-/opt/homebrew/opt/openssl@3}"

if [[ -z "$TDLIB_BUILD_DIR" && -f "$ROOT_DIR/vendor/tdlib-latest/build/libtdjson.dylib" ]]; then
  TDLIB_SOURCE_DIR="$ROOT_DIR/vendor/tdlib-latest"
  TDLIB_BUILD_DIR="$ROOT_DIR/vendor/tdlib-latest/build"
fi

mkdir -p "$BIN_DIR"

if [[ -n "$TDLIB_BUILD_DIR" ]]; then
  TDLIB_INCLUDE_FLAGS=()
  if [[ -n "$TDLIB_SOURCE_DIR" ]]; then
    TDLIB_INCLUDE_FLAGS+=(-I"$TDLIB_SOURCE_DIR")
  fi
  TDLIB_INCLUDE_FLAGS+=(-I"$TDLIB_BUILD_DIR")
  TDLIB_LIB_DIR="$TDLIB_BUILD_DIR"
  TDLIB_LINK_TARGET="$TDLIB_BUILD_DIR/libtdjson.dylib"
else
  TDLIB_INCLUDE_FLAGS=(-I"$TDLIB_PREFIX/include")
  TDLIB_LIB_DIR="$TDLIB_PREFIX/lib"
  TDLIB_LINK_TARGET="-ltdjson"
fi

c++ -O3 -std=c++20 -pthread \
  "$SRC" \
  "${TDLIB_INCLUDE_FLAGS[@]}" \
  -L"$TDLIB_LIB_DIR" \
  -L"$OPENSSL_PREFIX/lib" \
  -Wl,-rpath,"$TDLIB_LIB_DIR" \
  -Wl,-rpath,"$OPENSSL_PREFIX/lib" \
  "$TDLIB_LINK_TARGET" -lssl -lcrypto -lz \
  -o "$OUT"

echo "Built $OUT"
