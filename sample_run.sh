#!/usr/bin/env bash
set -euo pipefail
mkdir -p tmp
start=$(date +%s.%N)
blender phong.blend --background --python phong.py -- ./airplane.off ./tmp
end=$(date +%s.%N)
elapsed=$(awk "BEGIN {printf \"%.3f\", $end - $start}")
printf "Elapsed time: %s seconds\n" "$elapsed"