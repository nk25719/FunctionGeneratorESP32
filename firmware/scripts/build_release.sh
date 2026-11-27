#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUTPUT="${1:-$ROOT/dist/release-build}"

mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"

REPORT="$OUTPUT/BUILD_REPORT.txt"

echo "FunctionGeneratorESP32 build report" > "$REPORT"
echo "Version: $(cat VERSION)" >> "$REPORT"
echo "Commit: $(git rev-parse HEAD)" >> "$REPORT"

echo "=== Build tools ===" | tee -a "$REPORT"

pio --version | tee -a "$REPORT"
arduino-cli version | tee -a "$REPORT"
arduino-cli core list | tee -a "$REPORT"

echo "=== PlatformIO packages ===" | tee -a "$REPORT"

pio pkg list \
  --project-dir firmware/functiongenerator_web \
  | tee -a "$REPORT"

echo "=== PlatformIO ESP32 web firmware ===" \
  | tee -a "$REPORT"

pio run \
  --project-dir firmware/functiongenerator_web \
  --environment esp32dev \
  2>&1 | tee -a "$REPORT"

WEB_BUILD="firmware/functiongenerator_web/.pio/build/esp32dev"

mkdir -p "$OUTPUT/firmware/web-esp32dev"

for file in firmware.bin bootloader.bin partitions.bin
do
  test -s "$WEB_BUILD/$file"
  cp "$WEB_BUILD/$file" \
    "$OUTPUT/firmware/web-esp32dev/"
done

build_arduino() {
  local board="$1"
  local sketch="$2"
  local destination="$3"

  mkdir -p "$destination"

  echo "=== Arduino: $board / $sketch ===" \
    | tee -a "$REPORT"

  arduino-cli compile \
    --fqbn "$board" \
    --output-dir "$destination" \
    "$sketch" \
    2>&1 | tee -a "$REPORT"

  find "$destination" \
    -type f \
    ! -name '*.bin' \
    -delete

  if ! find "$destination" -name '*.bin' \
      -type f | grep -q .
  then
    echo "No firmware binaries generated."
    exit 1
  fi
}

build_arduino \
  "esp32:esp32:esp32" \
  "firmware/functiongenerator_esp32" \
  "$OUTPUT/firmware/standalone-esp32"

build_arduino \
  "esp32:esp32:esp32s2" \
  "firmware/functiongenerator_esp32" \
  "$OUTPUT/firmware/standalone-esp32s2"

build_arduino \
  "esp32:esp32:esp32" \
  "firmware/ADCtomid_ESP32" \
  "$OUTPUT/firmware/examples/adc-esp32"

build_arduino \
  "esp32:esp32:esp32s2" \
  "firmware/ADCtomid_ESP32" \
  "$OUTPUT/firmware/examples/adc-esp32s2"

echo "All five firmware builds completed." \
  | tee -a "$REPORT"
