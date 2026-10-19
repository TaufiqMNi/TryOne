#!/usr/bin/env bash
# Tampal overlay logo + banner pada video siap edit.
# Guna: ./apply_overlay.sh input.mp4 output.mp4
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
ffmpeg -y -i "$1" -i "$DIR/overlay_1080x1920.png" -filter_complex \
  "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v];[v][1:v]overlay=0:0,format=yuv420p" \
  -c:v libx264 -crf 18 -preset medium -r 30 -c:a copy "$2"
