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

TDLIB_HEADER_FOUND=0
for include_flag in "${TDLIB_INCLUDE_FLAGS[@]}"; do
  include_dir="${include_flag#-I}"
  if [[ -f "$include_dir/td/telegram/td_json_client.h" ]]; then
    TDLIB_HEADER_FOUND=1
    break
  fi
done

if [[ "$TDLIB_HEADER_FOUND" != "1" ]]; then
  echo "TDLib headers are required to build tdlib_json_relay." >&2
  echo "Set TDLIB_PREFIX, or set TDLIB_SOURCE_DIR and TDLIB_BUILD_DIR." >&2
  echo "Current TDLIB_PREFIX=$TDLIB_PREFIX" >&2
  exit 1
fi

if [[ -n "$TDLIB_BUILD_DIR" && ! -f "$TDLIB_LINK_TARGET" ]]; then
  echo "TDLib library not found: $TDLIB_LINK_TARGET" >&2
  exit 1
fi

OPENSSL_LINK_FLAGS=()
if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists openssl; then
  # shellcheck disable=SC2207
  OPENSSL_LINK_FLAGS=($(pkg-config --libs openssl))
elif [[ -d "$OPENSSL_PREFIX/lib" ]]; then
  OPENSSL_LINK_FLAGS=(-L"$OPENSSL_PREFIX/lib" -Wl,-rpath,"$OPENSSL_PREFIX/lib" -lssl -lcrypto)
fi

CMD=(
  c++ -O3 -std=c++20 -pthread
  "$SRC"
  "${TDLIB_INCLUDE_FLAGS[@]}"
  -L"$TDLIB_LIB_DIR"
  -Wl,-rpath,"$TDLIB_LIB_DIR"
  "$TDLIB_LINK_TARGET"
)
if ((${#OPENSSL_LINK_FLAGS[@]})); then
  CMD+=("${OPENSSL_LINK_FLAGS[@]}")
fi
CMD+=(-lz -o "$OUT")
"${CMD[@]}"

echo "Built $OUT"
