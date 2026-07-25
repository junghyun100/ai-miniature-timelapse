#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 output.mp4 input1.mp4 input2.mp4 ..." >&2
  exit 1
fi

output="$1"
shift

list_file="$(mktemp)"
trap 'rm -f "$list_file"' EXIT

for input in "$@"; do
  printf "file '%s'\n" "$input" >> "$list_file"
done

ffmpeg -y -f concat -safe 0 -i "$list_file" -c copy "$output"

