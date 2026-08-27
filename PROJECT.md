# stage-studioVR — public speaking practice in VR

**Status: M0 built, awaiting on-device sign-off.** This file is the brief.
Read it before writing any code, and update it as decisions get made.
[README.md](README.md) covers what now exists and how to run it.

Settled since this brief was written, by measurement rather than assumption:

- A-Frame 1.7.0 bundles **three.js r173**, and registers **58** components of
  its own — `grabbable` among them, as gotcha 1 warned.
- three r173 uses **physically based light units**. Punctual lights need
  intensities in the tens or hundreds; hemisphere and ambient stay in the 0–3
  range. This is a tenth gotcha and it is now in the list below.
- A furnished-but-empty hall costs **34–39 draw calls and ~5.1k triangles**,
  with no downloaded assets at all. The headroom for the audience is very
  large.
- **Instancing works and is easy.** The overhead lighting rig puts 14 fixtures
  into 2 draw calls with `THREE.InstancedMesh`, built directly in a component.
  The crowd plan depends on this technique, and it is now proven in-project.

Sister project to [room-studioVR](../room-studioVR) — same stack, same
constraints, same working method. Where this file says "as in room-studioVR",
that project is on disk next door and worth reading.

---

## What it is

A WebXR trainer for stage fright. Someone puts on a headset, finds themselves
standing on a stage in front of an audience, and speaks. The point is not the
speech — it is the **repeated, controllable exposure** to the thing that
frightens them, plus honest feedback on how they actually sounded.

Two things have to be true or the project fails:

1. **The audience has to feel like people.** Rows of frozen mannequins produce
   no anxiety and therefore no exposure. They have to breathe, shift, look at
   you, look away, cough, and react.
2. **The difficulty has to be dialable.** Someone who is genuinely afraid
   cannot start in a full auditorium. They start in an empty room, then five
   friendly people, then thirty, then a hall — on their own schedule.

The user's own words: *"people need to overcome stage/public fear so we need
to create a VR environment of a stage and no. of people sitting below, and we
need to add sound and all, and also need to have our mic too."*

## Who it is for

Same portfolio as room-studioVR — a commercial VR R&D track. Treat this as a
demonstrable product, not a toy: it should survive being shown to someone who
has never worn a headset, on the first try, without a technician.

---

## Hard constraints (inherited, non-negotiable)

These are not preferences. They come from the machine and network this is
built on, and they shaped every decision in room-studioVR.

- **WebXR over HTTPS. No APK, no sideloading.** There is no USB-C on the dev
  PC and the WiFi is not reliable enough for large pushes. The headset opens a
  URL. That is the whole delivery mechanism.
- **One self-contained `index.html`.** A-Frame from CDN. **No build step**, no
  bundler, no `node_modules`. You edit the file, you reload the headset.
- **A-Frame 1.7.0** (bundles three.js r173 in the current CDN build — check it,
  do not assume).
- **Assets must be small.** 19MB total was the ceiling that felt right last
  time over this network. Convert and downsize everything.
