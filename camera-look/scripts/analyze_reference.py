#!/usr/bin/env python3
"""Measure the camera language of a reference clip.

    python3 analyze_reference.py CLIP.mp4 OUT_DIR [--cut 0.35] [--fps 12]

Writes to OUT_DIR:
  shots.csv          one row per shot: start, end, duration, motion class, pan/tilt/zoom/roll, shake, light
  summary.json       cut rhythm, motion mix, cant, light and colour constants for the whole clip
  sheet_NN.jpg       contact sheets: first / middle / last frame of each shot, labelled
  luma.csv           brightness per analysed frame (to check light drift inside a shot)

What it measures is objective (cuts, image motion, brightness, colour). What it cannot measure
(shot size, lens height, who is in frame, mood) is read by Claude from the contact sheets.

Needs: Python 3, numpy, opencv-python (pip install --break-system-packages opencv-python-headless numpy).
"""
import argparse, csv, json, math, os, sys

try:
    import cv2
    import numpy as np
except ImportError:
    sys.exit("Missing numpy/opencv: pip install --break-system-packages opencv-python-headless numpy")


def hist(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [16, 8, 8], [0, 180, 0, 256, 0, 256])
    return cv2.normalize(h, h).flatten()


def global_motion(prev_g, g, orb, bf):
    """Similarity transform between two greyscale frames: dx, dy (px), scale, rotation (deg)."""
    k1, d1 = orb.detectAndCompute(prev_g, None)
    k2, d2 = orb.detectAndCompute(g, None)
    if d1 is None or d2 is None or len(k1) < 12 or len(k2) < 12:
        return None
    m = bf.match(d1, d2)
    if len(m) < 12:
        return None
    p1 = np.float32([k1[x.queryIdx].pt for x in m])
    p2 = np.float32([k2[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    if M is None or inl is None or inl.sum() < 10:
        return None
    s = math.hypot(M[0, 0], M[1, 0])
    rot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
    return M[0, 2], M[1, 2], s, rot


def horizon_cant(g):
    """Rough cant estimate: median deviation of strong near-horizontal and near-vertical lines from level."""
    edges = cv2.Canny(g, 60, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 360, threshold=40, minLineLength=g.shape[1] // 8, maxLineGap=6)
    if lines is None:
        return None
    devs = []
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        a = math.degrees(math.atan2(y2 - y1, x2 - x1))
        a = (a + 90) % 180 - 90  # -90..90
        if abs(a) < 30:
            devs.append(a)  # near horizontal
        elif abs(abs(a) - 90) < 30:
            devs.append((a - 90) if a > 0 else (a + 90))  # near vertical, as deviation
    if len(devs) < 4:
        return None
    return float(np.median(devs))


def classify(sh):
    d = sh["duration_s"]
    pan, tilt, zoom, roll, shake = sh["pan_deg_s"], sh["tilt_deg_s"], sh["zoom_pct"], sh["roll_deg"], sh["shake"]
    moves = []
    if sh["whip"]:
        moves.append("whip")
    if zoom > 8:
        moves.append("push-in/zoom-in")
    elif zoom < -8:
        moves.append("pull-out/zoom-out")
    if abs(pan) > 4:
        moves.append("pan " + ("right" if pan > 0 else "left"))
    if abs(tilt) > 3:
        moves.append("tilt " + ("down" if tilt > 0 else "up"))
    if abs(roll) > 4:
        moves.append("roll")
    base = "handheld" if shake > 0.6 else ("locked" if shake < 0.2 and not moves else "smooth")
    return base + (" + " + ", ".join(moves) if moves else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("out")
    ap.add_argument("--cut", type=float, default=0.35, help="cut sensitivity (histogram distance, 0-1)")
    ap.add_argument("--fps", type=float, default=12, help="analysis frame rate")
    ap.add_argument("--width", type=int, default=480, help="analysis width in pixels")
    ap.add_argument("--hfov", type=float, default=60, help="assumed horizontal field of view, for degrees/s")
    ap.add_argument("--offset", type=float, default=0, help="seconds added to every time (when the clip is a part of a longer film)")
    ap.add_argument("--progress", action="store_true", help="print progress every 100 s of analysed footage")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    cap = cv2.VideoCapture(a.clip)
    if not cap.isOpened():
        sys.exit(f"Cannot open {a.clip}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24
    n_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    W0, H0 = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1, round(src_fps / a.fps))
    w = min(a.width, W0)
    h = int(round(H0 * w / W0 / 2) * 2)
    deg_per_px = a.hfov / w

    # Stream the clip: keep only small per-frame data, so a feature film fits in memory.
    #   jpgs: small JPEG of each analysed frame (contact sheets, cant); motion: frame-to-frame transform
    orb = cv2.ORB_create(600)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    jw = 240; jh = int(round(jw * h / w / 2) * 2)
    jpgs, times, hists, thumbs, luma, warm, sat, motion, cants = [], [], [], [], [], [], [], [], []
    prev_g = None
    i = 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            ok, f = cap.retrieve()
            if not ok:
                break
            f = cv2.resize(f, (w, h), interpolation=cv2.INTER_AREA)
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            times.append(a.offset + i / src_fps); hists.append(hist(f))
            thumbs.append(cv2.resize(g, (64, max(8, int(64 * h / w)))).astype(np.float32))
            jpgs.append(cv2.imencode(".jpg", cv2.resize(f, (jw, jh), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes())
            luma.append(float(g.mean()))
            b, gg, r = [float(c.mean()) for c in cv2.split(f)]
            warm.append(r - b)
            sat.append(float(cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[:, :, 1].mean()))
            motion.append(global_motion(prev_g, g, orb, bf) if prev_g is not None else None)
            cants.append(horizon_cant(g) if len(times) % 4 == 1 else None)  # every 4th frame is enough
            prev_g = g
            if a.progress and len(times) % 1200 == 0:
                print(f"  {times[-1]:.0f} s", file=sys.stderr, flush=True)
        i += 1
    cap.release()
    duration = (n_src or i) / src_fps
    n = len(times)
    if n < 2:
        sys.exit("Clip too short to analyse")
    frame = lambda k: cv2.imdecode(np.frombuffer(jpgs[k], np.uint8), cv2.IMREAD_COLOR)

    # --- cuts: a colour-histogram jump, or a sharp one-frame spike in pixel difference
    #     (motion changes pixels over many frames; a cut changes them in one)
    dist = [0.0] + [1 - cv2.compareHist(hists[k - 1], hists[k], cv2.HISTCMP_CORREL) for k in range(1, n)]
    pdiff = [0.0] + [float(np.abs(thumbs[k] - thumbs[k - 1]).mean() / max(8.0, (thumbs[k].mean() + thumbs[k - 1].mean()) / 2))
                     for k in range(1, n)]
    def spike(k):
        nb = [pdiff[j] for j in range(max(1, k - 4), min(n, k + 5)) if abs(j - k) > 1]
        return pdiff[k] / max(0.02, float(np.median(nb))) if nb else 0.0
    score = [dist[k] + pdiff[k] for k in range(n)]
    cand = [k for k in range(1, n) if dist[k] > a.cut or (pdiff[k] > 0.25 and spike(k) > 3 and dist[k] > 0.1)]
    min_gap = max(2, int(0.25 * a.fps))
    cuts = []
    for k in cand:
        if cuts and k - cuts[-1] < min_gap:
            if score[k] > score[cuts[-1]]:
                cuts[-1] = k
        else:
            cuts.append(k)
    flashes = [round(times[k], 2) for k in range(n) if luma[k] > 235]
    bounds = [0] + cuts + [n]

    # --- per-shot motion (transforms across a cut are never used: k runs inside the shot)
    shots = []
    for s in range(len(bounds) - 1):
        a0, a1 = bounds[s], bounds[s + 1]
        t0 = times[a0]
        t1 = times[a1] if a1 < n else a.offset + duration
        dxs, dys, scs, rots = [], [], [], []
        for k in range(a0 + 1, a1):
            m = motion[k]
            # drop implausible frame-to-frame jumps (bad matches, hidden cuts); whips are caught by dx alone
            if m and abs(m[0]) < 0.5 * w and abs(m[1]) < 0.4 * h:
                dxs.append(m[0]); dys.append(m[1])
                if 0.93 < m[2] < 1.07 and abs(m[3]) < 2.5:
                    scs.append(m[2]); rots.append(m[3])
        dur = max(t1 - t0, 1e-3)
        if dxs:
            dx, dy = np.array(dxs), np.array(dys)
            # camera pans right -> image moves left: negate
            pan = -dx.sum() * deg_per_px / dur
            tilt = -dy.sum() * deg_per_px / dur
            zoom = (float(np.prod(scs)) - 1) * 100 if scs else 0.0
            roll = float(np.sum(rots)) if rots else 0.0
            k = 3 if len(dx) >= 5 else 1
            smooth = lambda v: np.convolve(v, np.ones(k) / k, mode="same")
            shake = float(np.sqrt(np.mean((dx - smooth(dx)) ** 2 + (dy - smooth(dy)) ** 2)))
            whip = bool(np.max(np.abs(dx)) * deg_per_px * a.fps > 120)
        else:
            pan = tilt = zoom = roll = shake = 0.0
            whip = False
        mid = (a0 + a1 - 1) // 2
        cs = [c for c in cants[a0:a1] if c is not None]
        cant = float(np.median(cs)) if cs else None
        seg = slice(a0, a1)
        sh = dict(shot=s + 1, start_s=round(t0, 3), end_s=round(t1, 3), duration_s=round(dur, 3),
                  pan_deg_s=round(pan, 1), tilt_deg_s=round(tilt, 1), zoom_pct=round(zoom, 1),
                  roll_deg=round(roll, 1), shake=round(shake, 2), whip=whip,
                  cant_deg=None if cant is None else round(cant, 1),
                  luma=round(float(np.mean(luma[seg])), 1),
                  luma_drift=round(luma[a1 - 1] - luma[a0], 1),
                  warmth=round(float(np.mean(warm[seg])), 1), saturation=round(float(np.mean(sat[seg])), 1))
        sh["motion"] = classify(sh)
        shots.append(sh)

    # --- write shots.csv / luma.csv
    with open(os.path.join(a.out, "shots.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(shots[0].keys()))
        wr.writeheader(); wr.writerows(shots)
    with open(os.path.join(a.out, "luma.csv"), "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["t_s", "luma", "warmth"])
        for t, l, wm in zip(times, luma, warm):
            wr.writerow([round(t, 3), round(l, 1), round(wm, 1)])

    # --- summary
    d = np.array([x["duration_s"] for x in shots])
    def share(pred):
        return round(100 * sum(1 for x in shots if pred(x)) / len(shots))
    summary = dict(
        clip=os.path.basename(a.clip), duration_s=round(duration, 2), fps=round(src_fps, 3), size=f"{W0}x{H0}",
        shots=len(shots), cuts_per_min=round(60 * (len(shots) - 1) / max(duration, 1e-3), 1),
        shot_length_s=dict(mean=round(float(d.mean()), 2), median=round(float(np.median(d)), 2),
                           min=round(float(d.min()), 2), max=round(float(d.max()), 2)),
        shot_length_mix_pct={"<1s": share(lambda x: x["duration_s"] < 1), "1-3s": share(lambda x: 1 <= x["duration_s"] < 3),
                             "3-6s": share(lambda x: 3 <= x["duration_s"] < 6), ">=6s": share(lambda x: x["duration_s"] >= 6)},
        motion_pct={"handheld": share(lambda x: x["motion"].startswith("handheld")),
                    "locked": share(lambda x: x["motion"].startswith("locked")),
                    "push_in": share(lambda x: "push-in" in x["motion"]), "pull_out": share(lambda x: "pull-out" in x["motion"]),
                    "pan": share(lambda x: "pan" in x["motion"]), "tilt": share(lambda x: "tilt" in x["motion"]),
                    "whip": share(lambda x: x["whip"]), "roll": share(lambda x: "roll" in x["motion"])},
        canted_over_8deg_pct=share(lambda x: x["cant_deg"] is not None and abs(x["cant_deg"]) > 8),
        flashes_at_s=flashes[:50],
        light=dict(luma_mean=round(float(np.mean(luma)), 1), luma_shot_spread=round(float(np.std([x["luma"] for x in shots])), 1),
                   warmth_mean=round(float(np.mean(warm)), 1), saturation_mean=round(float(np.mean(sat)), 1)),
        notes="Motion is image motion: a push-in and a zoom-in look alike, and an orbit reads as a pan. "
              "Cant is a rough line-angle estimate. Read the contact sheets for shot size, lens height and staging.")
    with open(os.path.join(a.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

    # --- contact sheets: 2 shots per row, 3 frames per shot (first, middle, last)
    tw = 200; th = int(tw * h / w)
    def tc(t):
        return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}" if a.offset or duration >= 600 else f"{t:.2f}s"
    per_sheet = 24
    for sheet_i in range(0, len(shots), per_sheet):
        chunk = shots[sheet_i:sheet_i + per_sheet]
        cols = 2
        rows = math.ceil(len(chunk) / cols)
        cell_w, cell_h = tw * 3 + 12, th + 26
        img = np.full((rows * cell_h + 8, cols * cell_w + 8, 3), 24, np.uint8)
        for j, sh in enumerate(chunk):
            a0, a1 = bounds[sh["shot"] - 1], bounds[sh["shot"]]
            picks = [a0, (a0 + a1 - 1) // 2, a1 - 1]
            x0 = 8 + (j % cols) * cell_w; y0 = 8 + (j // cols) * cell_h
            for q, k in enumerate(picks):
                img[y0 + 22:y0 + 22 + th, x0 + q * tw:x0 + (q + 1) * tw] = cv2.resize(frame(k), (tw, th))
            label = f"#{sh['shot']}  {tc(sh['start_s'])}  {sh['duration_s']:.2f}s  {sh['motion']}"
            cv2.putText(img, label[:70], (x0, y0 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(a.out, f"sheet_{sheet_i // per_sheet + 1:02d}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 85])

    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
