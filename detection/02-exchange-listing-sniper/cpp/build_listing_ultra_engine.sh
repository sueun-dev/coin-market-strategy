#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CPP_DIR="$ROOT_DIR/cpp"
BIN_DIR="$ROOT_DIR/bin"
SRC="$CPP_DIR/listing_ultra_engine.cpp"
LOCAL_OPENSSL_PREFIX="$ROOT_DIR/vendor/openssl-local"
if [[ -z "${OPENSSL_PREFIX:-}" && -d "$LOCAL_OPENSSL_PREFIX" ]]; then
  OPENSSL_PREFIX="$LOCAL_OPENSSL_PREFIX"
else
  OPENSSL_PREFIX="${OPENSSL_PREFIX:-/opt/homebrew/opt/openssl@3}"
fi
CXX_OPT_FLAGS="${CXX_OPT_FLAGS:--O3}"
UNAME="$(uname -s)"

mkdir -p "$BIN_DIR"

if [[ "$UNAME" == "Darwin" ]]; then
  OUT="$BIN_DIR/liblisting_ultra_engine.dylib"
  SHARED_FLAG="-dynamiclib"
else
  OUT="$BIN_DIR/liblisting_ultra_engine.so"
  SHARED_FLAG="-shared -fPIC"
fi

CURL_CFLAGS=""
CURL_LIBS="-lcurl"
OPENSSL_CFLAGS=""
OPENSSL_LIBS=""
OPENSSL_RPATH=""

if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists libcurl; then
  CURL_CFLAGS="$(pkg-config --cflags libcurl)"
  CURL_LIBS="$(pkg-config --libs libcurl)"
fi

if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists openssl; then
  OPENSSL_CFLAGS="$(pkg-config --cflags openssl)"
  OPENSSL_LIBS="$(pkg-config --libs openssl)"
elif [[ -f "$OPENSSL_PREFIX/include/openssl/hmac.h" ]]; then
  OPENSSL_CFLAGS="-I$OPENSSL_PREFIX/include"
  OPENSSL_LIBS="-L$OPENSSL_PREFIX/lib -lssl -lcrypto"
  OPENSSL_RPATH="-Wl,-rpath,$OPENSSL_PREFIX/lib"
else
  echo "OpenSSL headers are required to build listing_ultra_engine." >&2
  echo "Set OPENSSL_PREFIX or install OpenSSL development headers. Current OPENSSL_PREFIX=$OPENSSL_PREFIX" >&2
  exit 1
fi

c++ $CURL_CFLAGS $OPENSSL_CFLAGS \
  $CXX_OPT_FLAGS -std=c++20 -pthread $SHARED_FLAG "$SRC" \
  $CURL_LIBS $OPENSSL_LIBS $OPENSSL_RPATH \
  -o "$OUT"

echo "Built $OUT"