- **Check the licence before converting anything.** room-studioVR ended up
  with two Renderpeople figures and several no-licence packs baked into the
  scene, which now block a public deploy. Do not repeat that. Prefer CC0
  ([Poly Haven](https://polyhaven.com), CC0-filtered Sketchfab,
  [Freesound](https://freesound.org) filtered to CC0). Record every asset's
  origin and licence in `assets/CREDITS.md` **as you add it**, not later.

---

## The build, as currently imagined

Nothing here is decided. It is a starting position to argue with.

### The space

A hall. Stage at one end, raised ~0.9m, with a lectern, a mic on a stand, and
a screen or backdrop behind. Audience floor below and in front, seating in a
shallow arc or straight rows. Side and back walls close enough to feel like a
room, not an infinite void — the void reads as unfinished, not as vast.

The speaker stands. They should be able to step out from behind the lectern,
because walking is what people do when they are nervous, and taking that away
removes a real part of the experience.

### The audience — the central engineering problem

**A rigged, animated humanoid costs roughly 10k triangles and a skinned draw
call. A Quest cannot run two hundred of them.** This is the thing that decides
whether the project works, so settle it early — before modelling anything.

Plan of attack, cheapest first:

| Rows | Treatment |
| --- | --- |
| Front 1–2 | Real rigged glTF figures. These are the ones eye contact lands on. A handful, maybe 6–10. |
| Middle | Low-poly figures, shared skeleton, animation offset per person so they are not in lockstep. |
| Back | Billboard impostors — camera-facing quads with a rendered figure texture. From 15m in dim house lighting these are indistinguishable. |

Then: instancing where possible, aggressive LOD, and **no shadows from the
audience at all** — shadow casting from a hundred figures is not affordable
and nobody looks at the floor.

Budget to hold: **72fps on a Quest**, measured, not assumed. Decide the
per-frame cost before the audience is built, not after.

Variation matters more than fidelity. Ten identical people is worse than ten
crude but different ones — clothing colour, height, skin tone, posture, and
crucially **animation phase**. Any two audience members playing the same idle
in sync destroys the illusion instantly.

### Audience behaviour

- **Idle life** — breathing, weight shifts, small head movements, the
  occasional look at a neighbour. This can be procedural, as the cat and the
  standing figure in room-studioVR are; it does not all need clips.
- **Attention** — each person has a state: engaged, neutral, distracted (phone,
  window, watch). The *mix* is the difficulty dial, not the count alone.
- **Reactions** — applause, laughter, murmur, a cough. Triggered manually from
  a coach panel at first. Later, possibly driven by the speaker's own audio
  (a pause after a punchline could cue a laugh).
- **Eye contact** — audience heads turning toward the speaker is the single
  most anxiety-producing behaviour available, and it is nearly free. Use it as
  a difficulty setting: nobody looks / some look / everybody looks.

### Sound

- **Room tone and murmur** before the talk starts, dropping to near-silence
  when it does. That drop is what makes a room feel like it is waiting for you.
- **Positional audio** (`<a-sound positional>`) for individual events — a cough
  from the third row on the left has to come from there. A handful of
  positional sources over a stereo bed; do not make a hundred of them.
- **Reverb.** A dry voice in a big room is instantly wrong. Web Audio's
  `ConvolverNode` with an impulse response. A synthetic IR can be generated at
  runtime (decaying noise), which matches the room-studioVR habit of
  generating assets in the browser rather than shipping files.
- Applause needs to be **loud and long** to be satisfying. It is the reward.

### The microphone — the feature that makes this a trainer

`getUserMedia` → Web Audio `AnalyserNode`. Everything below is computable in
the browser with no ML and no server:

| Metric | How | Coaching value |
| --- | --- | --- |
| Volume | RMS over a window | "You are too quiet for the back row" |
| Pace | energy-envelope peak rate | words per minute, drift when nervous |
| Pauses | silence runs > 1.5s | shows the freezes |
| Monotony | pitch via autocorrelation, then its variance | flat delivery is the commonest fault |
| Talk time | total voiced duration | vs the target length |

Two more that need no microphone at all, because the headset already knows:

- **Gaze distribution** — where the speaker looked, bucketed by audience
  section. Staring at one corner for four minutes is a real, measurable,
  fixable habit.
- **Head stillness / fidget** — pose variance over time.

End of session: a **report**. Not a score out of ten — a few honest lines and
a couple of charts. Optionally `MediaRecorder` so they can hear themselves,
which is uncomfortable and effective.

**Gotcha, know this before designing the flow:** microphone permission cannot
be prompted from inside an immersive WebXR session. **Ask for the mic on the
2D page, before the Enter VR button.** Also: it needs a secure context, so the
headset must reach the page over HTTPS or `localhost`.

### The difficulty ladder

Roughly the shape of graduated exposure therapy — this is the actual product,
the rest is scenery:

1. Empty hall, lights up.
2. Five people, all friendly, all attentive.
3. Twenty, mixed attention.
4. Full hall, some distracted, some looking away.
5. Full hall with pressure: a timer, a heckling cough, someone leaving mid-talk.

Plus lighting as its own dial — **stage lights in your eyes are easier**,
because you cannot see faces. House lights up is the hard mode. That single
switch may be the most useful setting in the whole app.

### Controls

Carry over what already works in room-studioVR: a **tabbed panel on the left
controller** (it floats with the hand, is reachable anywhere, and collapses to
an arrow), plus a full desktop panel for setting scenes up at a keyboard.

Tabs, provisionally: Session · Audience · Room · Feedback.

---

## How this gets built (the working method that worked)

This is the part that matters most for whoever picks this up.

- **Measure, do not guess.** Every stubborn bug in room-studioVR was solved by
  measuring: vertex clustering to find which way a model faced, keyframe
  sampling to find an animation's peak, bounding boxes to normalise scale,
  plan-view clearance checks before placing furniture. Guessing cost days.
- **Verify in a real browser before claiming anything works.** There is a
  headless harness that works well, and it caught a fatal error that had been
  mistaken for a lighting bug:

  ```bash
  python3 -m http.server 8899          # from the project root
  google-chrome --headless=new --no-sandbox \
    --use-angle=swiftshader --enable-unsafe-swiftshader \
    --enable-logging=stderr --v=0 --virtual-time-budget=30000 \
    --screenshot=/tmp/shot.png http://localhost:8899/index.html
  ```

  Swap `--screenshot` for `--dump-dom` and grep stderr for `CONSOLE` to read
  the console. To measure something in-scene, write a temporary copy of
  `index.html` with a probe script appended and `console.log` the numbers.
  Note that `requestAnimationFrame` does not survive virtual-time budgeting —
  step animation mixers manually in probes.
- **Generate textures at runtime on a canvas** where possible — plaster, wood,
  fabric, carpet — with normal maps derived by Sobel. Nothing to download,
  nothing that can 404 mid-demo, and greyscale bases multiply over any colour.
- **Convert models with FBX2glTF 0.9.7** (Meta's standalone binary, fetch it to
  a scratch dir). Downsize textures with **PIL**. There is no Blender on this
  machine.
- **Expect converters to lose texture references.** Rebuild materials at
  runtime **by material name**. This is the norm, not the exception.
- **Commit in small, verified steps** with a message that explains *why*, not
  what. Ask before committing.

## Tooling — what this machine can run

Worked out in [docs/session-2026-08-27.md](docs/session-2026-08-27.md); the
conclusions are here.

**The hardware sets the limit.** No discrete GPU — Intel HD Graphics on a 3rd
gen Core / Xeon E3 v2, circa 2012. Modelling, conversion and scripting are
fine. GPU rendering is not, and **local AI 3D generation (Hunyuan3D, TRELLIS,
TripoSR) is out** — they want a CUDA card with ~6GB VRAM. That is why the
headset, not this screen, is where anything gets judged.

**SketchUp was considered and ruled out.** No Linux build has ever existed; the
browser version exports only `.skp` and `.stl`, neither of which carries UVs or
materials into a glTF pipeline. There is no way to drive it from a script, and
`.skp` is a proprietary binary. Its 3D Warehouse remains a decent *manual*
source for furniture and seating, with loose licensing that needs checking
per model.

**The stack to install:**

| Tool | Why |
| --- | --- |
| **Blender** | `blender --background --python script.py`, or `pip install bpy`. Modelling, rigging, animation, UV, decimation, glTF export — all scriptable. The one tool that covers the span. |
| **trimesh** | `pip install trimesh`. Load anything, measure it, convert it. The tool for *measure, don't guess*. |
| **gltf-transform** | `npm i -g @gltf-transform/cli`. Inspect, weld, dedupe, simplify, resize textures, meshopt/Draco/KTX2. |
| **gltfpack** | The blunt version of the same. `-mi` gives mesh instancing, which is directly the crowd problem. |
| **PyMeshLab** | When downloaded models arrive too heavy and need real decimation. |

**Assets can be fetched programmatically.** Poly Haven has a public API and it
works — `https://api.polyhaven.com/types` returns `["hdris","textures","models"]`,
and `/assets?type=hdris` lists them. **Everything on it is CC0**, which is the
licence problem in room-studioVR solved outright. ambientCG is the same shape.
Combined with gltf-transform that is an asset pipeline with no clicking in it.

**A plausible answer to the audience problem:** MPFB2 (MakeHuman, as a Blender
add-on, so reachable through `bpy`) for varied bodies → Mixamo for idle clips →
`gltfpack -mi` for instancing. Every step except Mixamo can be scripted. Not
proven, but it is the first thing to try.

Also free and scriptable, if the need arises: **OpenSCAD** and **build123d** /
**CadQuery** for precise parametric geometry (seating rows, raked floors,
risers), **FreeCAD**, **assimp** for format conversion, and **Godot 4** with
headless CLI export — though Godot ships to a headset as an APK, which the no
sideloading constraint rules out.

## Gotchas carried over from room-studioVR

Every one of these cost real time. They are stack-level, so they will happen
here too.

1. **A duplicate component name throws and kills the entire script.** A-Frame
   already owns `grabbable`; registering a second one aborted every line after
   it, including the boot function. The scene still rendered — just raw and
   unlit — which reads like a lighting bug, not a fatal error. **Check new
   component names against `aframe.min.js`, and read the console first.**
2. **`Box3.setFromObject` returns a WORLD box.** Subtracting its centre from an
   object's *local* position flings it as far as its parent is from the origin.
   Measure in the model's own space via an inverted `matrixWorld`.
3. **`visible: false` does not stop raycasts.** Hidden UI still steals clicks.
   Move it out of reach as well.
4. **Point lights ignore walls.** A light in one room lights every room. The
   only fix that ever worked was geometry.
5. **Every `MeshStandardMaterial` ships `emissiveIntensity: 1`** with a black
   emissive, so a guard testing `emissiveIntensity > 0` matches *everything*.
   Test the emissive colour instead.
6. **A finished `LoopOnce` animation leaves its last frame written in.** Stop
   the action to restore the rest pose.
7. **Product-showcase animation clips are usually round trips** — they open
   *and* close. Sample every channel to find the peak; do not eyeball one.
8. **Model node transforms compose.** A mesh node can carry its own rotation
   and offset on top of the accessor bounds. Walk the hierarchy.
9. **In A-Frame text, a larger `width` means larger glyphs.** Raising it to
   shrink a label does the opposite. Its `anchor` also defaults to centring
   the whole text block on the entity, so `align: left` alone still hangs half
   a block off to the left — set `anchor` explicitly.
10. **three.js r155 removed legacy light units, so r173 is physical.** Point
    and spot lights fall off as `intensity / distance^decay`; a ceiling lamp
    7m up at `intensity: 0.5` delivers ~0.01 and the room renders black.
    Punctual lights want **tens to hundreds**; hemisphere/ambient/directional
    are not distance-attenuated and stay in the **0–3** range. Mixing the two
    scales looks exactly like a broken lighting rig. Cost one render cycle in
    M0 to find.
11. **Headless virtual time does not drive the Web Audio clock.** Timers
    fast-forward while audio runs on the real clock, so a series of
    `setTimeout` samples all read the same buffer and a signal test measures
    nothing while appearing to pass. Test the analyser maths by stubbing
    `getFloatTimeDomainData` with a known waveform.

---

## Open questions — decide these before building

1. ~~**What is the maximum audience size we will support, and at what
   fidelity?**~~ **ANSWERED — a full house, at full fidelity.**

   Measured with `sv-crowd`, a lab that builds real `THREE.SkinnedMesh`
   figures with real skeletons, real `AnimationMixer`s and phase-offset idle
   clips, generated procedurally so the question could be settled **without
   downloading or licensing a single model**. A skinned figure costs the GPU
   the same whether it is shaped like a person or a blob.

   Cost of a **286-seat full house**, seen from the lectern:

   | Front-row figure | Total triangles | Draw calls |
   | --- | --- | --- |
   | 1,800 tris | 29,834 | 56 |
   | 5,000 tris | 55,490 | 59 |
   | **10,000 tris** | **95,692** | **59** |

   And the cost of the crowd alone, at 1,800 tris per skinned figure:

   | People | Draw calls | Triangles |
   | --- | --- | --- |
   | 0 | 39 | 8,074 |
   | 5 | 49 | 18,124 |
   | 20 | 57 | 25,578 |
   | 286 | 59 | 29,890 |

   **The first 8 people cost more than the next 278 combined.** Going from
   5 to 286 costs ten draw calls. This is the tiering working exactly as the
   brief hoped: 8 skinned + 40 instanced + 238 billboards, where each of the
   last two tiers is a single draw call no matter how many people are in it.

   The practical consequence is that **the crowd was never the constraint
   the brief feared.** Budget for 8 genuinely good rigged figures in the
   front rows and stop worrying about the rest — the back of the room is
   free. Spend the effort on their *behaviour* instead, which is what the
   anxiety actually comes from.

   Caveat: these are draw-call and triangle counts, which are properties of
   the scene and therefore transfer to any device. Whether a Quest sustains
   72fps while pushing them is a separate question and still needs the
   on-device reading.
2. Where do the audience models come from? Mixamo is the obvious source for
   rigged, animated humans, but check its terms for this use. CC0 alternatives
   are scarcer and worse. **Settle the licence before converting.**
3. Real speech recognition for filler words ("um", "like") would be the
   strongest feature in the app. The Web Speech API works in desktop Chrome;
   whether it works in the Quest browser is unknown and needs testing early —
   it may decide whether that feature exists at all.
4. Does a session need to persist between visits — progress up the ladder, past
   reports? That implies storage, and possibly accounts.
5. Guided mode: a scripted coach that tells you what to do next, or a sandbox
   with a settings panel? Probably both, eventually.
6. Is there a second person? A trainer joining from a desktop to trigger
   reactions live would be a genuinely different product. Out of scope for now,
   but do not design something that forecloses it.

## First milestone

Do not start with the audience. Start with the thing that proves the concept
is affordable:

**M0 — an empty hall that runs at 72fps in the headset, with a stage you can
stand on and walk off, and a live microphone level meter floating in front of
you.** If the mic permission flow and the frame budget both work, everything
after that is content.

**Built.** See [README.md](README.md). Verified headless: console clean, hall
renders in both lighting modes, walkable regions step 0.9 → 0.6 → 0.3 → 0 and
clamp at every wall, `getUserMedia` opens, and the RMS/dB/verdict maths passes
17/17 against known waveforms.

**Still open: the 72fps itself.** Frame rate is a property of the headset and
cannot be measured on a 2012 Intel IGP. The frame counter floats in front of
you in VR so it can be read while wearing it — that reading is the real M0
sign-off, and until it exists this milestone is not closed.
