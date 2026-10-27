#!/usr/bin/env bash
# One image with N frames spread across a video, each stamped with its time - for checking a take quickly.
# Usage: contact_sheet.sh IN.mp4 [N=12] [OUT.jpg]
set -euo pipefail
in="$1"; n="${2:-12}"; out="${3:-${in%.*}_sheet.jpg}"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
fps=$(awk -v n="$n" -v d="$d" 'BEGIN{printf "%.6f", n/d}')
cols=4; rows=$(( (n + cols - 1) / cols ))
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$in" -vf "fps=$fps,scale=480:-2,drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.5,tile=${cols}x${rows}" -frames:v 1 "$out"
echo "$out"
