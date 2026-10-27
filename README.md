# AI film shots - a Claude skill

A Claude skill for making new or replacement shots of a film with AI video, driven from Claude:

- **Higgsfield** (Seedance 2.5): drafts, video edits, extensions, 1080p finish, 4K upscale
- **Magnific**: Seedance Pro 2.5 multi-shot, Kling 4, Aleph 2, voice isolation and cloning

and the dull but essential part around them: a continuity file to check every take against, frame sheets, ProRes 4444 masters, and rendering an edit list (CSV) into a delivered cut, one file per shot plus the joined cut.

It was written while redoing shots of a family feature film with Claude, Higgsfield and Magnific over a weekend, and collects what worked and what bit us.

## Install

1. Set up Claude, Higgsfield and Magnific: see [`ai-film-shots/references/setup.md`](ai-film-shots/references/setup.md).
2. Zip the `ai-film-shots` folder (or download the zip from Releases) and add it to Claude as a skill.
3. In a new chat: *"Use the ai-film-shots skill. Help me write the continuity file for my film."*

## Scripts (need ffmpeg)

| Script | What it does |
| --- | --- |
| `scripts/contact_sheet.sh IN.mp4 [N]` | One image with N stamped frames of a take, to judge it at a glance |
| `scripts/encode_prores4444.sh IN [OUT] [--mirror] [--size WxH]` | ProRes 4444 master, optionally mirrored and conformed |
| `scripts/render_cut.sh CUT.csv MASTERS/ OUT/ [prores\|h264\|preview]` | Frame-accurate shots from an edit list, then the joined cut |
| `scripts/make_preview.sh IN.mp4 ID [DIR]` | 720 px preview and thumbnail of a take |

## Licence

MIT - see [LICENSE](LICENSE).
