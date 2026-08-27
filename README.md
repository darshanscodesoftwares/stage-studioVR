# stage-studioVR

A WebXR trainer for stage fright. You stand on a stage, in front of an
audience, and speak — for the repeated, controllable exposure, plus honest
feedback on how you actually sounded.

The brief is [PROJECT.md](PROJECT.md). This file is how to run what exists.

**Status: M0 complete.** The hall, the stage and the microphone work. There is
no audience yet — that is deliberate, and the reason why is in the brief.

---

## Run it

**Desktop:**

```bash
python3 -m http.server 8899        # from the project root
```

then open <http://localhost:8899>. `localhost` counts as a secure context, so
the microphone works without HTTPS.

**Headset:** the page must be on **HTTPS**. Plain HTTP fails twice over — the
Enter VR button never appears, *and* `getUserMedia` is not exposed, so the mic
is dead as well. Push to GitHub and serve it as a Render Static Site with
`index.html` at the repo root; that is zero-config.

## Controls

| Input | Action |
| --- | --- |
| Left thumbstick | Walk |
| Right thumbstick ←/→ | Snap turn, 30° |
| **A** or **X** button | House lights up / down — the difficulty dial |
| <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> | Walk (desktop) |
| Mouse drag | Look (desktop) |
| <kbd>L</kbd> | House lights (desktop) |
| <kbd>R</kbd> | Return to the lectern |

## What M0 is for

The first milestone deliberately skips the audience and proves the two things
that decide whether the project is possible at all.

**1. The microphone permission flow.** A permission prompt cannot be raised
from inside an immersive WebXR session. If it is not granted on the flat page
first, there is no microphone at all, and the whole coaching half of the
product is gone. So the flat lobby is not decoration — it is the only place
the mic can be asked for, and it shows a live level bar so a failure is
obvious before the headset goes on rather than after.

**2. The frame budget.** Measured headless, an empty hall costs:

| | |
| --- | --- |
| Draw calls | **34–39** |
| Triangles | **~5.1k** |
| Lights | 7 (1 hemisphere, 4 point, 2 spot — one spot casts) |
| Downloaded assets | **none** — A-Frame from CDN and nothing else |
| Page weight | 60 KB |

The overhead lighting rig is deliberately built with `THREE.InstancedMesh`:
**14 fixtures cost 2 draw calls, not 28.** That is a small rehearsal of the
technique the audience will live or die by.

That is a very large amount of headroom to spend on people, which is the point
of measuring it before building any.

**Not yet verified: the actual 72fps on-device.** The geometry budget is known
and it is tiny, but frame rate is a property of the headset, not of this
machine — a 2012 Intel IGP says nothing about a Snapdragon XR2. The frame
counter floats in front of you in VR so the number can be read while wearing
it. That reading is the real M0 sign-off.

## How it is built

One self-contained [index.html](index.html). A-Frame 1.7.0 from a CDN, no build
step, no `node_modules`, nothing to install. Edit the file, reload the headset.

- **Every texture is generated at runtime on a canvas** — plaster, stage plank,
  carpet, acoustic ceiling tile — with normal maps derived from the same canvas
  by a Sobel filter. Nothing to download, nothing that can 404 mid-demo, and a
  greyscale base multiplies over any colour, so one texture serves every paint.
- **The hall is built in code from `HALL`**, not written out as markup, so the
  dimensions, the geometry and the walkable regions cannot drift apart.
- **Walkable space is a union of rectangles**, each with a floor height. A move
  is legal if it lands inside one; eye height eases toward the tallest region
  containing you, which is what makes the three steps read as steps rather than
  as teleports. The same code path serves keyboard and thumbstick, so desktop
  and headset can never disagree about where a wall is.
- **Every component is prefixed `sv-`.** A-Frame 1.7.0 registers 58 components
  of its own, and a duplicate name throws — which aborts the rest of the script
  and looks exactly like a lighting bug. See gotcha 1 in the brief; it cost the
  sister project a day.
- **ACES Filmic tone mapping is load-bearing, not decoration.** Without it the
  renderer writes raw linear values: ceiling lamps clip to flat white discs and
  every surface facing away from a light crushes to black. It was the single
  largest visual improvement in the polish pass, for one renderer property.
- **Shadows are cast by exactly one light**, the stage-left spot, onto the
  stage only, from a 1024 map. That is enough to stop the lectern and the mic
  stand floating. The audience will never cast — the brief is explicit that
  shadow casting from a hundred figures is not affordable and nobody looks at
  the floor.

## Verifying a change

Do not claim a change works without rendering it. From the project root:

```bash
python3 -m http.server 8899
google-chrome --headless=new --no-sandbox \
  --use-angle=swiftshader --enable-unsafe-swiftshader \
  --enable-logging=stderr --v=0 --virtual-time-budget=30000 \
  --screenshot=/tmp/shot.png http://localhost:8899/index.html
```

Swap `--screenshot` for `--dump-dom` and grep stderr for `CONSOLE` to read the
console. To measure something in-scene, write a temporary copy of `index.html`
with a probe script appended and `console.log` the numbers.

Two things that bite in this harness:

- **The lobby covers the scene.** A screenshot of the unmodified page shows the
  permission panel, not the hall. Hide `#lobby` in the probe.
- **Virtual time does not drive the audio thread.** Timers fast-forward while
  Web Audio runs on the real clock, so every `setTimeout` sample reads the same
  buffer and a signal test silently measures nothing. Test `Mic.sample()` by
  stubbing `analyser.getFloatTimeDomainData` with a known waveform instead.

## Lighting units — read before touching an intensity

three.js r155 removed legacy light units, so r173 is physically based. A
point or spot light falls off as `intensity / distance^decay`, which means a
ceiling lamp 7 m up at `intensity: 0.5` delivers about `0.01` and the room
renders black. Punctual lights now want values in the **tens or hundreds**;
hemisphere, ambient and directional lights are not distance-attenuated and stay
in the **0–3** range. Mixing those two scales up is the single easiest way to
produce a scene that looks like a lighting bug but is not one.

The house-lights switch exploits this. Stage lights in your eyes is **easy
mode** — you cannot see any faces. House lights up is **hard mode**. The brief
suspects that one switch may be the most useful setting in the whole app.

## Next

M1, in the order the brief argues for:

1. Prototype the crowd **empty** — instanced billboards first, then measure,
   then decide the maximum audience size. Everything else depends on that number.
2. Seating geometry, generated parametrically, carving the walkable regions.
3. Room tone and murmur, and a `ConvolverNode` reverb from a runtime-generated
   impulse response.
4. The tabbed panel on the left controller, carried over from room-studioVR.

Open questions are listed at the end of [PROJECT.md](PROJECT.md). The one that
needs answering before any modelling starts is where the audience figures come
from and under what licence.
