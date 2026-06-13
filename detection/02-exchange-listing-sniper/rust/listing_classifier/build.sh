#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CRATE_DIR="$ROOT_DIR/rust/listing_classifier"
BIN_DIR="$ROOT_DIR/bin"

mkdir -p "$BIN_DIR"

if [[ -f "$HOME/.cargo/env" ]]; then
  . "$HOME/.cargo/env"
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo is required to build the Rust listing classifier." >&2
  echo "Install Rust/Cargo or set PATH so cargo is available." >&2
  exit 1
fi

cd "$CRATE_DIR"
cargo build --release

UNAME="$(uname -s)"
if [[ "$UNAME" == "Darwin" ]]; then
  cp "target/release/liblisting_classifier_rust.dylib" "$BIN_DIR/liblisting_classifier_rust.dylib"
elif [[ "$UNAME" == "Linux" ]]; then
  cp "target/release/liblisting_classifier_rust.so" "$BIN_DIR/liblisting_classifier_rust.so"
else
  cp "target/release/listing_classifier_rust.dll" "$BIN_DIR/listing_classifier_rust.dll"
fi

echo "Built Rust native classifier into $BIN_DIR"
