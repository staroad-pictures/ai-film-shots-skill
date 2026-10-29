---
name: camera-look
description: Turn a reference film, scene, trailer or ad into a measured "look pack" (cut rhythm, camera moves, angles, cant, light and colour) and write Seedance 2.5 prompts (Higgsfield or Magnific) that reproduce that camera language, then check the takes against the reference. Use when someone shares a reference clip and wants AI shots to feel like it, asks for the camera style or grammar of a film, wants a style guide for AI video, or says their AI shots look static or fake.
---

# Camera look from a reference

The director brings a reference ("make it feel like this"). You measure it, describe it, turn it into prompt wording that Seedance 2.5 really follows, and check the takes against the same numbers. Keep replies short; show a contact sheet whenever you make a claim about the reference or a take.

This skill covers the camera language. For references, drafts, finishing, 4K and delivery, use the `ai-film-shots` skill.

## 1. Get the reference

- A video file the user has: a scene, a trailer, an ad, or their own cut. 15 s to 3 min is plenty. Several short references can each get their own pack.
- The reference is for analysis only. Do not feed its frames to a generator as image references unless the user owns it.
- Note what the user likes about it in their words ("the camera feels nervous", "the light is all torches"). That decides which principles matter.

## 2. Measure it

```
python3 scripts/analyze_reference.py reference.mp4 look/<name>/ref
```

Needs Python with numpy and OpenCV (`pip install --break-system-packages opencv-python-headless numpy`). On a long clip it takes about 20 s a minute.

It writes `summary.json` (cut rhythm, camera motion mix, cant, light and colour), `shots.csv` (one row per shot), `luma.csv` and contact sheets `sheet_NN.jpg` with the first, middle and last frame of each shot.

Know its limits:
- Motion is measured on the background. A push-in and a zoom look alike; a camera backing away from someone walking toward it reads as a pull-out; an orbit reads as a pan.
- Cut detection misses cuts between two very similar shots and can count a whip-pan as a cut.
- Cant is a rough line-angle estimate; dark shots often have none.

## 3. Look at it

Read every contact sheet. For each shot, note what the numbers cannot give: shot size, lens height, angle on the actor, who moves and where, light sources and direction, colour. Correct the motion labels where your eyes disagree. Then summarise what is constant (the look) and what varies (the coverage).

## 4. Write the look pack

Copy `references/look_pack_template.md` to `look/<name>/look_<name>.md` and fill it in:
- the measured numbers and what the sheets show;
- 5 to 8 house rules, each checkable on a frame;
- 4 to 6 principles, each with prompt wording;
- a wording table, 3 or 4 generation plans, the rhythm for the edit, the sound line.

Write the prompt wording to `references/seedance_camera_notes.md`, which records what Seedance 2.5 really does. The main points:
- Name where every push-in or zoom ends, and add a limit ("never closer than chest height"). Expect plus or minus one shot size.
- One camera move per 4 s or so. Crowding moves breaks the shot (the actor jumps, props appear).
- Dutch angles: "dutch tilt" alone does nothing. "The camera body is canted about 20 degrees; the roll belongs to the camera only" works and tends to overshoot; small angles are ignored. For a subtle or exact cant, rotate in post from the 4K.
- Shot timings inside a take are approximate (up to about 1 s off). Fast rhythm and exact cut points are made in the edit from longer takes.
- "Handheld" alone barely moves the camera on a still subject; visible shake comes with movement (walking, push-ins). Leave the word out for a still frame.
- Blinking, only for close-ups held on a still face for more than 3 s (a frozen face shows most there): ask with a number and a speed ("he blinks quickly once or twice in the shot"), make 2 takes, keep the calm one. It worked in about half the takes. Never write "blinks naturally" alone (it gave a nervous flutter in both takes). Leave blinking out of wide shots and moving characters.

## 5. Test before the real shots

1. Pick 2 or 3 plans from the pack. Make 2 takes of each as 480p drafts (Higgsfield `seedance_2_5`, about 3 credits a second; say the cost first).
2. Measure each take with `analyze_reference.py` into `look/<name>/takes/<take>`.
3. Compare: `python3 scripts/compare_takes.py look/<name>/ref look/<name>/takes/*`. It flags takes far from the reference on handheld, push/pull, cant, brightness and warmth.
4. Show the user the take contact sheets next to the reference sheets. Adjust the wording, not the rules, and test again if needed.
5. When a new behaviour shows up (something Seedance does or ignores), add it with the date to `references/seedance_camera_notes.md`.

## 6. Use it

- Every shot prompt for that look starts from the pack: house rules plus the plan's lines, with the subject, wardrobe and place from the project's continuity file.
- After a cut is assembled, measure the cut itself and compare it with the reference: shot length belongs to the edit, not to single takes.
- Keep packs in the project folder (`look/`) so the next scene, or the next person, starts from them.
