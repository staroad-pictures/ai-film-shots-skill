#!/usr/bin/env bash
# Light preview of a take (720 px, 24 fps, H.264) and a 240x104 thumbnail, as used by the edit bench.
# Usage: make_preview.sh IN.mp4 TAKE_ID [OUT_DIR=.]
set -euo pipefail
in="$1"; id="$2"; o="${3:-.}"; mkdir -p "$o/clips" "$o/thumbs"
ffmpeg -nostdin -v error -y -i "$in" -vf "scale=720:-2,fps=24" -c:v libx264 -crf 27 -preset medium -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart "$o/clips/$id.mp4"
ffmpeg -nostdin -v error -y -ss 2 -i "$in" -frames:v 1 -vf "scale=240:104:force_original_aspect_ratio=increase,crop=240:104" -q:v 4 "$o/thumbs/$id.jpg"
printf '%s  %.2f s\n' "$id" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$o/clips/$id.mp4")"
