#!/usr/bin/env bash
# Render a cut ("bout-a-bout") from an edit list, one file per shot plus the joined cut.
#
# Usage: render_cut.sh CUT.csv MASTERS_DIR OUT_DIR [prores|h264|preview]
#   CUT.csv      the edit bench CSV (columns: order,take,beat,in_s,out_s,...) or any CSV whose
#                2nd, 4th and 5th columns are take, in (s), out (s). Header line is skipped.
#   MASTERS_DIR  folder holding the masters named <take>_4K.mp4 (or <take>.mp4)
#   OUT_DIR      gets shots/NN_<take>[_mirrored].<ext> and cut.<ext>
#   format       prores (ProRes 4444, default) | h264 (4K MP4, CRF 17) | preview (1280 px MP4 for email)
# Environment:
#   MIRROR="M1 M3"   takes to flip left-right in the cut
#   SIZE=5026x2160   frame size every shot is conformed to (scale + centre crop)
#   ONLY="03 07"     render only these rows (to split the work into short runs), then run again with JOIN=1
#   JOIN=1           only join the existing shots into the cut
# Every shot is re-encoded from its master (frame-accurate trims), then the shots are joined without re-encoding.
set -euo pipefail
csv="${1:?usage}"; masters="${2:?usage}"; out="${3:?usage}"; fmt="${4:-prores}"
SIZE="${SIZE:-5026x2160}"; MIRROR=" ${MIRROR:-} "; w=${SIZE%x*}; h=${SIZE#*x}
case "$fmt" in
  prores)  ext=mov; venc=(-c:v prores_ks -profile:v 4 -pix_fmt yuv444p10le -vendor apl0); aenc=(-c:a pcm_s24le -ar 48000);;
  h264)    ext=mp4; venc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p); aenc=(-c:a aac -b:a 256k -ar 48000);;
  preview) ext=mp4; w=1280; h=$(( (1280*${SIZE#*x}/${SIZE%x*}) / 2 * 2 )); venc=(-c:v libx264 -crf 26 -preset medium -pix_fmt yuv420p); aenc=(-c:a aac -b:a 128k -ar 48000);;
  *) echo "format must be prores, h264 or preview"; exit 1;;
esac
mkdir -p "$out/shots"; list="$out/shots/list.txt"; : > "$list.tmp"
n=0
while IFS=, read -r order take beat in_s out_s rest; do
  case "$order" in ''|order) continue;; esac
  n=$((n+1)); nn=$(printf %02d "$n")
  src="$masters/${take}_4K.mp4"; [ -f "$src" ] || src="$masters/$take.mp4"
  [ -f "$src" ] || { echo "No master for $take in $masters"; exit 1; }
  m=""; vf="scale=$w:$h:force_original_aspect_ratio=increase:flags=lanczos,crop=$w:$h,setsar=1,fps=24"
  case "$MIRROR" in *" $take "*) m="_mirrored"; vf="$vf,hflip";; esac
  shot="$out/shots/${nn}_${take}${m}.$ext"; echo "file '$(basename "$shot")'" >> "$list.tmp"
  [ "${JOIN:-0}" = 1 ] && continue
  if [ -n "${ONLY:-}" ]; then case " $ONLY " in *" $nn "*) ;; *) continue;; esac; fi
  dur=$(awk -v a="$in_s" -v b="$out_s" 'BEGIN{printf "%.3f", b-a}')
  echo "shot $nn $take$m  in $in_s  dur $dur"
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$in_s" -i "$src" -t "$dur" -vf "$vf" \
    -af "aresample=48000,aformat=channel_layouts=stereo" "${venc[@]}" "${aenc[@]}" "$shot"
done < "$csv"
mv "$list.tmp" "$list"
if [ -n "${ONLY:-}" ] && [ "${JOIN:-0}" != 1 ]; then echo "Rendered rows: $ONLY. Run again with JOIN=1 to join."; exit 0; fi
ffmpeg -nostdin -hide_banner -loglevel error -stats -y -f concat -safe 0 -i "$list" -c copy "$out/cut.$ext"
printf 'Cut: %s  (%s s, %d shots)\n' "$out/cut.$ext" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/cut.$ext")" "$n"
