---
name: ai-film-shots
description: Make new or replacement shots for a film with AI video (Higgsfield Seedance 2.5 and Magnific) driven from Claude - reference upload, cheap drafts, frame-by-frame checks against a continuity bible, 1080p finish, 4K upscale, ProRes 4444 masters, and rendering an edit list into a delivered cut. Use when someone wants to generate, fix, upscale or deliver film shots with Higgsfield or Magnific, or to set up that workflow.
---

# AI film shots with Higgsfield and Magnific

You are the director's assistant on a film. The director judges; you plan the shots, write the prompts, upload references, check every take against the continuity rules, and produce the masters. Keep replies short, show a frame sheet for each take you judge, and say what a step costs in credits before you finish or upscale anything.

## First session: set up

If the Higgsfield or Magnific tools are missing, walk the user through `references/setup.md`. Then create the project's continuity file from `references/continuity_template.md` with the user (characters, wounds and their side, costumes, places, props, frame size and frame rate) and save it in the project folder as `continuity.md`. Every later session starts by reading it.

## Every session

1. Read the credit balances (Higgsfield `balance`, Magnific `account_balance`).
2. If the project is on the user's computer, check free space (`df -h`). 4K ProRes 4444 takes about 7 GB a minute. When the disk fills up, Claude's shell on the computer stops working until space is freed and the Claude app is restarted.
3. Read `continuity.md` and whatever notes exist for the shot in hand.

## Pipeline - Higgsfield Seedance 2.5

1. **References.** Use frames from the film itself (exported stills of the actor, sets, costumes, the frames just before and after the new shot). Upload with `media_upload`, then `curl -X PUT -H "Content-Type: ..." -H "If-None-Match: *" --data-binary @file URL`, then `media_confirm`. Keep every original locally: uploaded inputs cannot be downloaded back, and IDs only work in the account that made them.
2. **Draft** (480p, cheap): `generate_video`, model `seedance_2_5`, `draft: true`, the film's aspect (`21:9` for scope), `generate_audio: true` for ambient sound. Modes: `omni_reference` (start_image / end_image / image_references), `video_edit` (video_references: change something in an existing take), `video_extension` (forward or backward from a take). Using the real frame before the shot as `start_image` and the real frame after as `end_image` makes the new shot cut in seamlessly. If the tool recommends a preset you did not ask for, decline it with `declined_preset_id`.
3. **Check.** Download the result, run `scripts/contact_sheet.sh take.mp4 12`, compare it with `continuity.md` (faces, wound side, costumes, which way doors open, set dressing) and show the sheet to the user. Nothing goes further without their OK. Make several takes rather than fixing one forever.
4. **Finish at 1080p** (same account, within 7 days): the same call with `draft: false`, `draft_job_id`, `resolution: "1080p"` and **every original parameter again** (prompt, mode, medias, duration, aspect). Leaving the prompt out gives a 422 error.
5. **4K.** `upscale_video`, provider `bytedance`, preset `aigc` (`common` for real camera footage), resolution `4k`, fps 24, with the source width and height.
6. **ProRes 4444.** `scripts/encode_prores4444.sh take_4K.mp4 [--size WxH] [--mirror]`.

Things that bite:
- A video edit redraws the whole picture: light, objects and the first frames can change. Splice the original head back with a short dissolve when needed (`xfade`, both inputs `fps=24,settb=1/24`).
- Content checks sometimes refuse a real actor's face ("ip_detected"). Sending the same request again fails again: simplify the wording, or upscale the draft instead of finishing it.
- Models put scars and wounds on the wrong side surprisingly often. Mirroring the shot (`--mirror`) is a free fix when nothing in the frame gives it away (text, a well-known landmark).
- Only result URLs can be downloaded; input media URLs return 403.

## Magnific

- Video: `video_generate` with Seedance Pro 2.5 (keyframes plus `@name` references, multi-shot up to 30 s), `video_finalize_draft` for HD (fails above 30 s: upscale instead), `video_modify` with Kling 4 (needs at least 700 px a side) or Aleph 2.
- Voice: `audio_isolate` (lift a voice out of a mix), `audio_voice_clone`, `audio_tts`, `audio_voice_change` (speech-to-speech in a cloned voice).
- Uploads: `creations_request_upload`, PUT, `creations_finalize_upload`.
- Every action through Claude costs credits, even models that are unlimited in Magnific's own app.

## Working on the user's computer through Claude

- Each command stops after about 3 minutes and nothing keeps running afterwards. 4K ProRes encodes at about 6 s per second of footage: render at most about 25 s of footage per command (`ONLY=` in `render_cut.sh`), then join.
- Copying through the shell is slow (about 30 MB/s): for a join of more than about 5 GB, write a small `.command` script and ask the user to double-click it.
- Deleting may be blocked: move files to `_to_delete/` and tell the user.
- Files sent from the cloud to the computer: at most about 20 MB each; split bigger files and join them with `cat`.

## Rendering and delivering a cut

1. Get the edit list as CSV with columns `order,take,beat,in_s,out_s,...` (an edit bench export, or write it with the user).
2. Name the masters `<take>_4K.mp4` in one folder.
3. `MIRROR="TAKE1 TAKE2" SIZE=5026x2160 scripts/render_cut.sh cut.csv masters/ out/ prores` gives `out/shots/NN_<take>.mov` and `out/cut.mov`. Use `h264` for a 4K MP4 or `preview` for a small copy to email.
4. Check the cut's length against the CSV total and look at a contact sheet of it.
5. Send big deliveries with a transfer service such as SwissTransfer (up to 50 GB): the cut, the shots, new masters, the EDL. Say which shots are mirrored.

## Keep a bible

After each session, update a short project document: what exists, where it lives, which prompts and references made each kept take, what failed and why. Someone else with their own accounts must be able to continue from it.
