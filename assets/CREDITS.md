# Asset credits and licences

**Nothing here yet, and as of M0 that is a deliberate position rather than an
oversight.** The hall ships zero downloaded assets: every texture is generated
at runtime on a canvas, and all geometry is A-Frame primitives. The only
third-party code is A-Frame 1.7.0 itself, from its CDN, under the MIT licence.

That means M0 is **clear to deploy publicly**, which is precisely what
room-studioVR cannot do. Keep it that way for as long as possible — the moment
the audience arrives, so does the licence problem.

Add an entry the moment an asset enters `assets/` — before converting it, not
after.

room-studioVR skipped this step and ended up with figures whose licence
forbids redistributing the 3D data, baked into the scene. A public URL is
redistribution. That project cannot be deployed publicly as a result.

Every entry needs:

- **What it is** and the source pack name
- **Author / vendor**
- **Licence**, quoted, and where it was found — "unknown" is a status that
  blocks deploy, not a footnote
- **Processing applied** — conversion tool, texture downsizing, channel
  swaps, anything stripped

Prefer CC0. [Poly Haven](https://polyhaven.com) is CC0 throughout.
[Freesound](https://freesound.org) can be filtered to CC0 for audio.
[Sketchfab](https://sketchfab.com) can be filtered to CC0/CC-BY, but the
licence is per-model and must be checked every time.
