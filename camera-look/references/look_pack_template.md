# Look pack: <name>

Reference: <title or file>, <length>, <what it is: trailer, scene, ad, our own cut>. Analysed <date>.
Use for: <which scenes, project or client>.

## Measured (from summary.json)

- Shots: <n>, about <cuts per minute> cuts a minute. Shot length: average <x> s, median <x> s, shortest <x> s, longest <x> s.
- Mix: <% under 1 s> / <% 1-3 s> / <% 3-6 s> / <% 6 s and over>.
- Camera: <% handheld>, <% locked>, <% push-in>, <% pull-out>, <% pan>, <% tilt>, <% whip>.
- Cant: <% of shots canted more than 8 degrees>.
- Light: brightness <luma mean>/255 (spread between shots <x>), warmth <x>, saturation <x>. Flashes: <none or times>.

## Seen on the contact sheets

- Shot sizes: <share of wide / full / medium / close-up / extreme close-up>.
- Lens height: <eye level / waist / floor / high / overhead, and when each is used>.
- Angles on people: <frontal, three-quarter, profile, over the shoulder, from behind>.
- Staging and movement: <who moves, toward or across the lens, crowds, depth>.
- Light: <sources in frame (torches, windows, practicals), direction, contrast, haze>.
- Colour: <palette and grade in plain words>.
- Transitions: <hard cuts, whips, flashes, dissolves, match cuts>.

## House rules

Always:
- <5 to 8 rules that make this look, each one checkable on a frame>

Never:
- <the things that would break it>

## Principles (4 to 6)

### 1. <name>
<One or two sentences: what it is and when it is used in the reference.>
> Prompt wording: `<words for Seedance, written to the tested notes>`

## Wording table

| Shot type | Prompt wording |
|---|---|
| <e.g. hero walk> | `<...>` |

## Generation plans (3 or 4)

### Plan A: <name> (<duration> s, <shots>)
```
<shot-by-shot lines, each with a size, a move, an end state, and at most one move per 4 s>
```
Cut in the edit: <which parts are kept and at what lengths>.

## Rhythm in the edit

<How generated takes are cut to reach the reference shot lengths: e.g. "generate 8 s takes, keep 3 to 5 s from each".>

## Sound line

<Ambience and effects to ask for; music is added in post unless the look needs source music.>

## Checks after each batch

Run `analyze_reference.py` on the takes and `compare_takes.py` against this reference. Look at: handheld share, push/pull share, cant, brightness and warmth. Judge shot length on the edited cut, not on single takes.
