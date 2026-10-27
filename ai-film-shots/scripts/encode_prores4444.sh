#!/usr/bin/env bash
# Encode a video to ProRes 4444 (10-bit 4:4:4, Apple vendor tag, 24-bit PCM 48 kHz stereo), 24 fps.
# Usage: encode_prores4444.sh IN.mp4 [OUT.mov] [--mirror] [--size WxH]
#   --mirror   flip left-right (fixes a wound/scar generated on the wrong side)
#   --size     scale and centre-crop to WxH (e.g. 5026x2160 so every shot matches the cut)
# Speed: about 5-6 s of encoding per second of 4K. Needs ffmpeg (brew install ffmpeg).
set -euo pipefail
in="${1:?usage: encode_prores4444.sh IN [OUT] [--mirror] [--size WxH]}"; shift
out=""; mirror=0; size=""
while [ $# -gt 0 ]; do case "$1" in
  --mirror) mirror=1;; --size) size="$2"; shift;; *) out="$1";; esac; shift; done
[ -n "$out" ] || out="${in%.*}$([ $mirror = 1 ] && echo _mirrored)_ProRes4444.mov"
vf="fps=24,setsar=1"
if [ -n "$size" ]; then w=${size%x*}; h=${size#*x}; vf="scale=$w:$h:force_original_aspect_ratio=increase:flags=lanczos,crop=$w:$h,$vf"; fi
[ $mirror = 1 ] && vf="$vf,hflip"
ffmpeg -nostdin -hide_banner -loglevel error -stats -y -i "$in" -vf "$vf" -af "aresample=48000,aformat=channel_layouts=stereo" \
  -c:v prores_ks -profile:v 4 -pix_fmt yuv444p10le -vendor apl0 -c:a pcm_s24le -ar 48000 "$out"
echo "$out"
