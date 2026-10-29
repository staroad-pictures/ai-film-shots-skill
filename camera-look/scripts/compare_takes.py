#!/usr/bin/env python3
"""Compare generated takes against a reference look, using analyze_reference.py outputs.

    python3 compare_takes.py REF_DIR TAKE_DIR [TAKE_DIR ...]

Each DIR is an output folder of analyze_reference.py (it holds summary.json and shots.csv).
Prints, per take: shots, average shot length, handheld share, push/pull, cant, brightness and
warmth against the reference, and flags what is far off. Numbers guide the eye; they do not
replace looking at the contact sheets.
"""
import csv, json, os, sys


def load(d):
    s = json.load(open(os.path.join(d, "summary.json")))
    rows = list(csv.DictReader(open(os.path.join(d, "shots.csv"))))
    return s, rows


def metrics(s, rows):
    cants = [abs(float(r["cant_deg"])) for r in rows if r["cant_deg"] not in ("", "None")]
    return {
        "shots": s["shots"],
        "avg_shot_s": s["shot_length_s"]["mean"],
        "handheld_%": s["motion_pct"]["handheld"],
        "push_in_%": s["motion_pct"]["push_in"],
        "pull_out_%": s["motion_pct"]["pull_out"],
        "cant_deg": round(sum(cants) / len(cants), 1) if cants else 0.0,
        "luma": s["light"]["luma_mean"],
        "warmth": s["light"]["warmth_mean"],
        "luma_drift_max": max(abs(float(r["luma_drift"])) for r in rows),
    }


# how far a take may sit from the reference before it is flagged
TOL = {"avg_shot_s": 0.5, "handheld_%": 30, "push_in_%": 40, "pull_out_%": 40, "cant_deg": 6,
       "luma": 20, "warmth": 15, "luma_drift_max": 25}


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ref = metrics(*load(sys.argv[1]))
    keys = list(ref.keys())
    print(f"{'':28}" + "".join(f"{k:>15}" for k in keys))
    print(f"{'REFERENCE':28}" + "".join(f"{ref[k]:>15}" for k in keys))
    for d in sys.argv[2:]:
        m = metrics(*load(d))
        cells = []
        for k in keys:
            v = m[k]
            flag = ""
            if k == "avg_shot_s":
                # relative tolerance on shot length (a single generated take is one long shot: skip)
                if m["shots"] > 1 and abs(v - ref[k]) > TOL[k] * max(ref[k], 1):
                    flag = " !"
            elif k == "luma_drift_max":
                # only more light drift than the reference is a problem
                if v > ref[k] + TOL[k]:
                    flag = " !"
            elif k in TOL and abs(v - ref[k]) > TOL[k]:
                flag = " !"
            cells.append(f"{str(v) + flag:>15}")
        print(f"{os.path.basename(os.path.normpath(d))[:28]:28}" + "".join(cells))
    print("\n'!' = far from the reference. Generated takes are cut down in the edit, so judge shot length on the cut, not the take.")


if __name__ == "__main__":
    main()
