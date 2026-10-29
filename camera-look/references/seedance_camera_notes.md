# Seedance 2.5 camera notes (tested)

What Seedance 2.5 actually does with camera wording, from our own A/B tests: text-to-video, 480p, 16:9, the same neutral scene (a bearded man in a wool cloak in a torchlit stone hall), 2 takes per wording, measured with `scripts/analyze_reference.py` and checked frame by frame. The prompts and frame strips are in the repository under `tests/camera-look-2026-10-29/`. Tested 29 Oct 2026 on Higgsfield `seedance_2_5`, about 520 credits for 30 clips; tests 7 and 8 (blinking and dramatic context, added the same day after a viewer said still characters look stoic) about 160 credits for 10 clips.

Two takes per wording is a small sample. Treat these as strong hints, re-test when the model changes, and add new results here with the date.

## Results

| # | Question | What happened | Rule we keep |
|---|---|---|---|
| 1 | Does a push-in stop where you ask? | With no end size, both takes pushed to chest-up. With "ending at medium shot, waist up; never closer than chest height", both stopped wider than asked (thighs-up). Without the "never closer" guard, one of two went one size tighter. | Always name the end size **and** a limit ("never closer than..."). Expect plus or minus one shot size; fine-tune by cropping the 4K. |
| 2 | How do you get a Dutch angle? | "Dutch tilt 20 degrees": no visible tilt (0/2). "The camera body is canted about N degrees; the roll belongs to the camera only": 12 degrees gave nothing (0/2), 15 degrees gave about 20 in one take and nothing in the other, 20 degrees gave 21 to 28 degrees (2/2). "The whole frame is rotated 15 degrees": nothing (0/2). The actor was never tilted on his own: when the frame tilted, the room and the actor tilted together. | A cant is all or nothing. For a strong cant, use the camera-body wording at about 20 degrees and expect more. For a subtle or exact cant, rotate in post from the 4K master (see below). |
| 3 | Does it matter where the light is described? | Light described first ("from the very first frame, constant") or last: no difference. Brightness drifted by less than 9 levels out of 255 in all four takes. | Describe the light anywhere. (Changing the light during a shot was not tested.) |
| 4 | How many camera moves fit in a take? | Five moves in 8 s (push, orbit, tilt, whip, pull back): the moves roughly happened, but both takes broke: the actor jumped to another spot, a table with a map appeared from nowhere, the whip turned into a cut. Two moves of 4 s each: both clean. | One camera move per 4 s or so. If you need more, make more takes and cut them together. |
| 5 | Do sound words like "water dripping", "echo" cause ripples in the picture? | No ripples or water artifacts in either take, same as the control. The sound itself was not judged. | No need to avoid those words for the picture. |
| 6 | Can you time cuts inside a multi-shot take? | Asked for cuts at 2.5 s and 4.5 s: they landed 0.1 to 0.9 s off. Asked for cuts at 3 s and 5 s: 0.25 s off in one take; the other added an extra shot. | Shot timings in a prompt are approximate either way; decimals are fine but no more precise. Put exact cut points in the edit. |
| 7 | How do you get natural blinking on a still character? | Nothing asked: 0 to 1 blink in 5 s, one take ended with eyes drifting half-closed (stiff). "Blinks naturally every few seconds, breathing, fingers on the cloak": about 6 blinks in 5 s in both takes, a nervous flutter. "Blinks only once or twice, calm": 1 slow blink (1.3 s, sleepy) and 2 natural blinks. "Quick blinks, each over in a fraction of a second, about one every three or four seconds": 2 quick natural blinks in one take, 6 in the other. Breathing and hand movement did not show clearly in any take. | Not a default. Only for close-ups held on a still face for more than 3 s: ask with a number and a speed ("blinks quickly once or twice in the shot"), make 2 takes, keep the calm one (2 of 4 takes good, against 0 of 2 with nothing asked). Never "blinks naturally" alone. Real people blink about once every 3 to 4 seconds, each blink well under half a second. |
| 8 | Does the dramatic situation alone bring a still face to life? | Same close-up, no word about blinking or breathing, but the situation given: "marched since dawn, just shoved into this hall, catching his breath, wary, listening for the door behind him". Both takes came alive: one acted the entrance (stumbles in, leans on a pillar, breathless, looks around), the other stood still with darting eyes, small head shifts and visible breathing. Body movement 1.6 and 0.8 against 0.2 and 0.5 for the neutral prompt. No flutter. One take played the past event on screen (the shove), which changed the framing. | Direct the moment, not the mechanics: say what just happened, what the character feels or wants, and what comes next. Put past events in the past ("a moment ago he was shoved in") and say what the shot shows now ("he stands still, catching his breath"), or the model acts them out. Blinking instructions are only a fix for a take that still comes out frozen. |

Other things seen during the tests:
- 3 of 33 requests came back flagged "nsfw" on a harmless prompt. The credits were returned, and sending the same prompt again worked.
- Without reference images, every take invents a different hall and a different man. For continuity, use real frames as references (see the `ai-film-shots` skill).
- Camera shake (the `shake` column of `shots.csv`, measured at 480 px): on a man standing still, "handheld" in the prompt gave only 0.2 to 0.5, against 0.03 to 0.4 without the word, so nearly still either way. Visible shake came with movement: walking toward the camera or pushing in gave 1 to 4. For comparison, a handheld feature-film sequence we measured sits at 0.7 to 3, and a locked-off shot at about 0.2. How to ask for stronger shake on a still subject is not tested yet.

## Cant in post

Rotating a frame by an angle means zooming in to hide the corners. For a 16:9 frame the zoom needed is `cos(a) + (16/9) * sin(a)`: about 1.15 for 5 degrees, 1.24 for 8, 1.35 for 12 (for scope 2.39:1, use 2.39 instead of 16/9: 1.20, 1.32, 1.47). From a 4K master delivered at 1080p that is free. With ffmpeg (8 degrees, 3840x2160 master):

```
ffmpeg -i in_4K.mp4 -vf "rotate=8*PI/180:ow=iw:oh=ih,scale=iw*1.24:-2,crop=3840:2160" -c:v libx264 -crf 16 out.mp4
```

Use a positive angle for clockwise. Animate it (`rotate='8*PI/180*t/3'`) for a roll that builds.
